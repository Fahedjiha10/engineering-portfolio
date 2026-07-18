#!/usr/bin/env python3
"""Smart splitter for construction plan-set PDFs.

This tool reads a PDF plan set, classifies each page by construction-related
keywords and sheet-title hints, writes category PDFs, and creates a CSV index.
It never writes back to the source PDF.
"""

from __future__ import annotations

import argparse
import csv
import gc
import json
import math
import queue
import re
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field, replace
from datetime import datetime
from pathlib import Path
from typing import Callable, Iterable

try:
    import fitz  # PyMuPDF
except ImportError:  # pragma: no cover - handled at runtime for users
    fitz = None


CATEGORY_COVER_INDEX = "01_Cover_Drawing_Index.pdf"
CATEGORY_FLOOR_PLANS = "02_Ground_Floor_Plans.pdf"
CATEGORY_PARTIAL_FLOOR_PLANS = "03_Partial_Floor_Plans.pdf"
CATEGORY_DOOR_SCHEDULES = "04_Door_Schedules.pdf"
CATEGORY_WINDOW_STOREFRONT_SCHEDULES = "05_Window_Storefront_Schedules.pdf"
CATEGORY_WINDOW_SCHEDULES = CATEGORY_WINDOW_STOREFRONT_SCHEDULES
CATEGORY_STOREFRONT_SCHEDULES = CATEGORY_WINDOW_STOREFRONT_SCHEDULES
CATEGORY_KITCHEN = "06_Kitchen.pdf"
CATEGORY_EXTERIOR_ELEVATIONS = "07_Exterior_Elevations.pdf"
CATEGORY_OPENING_ELEVATIONS = CATEGORY_EXTERIOR_ELEVATIONS
CATEGORY_STRUCTURAL_WIND = "09_Structural_Wind_Pressures.pdf"
CATEGORY_STRUCTURAL = "10_Structural_General.pdf"
CATEGORY_MECHANICAL = "11_Mechanical.pdf"
CATEGORY_ELECTRICAL = "12_Electrical.pdf"
CATEGORY_PLUMBING = "13_Plumbing.pdf"
CATEGORY_FIRE_ALARM = "14_Fire_Alarm.pdf"
CATEGORY_FIRE_PROTECTION = "15_Fire_Protection.pdf"
CATEGORY_VENDOR_DETAIL = "16_Vendor_Detail_Sheets.pdf"
CATEGORY_REVIEW = "17_Unknown_Needs_Manual_Review.pdf"

# Backward-compatible names used by the older scoring helpers.
CATEGORY_WINDOWS = CATEGORY_WINDOW_SCHEDULES
CATEGORY_DOORS = CATEGORY_DOOR_SCHEDULES
CATEGORY_OTHER_SCHEDULES = CATEGORY_REVIEW
CATEGORY_ELEVATIONS = CATEGORY_EXTERIOR_ELEVATIONS
CATEGORY_OTHER = CATEGORY_REVIEW
CATEGORY_MEP_DETAIL = CATEGORY_VENDOR_DETAIL

CATEGORY_LABELS = {
    CATEGORY_COVER_INDEX: "Cover / Drawing Index",
    CATEGORY_FLOOR_PLANS: "Ground / Floor Plans",
    CATEGORY_PARTIAL_FLOOR_PLANS: "Partial Floor Plans",
    CATEGORY_DOOR_SCHEDULES: "Door Schedules",
    CATEGORY_WINDOW_STOREFRONT_SCHEDULES: "Window / Storefront Schedules",
    CATEGORY_KITCHEN: "Kitchen / Food Service",
    CATEGORY_EXTERIOR_ELEVATIONS: "Exterior Elevations",
    CATEGORY_STRUCTURAL_WIND: "Structural Wind Pressures",
    CATEGORY_STRUCTURAL: "Structural General",
    CATEGORY_MECHANICAL: "Mechanical",
    CATEGORY_ELECTRICAL: "Electrical",
    CATEGORY_PLUMBING: "Plumbing",
    CATEGORY_FIRE_ALARM: "Fire Alarm",
    CATEGORY_FIRE_PROTECTION: "Fire Protection",
    CATEGORY_VENDOR_DETAIL: "Vendor / Detail Sheets",
    CATEGORY_REVIEW: "Unknown / Needs Manual Review",
}

CATEGORY_ORDER = [
    CATEGORY_COVER_INDEX,
    CATEGORY_FLOOR_PLANS,
    CATEGORY_PARTIAL_FLOOR_PLANS,
    CATEGORY_DOOR_SCHEDULES,
    CATEGORY_WINDOW_STOREFRONT_SCHEDULES,
    CATEGORY_KITCHEN,
    CATEGORY_EXTERIOR_ELEVATIONS,
    CATEGORY_STRUCTURAL_WIND,
    CATEGORY_STRUCTURAL,
    CATEGORY_MECHANICAL,
    CATEGORY_ELECTRICAL,
    CATEGORY_PLUMBING,
    CATEGORY_FIRE_ALARM,
    CATEGORY_FIRE_PROTECTION,
    CATEGORY_VENDOR_DETAIL,
    CATEGORY_REVIEW,
]

CATEGORY_SLUGS = {
    CATEGORY_COVER_INDEX: "cover_index",
    CATEGORY_FLOOR_PLANS: "floor_plans",
    CATEGORY_PARTIAL_FLOOR_PLANS: "partial_floor_plans",
    CATEGORY_DOOR_SCHEDULES: "door_schedules",
    CATEGORY_WINDOW_STOREFRONT_SCHEDULES: "window_storefront_schedules",
    CATEGORY_KITCHEN: "kitchen",
    CATEGORY_EXTERIOR_ELEVATIONS: "exterior_elevations",
    CATEGORY_STRUCTURAL_WIND: "structural_wind_pressures",
    CATEGORY_STRUCTURAL: "structural_general",
    CATEGORY_MECHANICAL: "mechanical",
    CATEGORY_ELECTRICAL: "electrical",
    CATEGORY_PLUMBING: "plumbing",
    CATEGORY_FIRE_ALARM: "fire_alarm",
    CATEGORY_FIRE_PROTECTION: "fire_protection",
    CATEGORY_VENDOR_DETAIL: "vendor_detail_sheets",
    CATEGORY_REVIEW: "unknown_needs_manual_review",
}

MAX_RASTER_FALLBACK_PIXELS = 6_000_000
MAX_METADATA_RENDER_PIXELS = 14_000_000
METADATA_RENDER_DPI = 200
STATUS_UPDATE_SECONDS = 0.25
MANUAL_REVIEW_THRESHOLD = 0.75
SMALL_PLAN_PAGE_THRESHOLD = 20
WEAK_INDEX_MATCH_RATIO = 0.50
WEAK_TITLE_BLOCK_RATIO = 0.60
LOW_CONFIDENCE_RATIO = 0.35
DEBUG_THUMBNAIL_DPI = 120
DEBUG_SMALL_PLAN_DPI = 300
DEBUG_LARGE_PLAN_DPI = 200

REGION_DOOR_SCHEDULE = "door_schedule_table"
REGION_WINDOW_SCHEDULE = "window_schedule_table"
REGION_STOREFRONT_SCHEDULE = "storefront_schedule_table"
REGION_GLAZING_SCHEDULE = "glazing_schedule_table"
REGION_HARDWARE_SCHEDULE = "hardware_schedule_table"
REGION_EXTERIOR_ELEVATION = "exterior_elevation"
REGION_STOREFRONT_ELEVATION = "storefront_elevation"
REGION_DOOR_DETAIL = "door_detail"
REGION_WINDOW_DETAIL = "window_detail"
REGION_STOREFRONT_DETAIL = "storefront_detail"
REGION_GENERAL_NOTES = "general_notes"
REGION_VENDOR_DETAIL = "vendor_detail_sheet"
REGION_REVIEW = "unknown_needs_manual_review"

REGION_SCHEDULE_TO_PAGE_CATEGORY = {
    REGION_DOOR_SCHEDULE: CATEGORY_DOOR_SCHEDULES,
    REGION_HARDWARE_SCHEDULE: CATEGORY_DOOR_SCHEDULES,
    REGION_WINDOW_SCHEDULE: CATEGORY_WINDOW_SCHEDULES,
    REGION_GLAZING_SCHEDULE: CATEGORY_WINDOW_SCHEDULES,
    REGION_STOREFRONT_SCHEDULE: CATEGORY_WINDOW_STOREFRONT_SCHEDULES,
}

INDEX_KEYWORD_PATTERNS = [
    ("partial floor plan", r"\bpartial\b.{0,80}\bfloor\s+plans?\b|\bfloor\s+plans?\s*[-:]?\s*(?:area|sector|zone|part)\s+[A-Z0-9]\b|\bplans?\s*[-:]?\s*(?:area|sector|zone|part)\s+[A-Z0-9]\b"),
    ("window schedule", r"\bwindow\s+schedules?\b"),
    ("window type", r"\bwindows?\s+types?\b|\bwindows?\s+elevations?\b|\bwindows?\s+details?\b|\bwindows?\s+spec(?:ification)?s?\b"),
    ("door schedule", r"\bdoor\s+schedules?\b"),
    ("door type", r"\bdoors?\s+types?\b|\bdoors?\s+elevations?\b|\bdoors?\s+details?\b|\bdoors?\s+hardware\b|\bdoors?\s+spec(?:ification)?s?\b"),
    ("storefront", r"\bstore\s*front\b|\bstorefronts?\b"),
    ("curtain wall", r"\bcurtain\s+walls?\b"),
    ("glazing", r"\bglaz(?:ing|ed|er|ers?)\b"),
    ("kitchen", r"\bkitchen\b|\bfood\s*service\b|\bfoodservice\b|\bkitchen\s+equipment\b|\bequipment\s+(?:plan|schedule)\b|\bhood\b|\bgrease\s+interceptor\b"),
    ("elevations", r"\belevations?\b"),
    ("floor plans", r"\bfloor\s+plans?\b"),
    ("structural", r"\bstructural\b|\bstructure\b"),
    ("wind pressure", r"\bwind\s+pressures?\b|\bdesign\s+pressures?\b"),
    ("PSF pressure chart", r"\bpsf\b|\bp\.?\s*s\.?\s*f\.?\b|\bpressure\s+(?:chart|table|schedule|zone)s?\b"),
    (
        "components and cladding",
        r"\bcomponents?\s+(?:and|&)\s+cladding\b|\bC\s*&\s*C\b|\bC\s*/\s*C\b",
    ),
    ("U-factor", r"\bU\s*[- ]?\s*factors?\b|\bU\s*[- ]?\s*values?\b"),
    ("SHGC", r"\bSHGC\b|\bsolar\s+heat\s+gain\b"),
    ("NOA", r"\bNOA\b|\bnotice\s+of\s+acceptance\b"),
    ("impact glazing", r"\bimpact\s+glaz(?:ing|ed)\b|\bimpact\s+resistant\b"),
    ("finish schedule", r"\bfinish\s+schedules?\b"),
]

CATEGORY_RULES = {
    CATEGORY_PARTIAL_FLOOR_PLANS: [
        ("partial floor plan", r"\bpartial\b.{0,80}\bfloor\s+plans?\b", 24),
        ("floor plan area", r"\bfloor\s+plans?\s*[-:]?\s*(?:area|sector|zone|part|portion)\s+[A-Z0-9]\b", 18),
        ("area floor plan", r"\b(?:area|sector|zone|part|portion)\s+[A-Z0-9]\s+(?:\w+\s+){0,3}floor\s+plans?\b", 18),
        ("plan area", r"\b(?:partial\s+)?(?:\w+\s+){0,3}plans?\s*[-:]?\s*(?:area|sector|zone|part|portion)\s+[A-Z0-9]\b", 14),
        ("area plan", r"\b(?:area|sector|zone|part|portion)\s+[A-Z0-9]\s+(?:\w+\s+){0,3}plans?\b", 14),
        ("matchline plan", r"\bmatch\s*lines?\b|\bmatchline\b", 8),
    ],
    CATEGORY_FLOOR_PLANS: [
        ("floor plan", r"\bfloor\s+plans?\b", 14),
        ("overall floor plan", r"\boverall\s+(?:\w+\s+){0,3}floor\s+plans?\b", 18),
        ("life safety plan", r"\blife\s+safety\s+plans?\b", 10),
        ("reflected ceiling plan", r"\breflected\s+ceiling\s+plans?\b|\bRCP\b", 10),
        ("roof plan", r"\broof\s+plans?\b", 9),
        ("enlarged plan", r"\benlarged\s+plans?\b", 8),
        ("architectural plan", r"\barchitectural\s+plans?\b", 8),
        ("level plan", r"\b(?:level|first|second|third|ground)\s+\w*\s*plans?\b", 6),
    ],
    CATEGORY_WINDOWS: [
        ("window schedule", r"\bwindow\s+schedules?\b", 22),
        ("window types", r"\bwindows?\s+types?\b", 18),
        ("window elevation", r"\bwindows?\s+elevations?\b", 18),
        ("window detail", r"\bwindows?\s+details?\b", 18),
        ("window specs", r"\bwindows?\s+spec(?:ification)?s?\b|\bwindows?\s+notes?\b", 14),
        ("storefront", r"\bstore\s*front\b|\bstorefronts?\b", 20),
        ("curtain wall", r"\bcurtain\s+walls?\b", 18),
        ("glazing", r"\bglaz(?:ing|ed|er|ers?)\b", 16),
        ("glass", r"\bglass\s+(?:types?|schedule|details?|spec(?:ification)?s?|elevations?)\b", 12),
        ("fenestration", r"\bfenestration\b", 12),
        ("U-factor", r"\bU\s*[- ]?\s*factors?\b|\bU\s*[- ]?\s*values?\b", 10),
        ("SHGC", r"\bSHGC\b|\bsolar\s+heat\s+gain\b", 10),
        ("NOA", r"\bNOA\b|\bnotice\s+of\s+acceptance\b|\bproduct\s+approval\b", 9),
        ("impact glazing", r"\bimpact\s+glaz(?:ing|ed)\b|\bimpact\s+resistant\b", 11),
    ],
    CATEGORY_DOORS: [
        ("door schedule", r"\bdoor\s+schedules?\b", 22),
        ("door types", r"\bdoors?\s+types?\b", 18),
        ("door elevation", r"\bdoors?\s+elevations?\b", 18),
        ("door detail", r"\bdoors?\s+details?\b", 18),
        ("door hardware", r"\bdoors?\s+hardware\b|\bhardware\s+schedules?\b", 16),
        ("door specs", r"\bdoors?\s+spec(?:ification)?s?\b|\bdoors?\s+notes?\b", 14),
        ("doors", r"\bdoors?\b", 8),
    ],
    CATEGORY_KITCHEN: [
        ("kitchen plan", r"\bkitchen\s+(?:equipment\s+)?plans?\b", 24),
        ("kitchen equipment", r"\bkitchen\s+equipment\b", 24),
        ("food service", r"\bfood\s*service\b|\bfoodservice\b", 24),
        ("commercial kitchen", r"\bcommercial\s+kitchen\b", 20),
        ("kitchen schedule", r"\bkitchen\b.{0,40}\bschedules?\b|\bschedules?\b.{0,40}\bkitchen\b", 18),
        ("equipment schedule", r"\bequipment\s+schedules?\b", 12),
        ("hood", r"\b(?:exhaust\s+)?hoods?\b|\bType\s*I\s+hood\b", 12),
        ("grease", r"\bgrease\s+(?:interceptor|trap|duct)\b", 12),
        ("dishwash", r"\bdish\s*wash(?:er|ing)?\b", 10),
        ("walk-in", r"\bwalk\s*[- ]?in\s+(?:cooler|freezer)\b", 10),
    ],
    CATEGORY_OTHER_SCHEDULES: [
        ("finish schedule", r"\bfinish\s+schedules?\b", 12),
        ("room finish schedule", r"\broom\s+finish\s+schedules?\b", 14),
        ("schedule", r"\bschedules?\b", 7),
    ],
    CATEGORY_ELEVATIONS: [
        ("elevation", r"\belevations?\b", 14),
        ("exterior elevation", r"\bexterior\s+elevations?\b", 16),
        ("interior elevation", r"\binterior\s+elevations?\b", 12),
        ("building elevation", r"\bbuilding\s+elevations?\b", 14),
    ],
    CATEGORY_STRUCTURAL: [
        ("wind pressure", r"\bwind\s+pressures?\b|\bdesign\s+pressures?\b", 16),
        ("pressure chart", r"\bpressure\s+(?:chart|table|schedule|zone)s?\b", 14),
        ("psf wind pressure", r"\bpsf\b|\bp\.?\s*s\.?\s*f\.?\b", 8),
        (
            "components and cladding",
            r"\bcomponents?\s+(?:and|&)\s+cladding\b|\bC\s*&\s*C\b|\bC\s*/\s*C\b",
            16,
        ),
        ("structural", r"\bstructural\b|\bstructure\b", 11),
        ("foundation", r"\bfoundation\s+plans?\b|\bfoundations?\b", 8),
        ("framing", r"\bframing\s+plans?\b|\bframing\b", 8),
        ("shear wall", r"\bshear\s+walls?\b", 8),
    ],
}

TITLE_KEYWORD_RE = re.compile(
    r"\b("
    r"schedule|floor plan|partial|overall|area|sector|zone|plan|elevation|structural|wind|pressure|"
    r"store\s*front|storefront|curtain wall|glazing|glass|fenestration|finish|foundation|framing|"
    r"window|door|hardware|roof|level|life safety|reflected ceiling|details?|types?|specifications?|notes?"
    r")\b",
    re.IGNORECASE,
)

COVER_OR_INDEX_TITLE_RE = re.compile(
    r"\b(cover\s+sheet|drawing\s+index|sheet\s+index|project\s+information|"
    r"index\s+of\s+drawings|drawing\s+list|sheet\s+list|list\s+of\s+drawings|"
    r"table\s+of\s+contents|code\s+summary|abbreviations?|symbols?|legend)\b",
    re.IGNORECASE,
)

INDEX_PAGE_RE = re.compile(
    r"\b(sheet\s+(?:index|list|number|no\.?|title)|drawing\s+(?:index|list|title|no\.?)|"
    r"index\s+of\s+drawings|list\s+of\s+drawings|table\s+of\s+contents|cover\s+sheet)\b",
    re.IGNORECASE,
)

STRONG_INDEX_PAGE_RE = re.compile(
    r"\b(sheet\s+(?:index|list)|drawing\s+(?:index|list)|"
    r"index\s+of\s+drawings|list\s+of\s+drawings|table\s+of\s+contents|cover\s+sheet)\b",
    re.IGNORECASE,
)

DRAWING_SET_HEADER_PATTERNS = [
    ("Architectural Set", r"^(?:a\s*[-:]?\s*)?architectural(?:\s+(?:set|drawings?))?$"),
    ("Structural Set", r"^(?:s\s*[-:]?\s*)?structural(?:\s+(?:set|drawings?))?$"),
    ("Mechanical Set", r"^(?:m\s*[-:]?\s*)?mechanical(?:\s+(?:set|drawings?))?$"),
    ("Plumbing Set", r"^(?:p\s*[-:]?\s*)?plumbing(?:\s+(?:set|drawings?))?$"),
    ("Electrical Set", r"^(?:e\s*[-:]?\s*)?electrical(?:\s+(?:set|drawings?))?$"),
    ("Fire Protection Set", r"^(?:fp\s*[-:]?\s*)?fire\s+protection(?:\s+(?:set|drawings?))?$"),
    ("Civil Set", r"^(?:c\s*[-:]?\s*)?civil(?:\s+(?:set|drawings?))?$"),
    ("Landscape Set", r"^(?:l\s*[-:]?\s*)?landscape(?:\s+(?:set|drawings?))?$"),
    ("Interior Set", r"^(?:i|id\s*[-:]?\s*)?interior(?:\s+(?:set|drawings?))?$"),
    ("Kitchen / Food Service Set", r"^(?:(?:k|ke|fs)\s*[-:]?\s*)?(?:kitchen|food\s*service|foodservice|commercial\s+kitchen)(?:\s+(?:set|drawings?|equipment))?$"),
    ("Vendor / Detail Set", r"^(?:vendor|detail|vendor\s+detail|vendor\s+and\s+detail)(?:\s+(?:set|drawings?))?$"),
    (
        "Floor For Reference Only Set",
        r"^(?:floor\s+(?:plans?\s+)?for\s+reference\s+only|for\s+reference\s+only)(?:\s+set)?$",
    ),
]

DISCIPLINE_OTHER_PREFIXES = {"C", "L", "M", "P", "E", "FP", "FA", "FS", "LV", "T", "TEL", "V"}
DISCIPLINE_OTHER_SET_RE = re.compile(
    r"\b(mechanical|plumbing|electrical|fire\s+protection|civil|landscape|low\s+voltage|technology|telecom|vendor|detail)\b",
    re.IGNORECASE,
)
ARCHITECTURAL_SET_RE = re.compile(r"\barchitectural\b", re.IGNORECASE)
STRUCTURAL_SET_RE = re.compile(r"\bstructural\b", re.IGNORECASE)
FLOOR_REFERENCE_SET_RE = re.compile(r"\bfloor\b.*\breference\b|\breference\b.*\bfloor\b", re.IGNORECASE)
FLOOR_LEVEL_RE = re.compile(
    r"\b("
    r"basement|ground|lobby|podium|mezzanine|roof|level|floor|"
    r"first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|"
    r"1st|2nd|3rd|[4-9]th"
    r")\b",
    re.IGNORECASE,
)
NON_FLOOR_TITLE_RE = re.compile(
    r"\b(schedule|elevation|section|detail|notes?|legend|diagram|riser|single\s+line|panel|load|fixture)\b",
    re.IGNORECASE,
)

SHEET_NUMBER_RE = re.compile(
    r"\b(?:[A-Z]{1,3}\s*[-.]?\s*\d{1,3}(?:\.\d{1,2})?[A-Z]?|"
    r"[A-Z]{1,3}\s*\d{1,2}\.\d{1,2}[A-Z]?)\b",
    re.IGNORECASE,
)

BAD_SHEET_PREFIXES = {
    "AAM",
    "ADA",
    "ANSI",
    "AST",
    "ASTM",
    "FBC",
    "IBC",
    "ICC",
    "LLC",
    "NOA",
    "NTS",
    "CW",
    "SF",
    "SG",
    "UL",
}

TITLE_REJECT_RE = re.compile(
    r"\b("
    r"architects?|architecture|engineers?|consultants?|contractors?|"
    r"drawn|checked|approved|revisions?|date|scale|project|owner|client|"
    r"copyright|phone|email|www|address|sheet\s+number|sheet\s+no"
    r")\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class PageRecord:
    page_index: int
    original_page_number: int
    sheet_number: str
    sheet_title: str
    drawing_set: str
    discipline_prefix: str
    detected_discipline: str
    raw_title_block_text: str
    matched_index: bool
    confidence: float
    reason: str
    needs_manual_review: bool
    matched_keywords: list[str]
    category_files: list[str]
    sheet_title_source: str
    index_source_page: int | None
    regions: list["RegionRecord"]
    evidence_scores: dict[str, float] = field(default_factory=dict)
    top_candidates: list[dict[str, object]] = field(default_factory=list)
    small_plan_mode: bool = False
    debug_files: dict[str, list[str]] = field(default_factory=dict)


@dataclass(frozen=True)
class SheetIndexEntry:
    sheet_number: str
    sheet_title: str
    drawing_set: str
    source_page_number: int
    confidence: int


@dataclass(frozen=True)
class RegionRecord:
    page_index: int
    pdf_page_number: int
    sheet_number: str
    sheet_title: str
    region_id: str
    region_bbox: list[float]
    region_category: str
    confidence: float
    reason: str
    needs_manual_review: bool
    extracted_rows: list[list[str]]
    raw_text: str
    evidence_scores: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class SplitResult:
    output_dir: Path
    manifest_path: Path
    csv_path: Path
    sheet_index_csv_path: Path
    page_count: int
    debug_dir: Path | None = None


StatusCallback = Callable[[str], None]


def collapse_spaces(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def clean_lines(text: str) -> list[str]:
    lines: list[str] = []
    for raw_line in text.splitlines():
        line = collapse_spaces(raw_line)
        if not line:
            continue
        if len(line) > 140:
            continue
        lines.append(line)
    return lines


def normalize_sheet_number(value: str) -> str:
    return re.sub(r"\s+", "", value.strip().upper().strip(":;,."))


def sheet_lookup_key(value: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", normalize_sheet_number(value))


def sheet_prefix(sheet_number: str) -> str:
    match = re.match(r"([A-Z]+)", sheet_number.upper())
    return match.group(1) if match else ""


def is_bad_sheet_candidate(candidate: str) -> bool:
    prefix = sheet_prefix(candidate)
    if prefix in BAD_SHEET_PREFIXES:
        return True
    if len(prefix) > 3:
        return True
    digit_count = sum(char.isdigit() for char in candidate)
    return digit_count == 0


def detect_sheet_number(lines: list[str]) -> tuple[str, int | None]:
    best_number = ""
    best_index: int | None = None
    best_score = -1.0
    total = max(len(lines), 1)

    for index, line in enumerate(lines):
        for match in SHEET_NUMBER_RE.finditer(line):
            candidate = normalize_sheet_number(match.group(0))
            if is_bad_sheet_candidate(candidate):
                continue

            score = 0.0
            normalized_line = normalize_sheet_number(line)
            if normalized_line == candidate:
                score += 50
            if "sheet" in line.lower():
                score += 20
            if sheet_prefix(candidate) in {"A", "AD", "G", "S", "C", "E", "M", "P", "FP", "ID", "LS"}:
                score += 8
            score += (index / total) * 10
            if len(candidate) <= 8:
                score += 4

            if score > best_score:
                best_number = candidate
                best_index = index
                best_score = score

    return best_number, best_index


def detect_sheet_number_from_index(
    lines: list[str],
    sheet_index: dict[str, SheetIndexEntry],
) -> tuple[str, int | None]:
    best_number = ""
    best_index: int | None = None
    best_score = -1.0
    total = max(len(lines), 1)

    for index, line in enumerate(lines):
        for match in SHEET_NUMBER_RE.finditer(line):
            candidate = normalize_sheet_number(match.group(0))
            key = sheet_lookup_key(candidate)
            if key not in sheet_index or is_bad_sheet_candidate(candidate):
                continue

            score = 100.0
            normalized_line = normalize_sheet_number(line)
            if normalized_line == candidate:
                score += 50
            if sheet_index[key].sheet_title and sheet_index[key].sheet_title.lower() in line.lower():
                score += 30
            if "sheet" in line.lower():
                score += 10
            score += (index / total) * 12
            if len(candidate) <= 8:
                score += 4

            if score > best_score:
                best_number = sheet_index[key].sheet_number
                best_index = index
                best_score = score

    if best_number:
        return best_number, best_index

    return detect_sheet_number(lines)


def detect_sheet_number_from_index_words(
    words: list[tuple],
    page_rect: "fitz.Rect",
    sheet_index: dict[str, SheetIndexEntry],
) -> str:
    best_number = ""
    best_score = -1.0
    width = max(float(page_rect.width), 1.0)
    height = max(float(page_rect.height), 1.0)

    for row in group_words_into_rows(words):
        row_text = " ".join(str(word[4]) for word in row)
        row_upper = row_text.upper()
        for token_index, word in enumerate(row):
            candidate = sheet_number_from_word(str(word[4]))
            key = sheet_lookup_key(candidate)
            if not candidate or key not in sheet_index:
                continue

            x0 = float(word[0])
            y0 = float(word[1])
            x_ratio = x0 / width
            y_ratio = y0 / height

            score = 100.0
            score += x_ratio * 12
            score += y_ratio * 24

            if x_ratio >= 0.72 and y_ratio >= 0.74:
                score += 180
            elif x_ratio >= 0.62 and y_ratio >= 0.65:
                score += 80

            if y_ratio >= 0.88:
                score += 55
            if x_ratio >= 0.82:
                score += 25

            if "MATCH LINE" in row_upper or "MATCHLINE" in row_upper:
                score -= 100
            if token_index > 0 and str(row[token_index - 1][4]).upper().strip(":-") in {"DETAIL", "SECTION"}:
                score -= 40
            if x_ratio < 0.35 and y_ratio < 0.80:
                score -= 35

            if score > best_score:
                best_number = sheet_index[key].sheet_number
                best_score = score

    return best_number if best_score >= 100 else ""


def row_sheet_number_candidates(row: list[tuple]) -> list[tuple[str, int, int, float, float, float, float]]:
    candidates: list[tuple[str, int, int, float, float, float, float]] = []
    seen: set[tuple[str, int, int]] = set()
    max_span = min(5, len(row))

    for start_index in range(len(row)):
        for end_index in range(start_index + 1, min(len(row), start_index + max_span) + 1):
            words = row[start_index:end_index]
            joined = " ".join(str(word[4]) for word in words)
            candidate = normalize_sheet_number(joined)
            if not SHEET_NUMBER_RE.fullmatch(candidate) or is_bad_sheet_candidate(candidate):
                continue

            key = (candidate, start_index, end_index)
            if key in seen:
                continue
            seen.add(key)

            x0 = min(float(word[0]) for word in words)
            y0 = min(float(word[1]) for word in words)
            x1 = max(float(word[2]) for word in words)
            y1 = max(float(word[3]) for word in words)
            candidates.append((candidate, start_index, end_index, x0, y0, x1, y1))

    return candidates


def detect_title_block_sheet_number(
    words: list[tuple],
    page_rect: "fitz.Rect",
    sheet_index: dict[str, SheetIndexEntry],
) -> str:
    best_number = ""
    best_score = -1.0
    width = max(float(page_rect.width), 1.0)
    height = max(float(page_rect.height), 1.0)

    for row in group_words_into_rows(words):
        row_text = " ".join(str(word[4]) for word in row)
        row_upper = row_text.upper()
        row_has_title_block_label = bool(
            re.search(r"\b(sheet\s*(?:number|no\.?|#)|drawing\s*(?:number|no\.?))\b", row_text, re.IGNORECASE)
        )

        for candidate, start_index, _end_index, x0, y0, x1, y1 in row_sheet_number_candidates(row):
            key = sheet_lookup_key(candidate)
            x_center_ratio = ((x0 + x1) / 2.0) / width
            y_center_ratio = ((y0 + y1) / 2.0) / height
            x0_ratio = x0 / width
            y0_ratio = y0 / height

            score = 0.0
            score += x_center_ratio * 55
            score += y_center_ratio * 75

            if key in sheet_index:
                score += 90
            if row_has_title_block_label:
                score += 55
            if x0_ratio >= 0.62 and y0_ratio >= 0.66:
                score += 135
            elif x0_ratio >= 0.50 and y0_ratio >= 0.72:
                score += 95
            elif y0_ratio >= 0.84:
                score += 80
            elif x0_ratio >= 0.78:
                score += 45

            if len(candidate) <= 8:
                score += 8
            if sheet_prefix(candidate) in {"A", "AD", "G", "S", "C", "E", "M", "P", "FP", "ID", "LS", "FR"}:
                score += 10

            previous_word = str(row[start_index - 1][4]).upper().strip(":-") if start_index > 0 else ""
            if previous_word in {"SHEET", "NO", "NUMBER", "DRAWING"}:
                score += 20

            if "MATCH LINE" in row_upper or "MATCHLINE" in row_upper:
                score -= 140
            if previous_word in {"DETAIL", "SECTION", "ELEVATION", "KEYNOTE", "NOTE"}:
                score -= 75
            if x0_ratio < 0.42 and y0_ratio < 0.70 and not row_has_title_block_label and key not in sheet_index:
                score -= 90

            if score > best_score:
                best_number = sheet_index[key].sheet_number if key in sheet_index else candidate
                best_score = score

    return best_number if best_score >= 125 else ""


def detect_title_block_sheet_title(
    words: list[tuple],
    page_rect: "fitz.Rect",
    sheet_number: str,
) -> str:
    best_title = ""
    best_score = -1.0
    width = max(float(page_rect.width), 1.0)
    height = max(float(page_rect.height), 1.0)
    sheet_key = sheet_lookup_key(sheet_number)

    for row in group_words_into_rows(words):
        row_text = clean_title(" ".join(str(word[4]) for word in row))
        if not row_text or sheet_key and sheet_key in sheet_lookup_key(row_text):
            continue
        if TITLE_REJECT_RE.search(row_text):
            continue
        if re.search(r"\b(sheet\s*(?:number|no\.?|title)|drawing\s*(?:number|no\.?|title)|scale|date|revision)\b", row_text, re.IGNORECASE):
            continue

        x0 = min(float(word[0]) for word in row)
        y0 = min(float(word[1]) for word in row)
        x1 = max(float(word[2]) for word in row)
        x_center_ratio = ((x0 + x1) / 2.0) / width
        y_ratio = y0 / height

        title = clean_title(row_text)
        if not looks_like_title(title) and not title_is_floor_plan_like(title):
            continue

        score = 0.0
        if title_is_floor_plan_like(title):
            score += 45
        if TITLE_KEYWORD_RE.search(title):
            score += 25
        score += uppercase_ratio(title) * 12
        score += y_ratio * 45
        score += x_center_ratio * 18

        if y_ratio >= 0.58 and x_center_ratio >= 0.42:
            score += 60
        elif y_ratio >= 0.70:
            score += 40
        if len(title.split()) <= 1:
            score -= 25
        if re.search(r"\b(general|notes?|legend|abbreviations?|symbols?)\b", title, re.IGNORECASE):
            score -= 35

        if score > best_score:
            best_title = title
            best_score = score

    return best_title if best_score >= 42 else ""


def uppercase_ratio(value: str) -> float:
    letters = [char for char in value if char.isalpha()]
    if not letters:
        return 0.0
    uppercase = [char for char in letters if char.isupper()]
    return len(uppercase) / len(letters)


def clean_title(value: str) -> str:
    title = collapse_spaces(value)
    title = re.sub(r"^(?:sheet|drawing)\s+title\s*[:\-]?\s*", "", title, flags=re.IGNORECASE)
    title = title.strip(" :-|")
    return title[:120]


def looks_like_title(line: str) -> bool:
    if len(line) < 3 or len(line) > 90:
        return False
    if TITLE_REJECT_RE.search(line):
        return False
    if re.fullmatch(r"[\W\d_]+", line):
        return False
    digit_ratio = sum(char.isdigit() for char in line) / max(len(line), 1)
    if digit_ratio > 0.45:
        return False
    return bool(TITLE_KEYWORD_RE.search(line)) or uppercase_ratio(line) >= 0.65


def detect_sheet_title(lines: list[str], sheet_number_index: int | None) -> str:
    for index, line in enumerate(lines):
        explicit = re.search(
            r"\b(?:sheet|drawing)\s+title\s*[:\-]\s*(.+)$",
            line,
            flags=re.IGNORECASE,
        )
        if explicit:
            title = clean_title(explicit.group(1))
            if title and not TITLE_REJECT_RE.search(title):
                return title
            if index + 1 < len(lines):
                next_line = clean_title(lines[index + 1])
                if looks_like_title(next_line):
                    return next_line

    candidate_scores: list[tuple[float, str]] = []
    total = max(len(lines), 1)
    for index, line in enumerate(lines):
        title = clean_title(line)
        if not looks_like_title(title):
            continue

        score = 0.0
        if TITLE_KEYWORD_RE.search(title):
            score += 30
        score += uppercase_ratio(title) * 10
        score += (index / total) * 6

        if sheet_number_index is not None:
            distance = abs(index - sheet_number_index)
            if distance <= 5:
                score += 22 - (distance * 3)

        if COVER_OR_INDEX_TITLE_RE.search(title):
            score += 8
        if len(title.split()) <= 2 and not TITLE_KEYWORD_RE.search(title):
            score -= 8

        candidate_scores.append((score, title))

    if not candidate_scores:
        return ""

    candidate_scores.sort(key=lambda item: item[0], reverse=True)
    best_score, best_title = candidate_scores[0]
    return best_title if best_score >= 14 else ""


def clean_index_title(value: str) -> str:
    title = clean_title(value)
    title = re.sub(
        r"^(?:sheet|drawing)\s+(?:no\.?|number|title)\b\s*[:\-]?\s*",
        "",
        title,
        flags=re.IGNORECASE,
    )
    title = re.sub(r"\b(?:issued|date|revision|rev\.?)\s*[:\-]?\s*\S.*$", "", title, flags=re.IGNORECASE)
    title = re.sub(r"\.{2,}\s*\d+\s*$", "", title)
    title = re.sub(r"\s+(?:\d{1,3}|[A-Z]\d{1,3})\s*$", "", title)
    title = re.sub(r"\s{2,}", " ", title)
    return title.strip(" :-|")


def is_useful_index_title(title: str) -> bool:
    if len(title) < 3 or len(title) > 110:
        return False
    if SHEET_NUMBER_RE.fullmatch(title):
        return False
    if TITLE_REJECT_RE.search(title):
        return False
    if re.search(r"\b(sheet\s+(?:no\.?|number|title)|drawing\s+(?:no\.?|title))\b", title, re.IGNORECASE):
        return False
    letters = sum(char.isalpha() for char in title)
    if letters < 3:
        return False
    digit_ratio = sum(char.isdigit() for char in title) / max(len(title), 1)
    return digit_ratio <= 0.45


def clean_drawing_set_header(value: str) -> str:
    header = collapse_spaces(value)
    header = re.sub(r"^[\W\d_]+|[\W\d_:;-]+$", "", header).strip()
    header = re.sub(r"\s{2,}", " ", header)
    if not header or len(header) > 80:
        return ""
    if SHEET_NUMBER_RE.search(header):
        return ""

    normalized = header.lower()
    normalized = normalized.replace("&", " and ")
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized).strip()
    for label, pattern in DRAWING_SET_HEADER_PATTERNS:
        if re.fullmatch(pattern, normalized, flags=re.IGNORECASE):
            return label
    return ""


def nearest_allowed_column(bin_value: int, allowed_columns: set[int]) -> int:
    if not allowed_columns:
        return bin_value
    return min(allowed_columns, key=lambda allowed: abs(allowed - bin_value))


def row_text_chunks(row: list[tuple], gap: float = 60.0) -> list[tuple[float, str]]:
    chunks: list[list[tuple]] = []
    current: list[tuple] = []
    previous_x1: float | None = None
    for word in sorted(row, key=lambda item: item[0]):
        x0 = float(word[0])
        if current and previous_x1 is not None and x0 - previous_x1 > gap:
            chunks.append(current)
            current = []
        current.append(word)
        previous_x1 = float(word[2])
    if current:
        chunks.append(current)

    return [
        (
            sum(float(word[0]) for word in chunk) / max(len(chunk), 1),
            " ".join(str(word[4]) for word in chunk),
        )
        for chunk in chunks
    ]


def is_architectural_context(sheet_number: str, drawing_set: str) -> bool:
    prefix = sheet_prefix(sheet_number)
    return prefix.startswith("A") or bool(ARCHITECTURAL_SET_RE.search(drawing_set))


def is_structural_context(sheet_number: str, drawing_set: str) -> bool:
    prefix = sheet_prefix(sheet_number)
    return prefix.startswith("S") or bool(STRUCTURAL_SET_RE.search(drawing_set))


def is_floor_reference_context(drawing_set: str) -> bool:
    return bool(FLOOR_REFERENCE_SET_RE.search(drawing_set))


def is_other_discipline_context(sheet_number: str, drawing_set: str) -> bool:
    prefix = sheet_prefix(sheet_number)
    return prefix in DISCIPLINE_OTHER_PREFIXES or bool(DISCIPLINE_OTHER_SET_RE.search(drawing_set))


def detected_discipline(sheet_number: str, drawing_set: str) -> str:
    prefix = sheet_prefix(sheet_number)
    context = drawing_set.lower()
    if prefix.startswith("A") or "architectural" in context:
        return "architectural"
    if prefix.startswith("S") or "structural" in context:
        return "structural"
    if prefix == "M" or "mechanical" in context:
        return "mechanical"
    if prefix == "E" or "electrical" in context:
        return "electrical"
    if prefix == "P" or "plumbing" in context:
        return "plumbing"
    if prefix in {"FA", "FS"} or "fire alarm" in context:
        return "fire_alarm"
    if prefix == "FP" or "fire protection" in context:
        return "fire_protection"
    if prefix in {"V", "DS"} or "vendor" in context or "detail" in context:
        return "vendor_detail"
    if prefix in {"CS", "G"}:
        return "cover_index"
    if prefix:
        return prefix.lower()
    return ""


def discipline_category(sheet_number: str, drawing_set: str) -> str | None:
    discipline = detected_discipline(sheet_number, drawing_set)
    if discipline == "mechanical":
        return CATEGORY_MECHANICAL
    if discipline == "electrical":
        return CATEGORY_ELECTRICAL
    if discipline == "plumbing":
        return CATEGORY_PLUMBING
    if discipline == "fire_alarm":
        return CATEGORY_FIRE_ALARM
    if discipline == "fire_protection":
        return CATEGORY_FIRE_PROTECTION
    if discipline == "vendor_detail" or is_other_discipline_context(sheet_number, drawing_set):
        return CATEGORY_VENDOR_DETAIL
    return None


def title_has_floor_level(title: str) -> bool:
    return bool(FLOOR_LEVEL_RE.search(title))


def title_is_floor_plan_like(title: str) -> bool:
    if NON_FLOOR_TITLE_RE.search(title):
        return False
    if re.search(r"\b(life\s+safety|reflected\s+ceiling|RCP|overall|enlarged)\s+plans?\b", title, re.IGNORECASE):
        return True
    if re.search(
        r"\b(?:floor|level|roof|ground|basement|first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|"
        r"1st|2nd|3rd|[4-9]th|area|sector|zone|part|portion)\b.*\bplans?\b|"
        r"\bplans?\b.*\b(?:floor|level|roof|area|sector|zone|part|portion)\b",
        title,
        re.IGNORECASE,
    ):
        return True
    return title_has_floor_level(title)


def metadata_render_zoom(rect: "fitz.Rect") -> float:
    preferred_zoom = METADATA_RENDER_DPI / 72.0
    page_pixels = max(float(rect.width) * float(rect.height) * preferred_zoom * preferred_zoom, 1.0)
    if page_pixels <= MAX_METADATA_RENDER_PIXELS:
        return preferred_zoom
    return math.sqrt(MAX_METADATA_RENDER_PIXELS / max(float(rect.width) * float(rect.height), 1.0))


def render_metadata_image(page: "fitz.Page") -> str:
    rect = page.rect
    orientation = "landscape" if rect.width >= rect.height else "portrait"
    zoom = metadata_render_zoom(rect)
    pixmap = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False, colorspace=fitz.csGRAY)
    width = pixmap.width
    height = pixmap.height
    pixmap = None
    return f"{orientation}; rendered {width}x{height}px for metadata scan"


def extract_page_ocr_text(page: "fitz.Page", dpi: int) -> tuple[str, list[tuple], str]:
    try:
        textpage = page.get_textpage_ocr(dpi=dpi, full=True)
        text = page.get_text("text", textpage=textpage, sort=True) or ""
        words = page.get_text("words", textpage=textpage, sort=True) or []
        return text, words, f"ocr {dpi}dpi text length {len(text)}"
    except Exception as exc:
        return "", [], f"ocr {dpi}dpi unavailable: {exc}"


def words_in_ratio_box(
    words: list[tuple],
    page_rect: "fitz.Rect",
    left: float,
    top: float,
    right: float,
    bottom: float,
) -> list[tuple]:
    width = max(float(page_rect.width), 1.0)
    height = max(float(page_rect.height), 1.0)
    return [
        word
        for word in words
        if left <= float(word[0]) / width <= right and top <= float(word[1]) / height <= bottom
    ]


def words_to_text(words: list[tuple]) -> str:
    rows = group_words_into_rows(words)
    return "\n".join(
        collapse_spaces(" ".join(str(word[4]) for word in row))
        for row in rows
        if row
    )


def extract_title_block_text(words: list[tuple], page_rect: "fitz.Rect") -> str:
    zones = [
        ("right_vertical_strip", words_in_ratio_box(words, page_rect, 0.72, 0.00, 1.00, 1.00)),
        ("bottom_right_corner", words_in_ratio_box(words, page_rect, 0.52, 0.58, 1.00, 1.00)),
        ("bottom_title_strip", words_in_ratio_box(words, page_rect, 0.00, 0.76, 1.00, 1.00)),
        ("top_right_fallback", words_in_ratio_box(words, page_rect, 0.58, 0.00, 1.00, 0.28)),
    ]
    parts = []
    seen = set()
    for label, zone_words in zones:
        text = words_to_text(zone_words)
        if text and text not in seen:
            parts.append(f"[{label}]\n{text}")
            seen.add(text)
    return "\n\n".join(parts)


def edit_distance_at_most(left: str, right: str, limit: int = 1) -> bool:
    if abs(len(left) - len(right)) > limit:
        return False
    previous = list(range(len(right) + 1))
    for i, left_char in enumerate(left, start=1):
        current = [i]
        row_min = i
        for j, right_char in enumerate(right, start=1):
            cost = 0 if left_char == right_char else 1
            value = min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + cost)
            current.append(value)
            row_min = min(row_min, value)
        if row_min > limit:
            return False
        previous = current
    return previous[-1] <= limit


def find_sheet_index_entry(
    sheet_number: str,
    sheet_index: dict[str, SheetIndexEntry],
) -> tuple[SheetIndexEntry | None, bool]:
    if not sheet_number:
        return None, False
    key = sheet_lookup_key(sheet_number)
    if key in sheet_index:
        return sheet_index[key], False

    ocr_key = key.replace("O", "0").replace("I", "1")
    for index_key, entry in sheet_index.items():
        normalized_index_key = index_key.replace("O", "0").replace("I", "1")
        if normalized_index_key == ocr_key:
            return entry, True
        if ocr_key != key and edit_distance_at_most(normalized_index_key, ocr_key, 1):
            return entry, True
    return None, False


def category_slug(category_file: str) -> str:
    return CATEGORY_SLUGS.get(category_file, "unknown_needs_manual_review")


def category_from_slug(slug: str) -> str | None:
    if slug in {"window_schedules", "storefront_schedules"}:
        return CATEGORY_WINDOW_STOREFRONT_SCHEDULES
    if slug == "storefront_door_window_elevations":
        return CATEGORY_EXTERIOR_ELEVATIONS
    for category, category_slug_value in CATEGORY_SLUGS.items():
        if category_slug_value == slug:
            return category
    return None


def clamp_score(value: float) -> float:
    return max(0.0, min(1.0, value))


def candidate(category: str, score: float) -> dict[str, object]:
    return {"category": category_slug(category), "score": round(clamp_score(score), 2)}


def confidence_or_review(category: str, confidence: float, reason: str) -> tuple[str, float, str, bool]:
    confidence = max(0.0, min(1.0, confidence))
    if confidence < MANUAL_REVIEW_THRESHOLD:
        return (
            CATEGORY_REVIEW,
            confidence,
            f"Needs manual review: {reason}",
            True,
        )
    return category, confidence, reason, False


def title_has_schedule(title: str) -> bool:
    return bool(re.search(r"\bschedules?\b|\bsched\.?\b", title, re.IGNORECASE))


def title_has_exterior_elevation(title: str) -> bool:
    return bool(
        re.search(
            r"\b(exterior|building|front|rear|left|right|north|south|east|west)\s+elevations?\b|"
            r"\belevations?\s*[-:]?\s*(front|rear|left|right|north|south|east|west)\b",
            title,
            re.IGNORECASE,
        )
    )


def title_has_opening_elevation(title: str) -> bool:
    return bool(
        re.search(
            r"\b(window|door|store\s*front|storefront|curtain\s+wall|glazing|opening)s?\b.*\b(elevations?|types?|details?)\b|"
            r"\b(elevations?|types?|details?)\b.*\b(window|door|store\s*front|storefront|curtain\s+wall|glazing|opening)s?\b",
            title,
            re.IGNORECASE,
        )
    )


def table_like_row_count(words: list[tuple]) -> int:
    return sum(1 for row in group_words_into_rows(words) if len(row) >= 4)


def has_schedule_table(text: str, words: list[tuple], schedule_type: str) -> bool:
    table_like = table_like_row_count(words) >= 8
    lowered = text.lower()
    if schedule_type == "door":
        indicators = [
            r"\bdoor\s+schedules?\b",
            r"\bopening\s+schedules?\b",
            r"\bframe\b",
            r"\bhardware\b",
            r"\bwidth\b",
            r"\bheight\b",
            r"\bdoor\s+type\b",
        ]
    elif schedule_type == "window":
        indicators = [
            r"\bwindow\s+schedules?\b",
            r"\bglazing\s+schedules?\b",
            r"\bglass\s+type\b",
            r"\bframe\b",
            r"\bremarks?\b",
            r"\bW-?\d+\b",
        ]
    else:
        indicators = [
            r"\bstore\s*front\s+schedules?\b",
            r"\bstorefront\s+schedules?\b",
            r"\bcurtain\s+wall\b",
            r"\baluminum\s+storefront\b",
            r"\bframe\s+finish\b",
            r"\bglass\s+makeup\b",
            r"\bopening\s+mark\b",
            r"\bdoor\s+type\b",
            r"\bframing\s+system\b",
            r"\b(?:SF|CW|SG)-?\d+\b",
        ]
    hits = sum(1 for pattern in indicators if re.search(pattern, lowered, re.IGNORECASE))
    if schedule_type == "storefront":
        return hits >= 2 and has_storefront_system_signal(text) and (table_like or hits >= 3)
    return hits >= 2 and (table_like or hits >= 3)


def bbox_from_words(words: list[tuple]) -> list[float]:
    if not words:
        return [0.0, 0.0, 0.0, 0.0]
    return [
        round(min(float(word[0]) for word in words), 2),
        round(min(float(word[1]) for word in words), 2),
        round(max(float(word[2]) for word in words), 2),
        round(max(float(word[3]) for word in words), 2),
    ]


def row_column_signature(row: list[tuple]) -> set[int]:
    return {int(round(float(word[0]) / 18.0) * 18) for word in row}


def row_text(row: list[tuple]) -> str:
    return collapse_spaces(" ".join(str(word[4]) for word in sorted(row, key=lambda item: item[0])))


def is_table_candidate_row(row: list[tuple]) -> bool:
    text = row_text(row)
    if len(row) >= 4:
        return True
    if len(row) >= 3 and re.search(r"\b(mark|type|width|height|frame|glass|hardware|remarks?|finish|size)\b", text, re.IGNORECASE):
        return True
    return False


def detect_table_region_word_groups(words: list[tuple]) -> list[list[tuple]]:
    rows = group_words_into_rows(words)
    groups: list[list[list[tuple]]] = []
    current: list[list[tuple]] = []
    current_signature: set[int] = set()
    previous_y: float | None = None

    for row in rows:
        y0 = min(float(word[1]) for word in row)
        signature = row_column_signature(row)
        table_like = is_table_candidate_row(row)
        overlaps_current = bool(current_signature and len(signature & current_signature) >= 2)
        close_to_previous = previous_y is None or y0 - previous_y <= 34

        if table_like and (not current or overlaps_current or close_to_previous):
            current.append(row)
            current_signature = signature if not current_signature else current_signature | signature
            previous_y = y0
            continue

        if len(current) >= 3:
            groups.append(current)
        current = [row] if table_like else []
        current_signature = signature if table_like else set()
        previous_y = y0 if table_like else None

    if len(current) >= 3:
        groups.append(current)

    word_groups: list[list[tuple]] = []
    for group in groups:
        group_words = [word for row in group for word in row]
        if len(group_words) >= 10:
            word_groups.append(group_words)
    return word_groups


def rows_from_words(words: list[tuple]) -> list[list[str]]:
    rows: list[list[str]] = []
    for row in group_words_into_rows(words):
        values = [str(word[4]) for word in sorted(row, key=lambda item: item[0])]
        if values:
            rows.append(values)
    return rows


def count_patterns(patterns: list[str], text: str) -> int:
    return sum(1 for pattern in patterns if re.search(pattern, text, re.IGNORECASE))


def repeated_mark_count(pattern: str, text: str) -> int:
    return len(set(re.findall(pattern, text, re.IGNORECASE)))


def storefront_system_signal_count(text: str) -> int:
    return count_patterns(
        [
            r"\bstore\s*front\b",
            r"\bstorefront\b",
            r"\bcurtain\s+wall\b",
            r"\baluminum\s+storefront\b",
            r"\bentrance\s+system\b",
            r"\bframing\s+system\b",
            r"\bframe\s+finish\b",
            r"\bglass\s+makeup\b",
            r"\bdoor\s+type\b",
            r"\bopening\s+mark\b",
            r"\b(?:SF|CW|SG)-?\d+\b",
        ],
        text,
    )


def has_storefront_system_signal(text: str) -> bool:
    return storefront_system_signal_count(text) >= 2


def classify_schedule_region(
    region_text: str,
    region_words: list[tuple],
    sheet_title: str,
    drawing_set: str,
    detected_sheet_discipline: str,
) -> tuple[str, float, str, bool]:
    combined = f"{sheet_title}\n{region_text}"
    if detected_sheet_discipline == "vendor_detail":
        return (
            REGION_VENDOR_DETAIL,
            0.90,
            "Vendor/detail discipline detected; not mixed into architectural door/window/storefront schedules.",
            False,
        )

    table_rows = table_like_row_count(region_words)
    has_table_structure = table_rows >= 3 and len(region_words) >= 10

    hardware_header = bool(re.search(r"\bhardware\s+schedules?\b", combined, re.IGNORECASE))
    hardware_cols = count_patterns([r"\bhardware\b", r"\bset\b", r"\bgroup\b", r"\bremarks?\b"], region_text)
    if has_table_structure and hardware_header and hardware_cols >= 2:
        return (
            REGION_HARDWARE_SCHEDULE,
            0.90,
            "Detected hardware schedule table with hardware header and schedule-style columns.",
            False,
        )

    competing_opening_header = bool(
        re.search(
            r"\b(window|glazing|store\s*front|storefront|curtain\s+wall)\b.{0,30}\b(schedules?|types?)\b|"
            r"\b(schedules?|types?)\b.{0,30}\b(window|glazing|store\s*front|storefront|curtain\s+wall)\b",
            combined,
            re.IGNORECASE,
        )
    )
    door_header = bool(re.search(r"\bdoor\s+schedules?\b|\bopening\s+schedules?\b|\bdoor\s*&\s*frame\s+schedules?\b", combined, re.IGNORECASE))
    door_cols = count_patterns(
        [r"\bmark\b", r"\bdoor\s+no\b", r"\bopening\b", r"\bwidth\b", r"\bheight\b", r"\btype\b", r"\bframe\b", r"\bmaterial\b", r"\bhardware\b", r"\bremarks?\b"],
        region_text,
    )
    door_marks = repeated_mark_count(r"\b(?:[1-9]\d{2,3}|[A-Z]?\d{2,4})\b", region_text)
    if has_table_structure and not competing_opening_header and door_header and door_cols >= 4 and door_marks >= 2:
        return (
            REGION_DOOR_SCHEDULE,
            0.93,
            "Detected table titled door/opening schedule with schedule columns and repeated door/opening marks.",
            False,
        )
    if has_table_structure and not competing_opening_header and ((door_header and door_cols >= 3) or (door_cols >= 5 and door_marks >= 2)):
        return confidence_or_region_review(
            REGION_DOOR_SCHEDULE,
            0.82,
            "Detected door schedule table from schedule columns and repeated opening marks.",
        )

    glazing_header = bool(re.search(r"\bglazing\s+schedules?\b", combined, re.IGNORECASE))
    storefront_signal_count = storefront_system_signal_count(combined)
    storefront_system_signal = storefront_signal_count >= 2
    storefront_header = bool(
        re.search(
            r"\bstore\s*front\s+schedules?\b|\bstorefront\s+schedules?\b|\bcurtain\s+wall\s+schedules?\b|"
            r"\baluminum\s+storefront\s+schedules?\b",
            combined,
            re.IGNORECASE,
        )
    ) or (glazing_header and storefront_system_signal)
    storefront_cols = count_patterns(
        [
            r"\bmark\b",
            r"\bopening\b",
            r"\belevations?\b",
            r"\bwidth\b",
            r"\bheight\b",
            r"\bframe\b",
            r"\bframe\s+finish\b",
            r"\bfinish\b",
            r"\bglass\b",
            r"\bglass\s+makeup\b",
            r"\bdoor\s+type\b",
            r"\bremarks?\b",
            r"\bsystem\b",
            r"\baluminum\b",
        ],
        region_text,
    )
    storefront_marks = repeated_mark_count(r"\b(?:SF-?\d+|CW-?\d+|SG-?\d+)\b", region_text)
    if storefront_system_signal:
        storefront_marks += repeated_mark_count(r"\b[PQR]\b", region_text)
    storefront_material = bool(
        re.search(
            r"\bglass\s+makeup\b|\bframe\s+finish\b|\baluminum\s+storefront\b|\bcurtain\s+wall\b|\bframing\s+system\b",
            region_text,
            re.IGNORECASE,
        )
    )
    if has_table_structure and storefront_header and storefront_cols >= 3 and (storefront_marks >= 1 or storefront_material):
        return (
            REGION_STOREFRONT_SCHEDULE,
            0.92,
            "Detected storefront/curtain wall schedule table with frame/glass/opening data.",
            False,
        )
    if has_table_structure and storefront_system_signal and storefront_cols >= 4 and storefront_material:
        return confidence_or_region_review(
            REGION_STOREFRONT_SCHEDULE,
            0.82,
            "Detected storefront schedule from frame finish/glass makeup/opening columns.",
        )

    glazing_cols = count_patterns(
        [r"\bmark\b", r"\btype\b", r"\bwidth\b", r"\bheight\b", r"\bglass\b", r"\bU\s*[- ]?\s*factor\b", r"\bSHGC\b", r"\bremarks?\b", r"\bframe\b", r"\bfinish\b"],
        region_text,
    )
    glazing_marks = repeated_mark_count(r"\b(?:W-?\d+[A-Z]?|R-[A-Z]|G-?\d+)\b", region_text)
    if has_table_structure and glazing_header and glazing_cols >= 3 and glazing_marks >= 1:
        return (
            REGION_GLAZING_SCHEDULE,
            0.91,
            "Detected glazing schedule table with glass/spec columns and repeated opening/glazing marks.",
            False,
        )

    window_header = bool(re.search(r"\bwindow\s+schedules?\b|\bwindow\s+types?\b|\bopening\s+schedules?\b", combined, re.IGNORECASE))
    window_cols = count_patterns(
        [r"\bmark\b", r"\btype\b", r"\bwidth\b", r"\bheight\b", r"\bglass\b", r"\bframe\b", r"\bfinish\b", r"\bU\s*[- ]?\s*factor\b", r"\bSHGC\b", r"\bremarks?\b"],
        region_text,
    )
    window_marks = repeated_mark_count(r"\b(?:W-?\d+[A-Z]?|R-[A-Z])\b", region_text)
    if has_table_structure and window_header and window_cols >= 4 and window_marks >= 2:
        return (
            REGION_WINDOW_SCHEDULE,
            0.93,
            "Detected window schedule/types table with marks, size/spec columns, and repeated window marks.",
            False,
        )
    if has_table_structure and ((window_header and window_cols >= 3) or (window_cols >= 5 and window_marks >= 2)):
        return confidence_or_region_review(
            REGION_WINDOW_SCHEDULE,
            0.82,
            "Detected window schedule table from window marks and size/spec columns.",
        )

    if has_table_structure and re.search(r"\bschedules?\b", combined, re.IGNORECASE):
        return confidence_or_region_review(
            REGION_REVIEW,
            0.62,
            "Detected a table on a schedule sheet, but schedule type signals were incomplete.",
        )

    return confidence_or_region_review(
        REGION_REVIEW,
        0.45,
        "Detected table-like layout, but it does not have enough schedule columns or repeated valid marks.",
    )


def confidence_or_region_review(category: str, confidence: float, reason: str) -> tuple[str, float, str, bool]:
    confidence = max(0.0, min(1.0, confidence))
    if confidence < MANUAL_REVIEW_THRESHOLD:
        return REGION_REVIEW, confidence, f"Needs manual review: {reason}", True
    return category, confidence, reason, False


def region_evidence_scores(
    category: str,
    confidence: float,
    text: str,
    words: list[tuple],
) -> dict[str, float]:
    table_rows = table_like_row_count(words)
    has_schedule_title = bool(re.search(r"\bschedules?\b|\btypes?\b", text, re.IGNORECASE))
    mark_patterns = [
        r"\b(?:[1-9]\d{2,3}|[A-Z]?\d{2,4})\b",
        r"\b(?:W-?\d+[A-Z]?|R-[A-Z]|G-?\d+)\b",
        r"\b(?:SF-?\d+|CW-?\d+|SG-?\d+)\b",
    ]
    mark_count = max(repeated_mark_count(pattern, text) for pattern in mark_patterns)
    visual_layout = 0.85 if category in {REGION_EXTERIOR_ELEVATION, REGION_STOREFRONT_ELEVATION} else 0.25
    if table_rows >= 3:
        visual_layout = max(visual_layout, 0.65)
    return {
        "title_block_score": round(0.70 if has_schedule_title else 0.20, 2),
        "index_match_score": 0.0,
        "keyword_score": round(min(1.0, len(matched_index_keywords(text)) / 4.0), 2),
        "table_structure_score": round(min(1.0, table_rows / 5.0), 2),
        "mark_pattern_score": round(min(1.0, mark_count / 3.0), 2),
        "visual_layout_score": round(visual_layout, 2),
        "neighbor_score": 0.0,
        "combined_score": round(clamp_score(confidence), 2),
    }


def classify_non_table_region(
    text: str,
    sheet_title: str,
    detected_sheet_discipline: str,
) -> tuple[str, float, str, bool]:
    combined = f"{sheet_title}\n{text}"
    if detected_sheet_discipline == "vendor_detail":
        return REGION_VENDOR_DETAIL, 0.90, "Vendor/detail sheet metadata controls this non-schedule region.", False
    if title_has_exterior_elevation(combined):
        return REGION_EXTERIOR_ELEVATION, 0.86, "Region/sheet title identifies exterior/building elevation drawings without schedule-table structure.", False
    if re.search(r"\bstore\s*front|storefront|curtain\s+wall\b", combined, re.IGNORECASE) and re.search(r"\belevations?\b", combined, re.IGNORECASE):
        return REGION_STOREFRONT_ELEVATION, 0.86, "Region identifies storefront elevation drawings without schedule-table structure.", False
    if re.search(r"\b(general\s+notes?|notes?|specifications?)\b", combined, re.IGNORECASE):
        return REGION_GENERAL_NOTES, 0.80, "Region identifies general notes/specifications without schedule-table structure.", False
    if re.search(r"\bdoor\b", combined, re.IGNORECASE) and re.search(r"\b(details?|sections?|head|jamb|sill|anchor|threshold)\b", combined, re.IGNORECASE):
        return REGION_DOOR_DETAIL, 0.84, "Region identifies door details/sections, not a schedule table.", False
    if re.search(r"\bwindow\b", combined, re.IGNORECASE) and re.search(r"\b(details?|sections?|head|jamb|sill|anchor)\b", combined, re.IGNORECASE):
        return REGION_WINDOW_DETAIL, 0.84, "Region identifies window details/sections, not a schedule table.", False
    if re.search(r"\bstore\s*front|storefront|curtain\s+wall\b", combined, re.IGNORECASE) and re.search(r"\b(details?|sections?|head|jamb|sill|anchor)\b", combined, re.IGNORECASE):
        return REGION_STOREFRONT_DETAIL, 0.84, "Region identifies storefront details/sections, not a schedule table.", False
    return confidence_or_region_review(REGION_REVIEW, 0.55, "No high-confidence table, elevation, detail, note, or vendor region rule matched.")


def detect_page_regions(
    page_index: int,
    pdf_page_number: int,
    words: list[tuple],
    page_rect: "fitz.Rect",
    sheet_number: str,
    sheet_title: str,
    drawing_set: str,
) -> list[RegionRecord]:
    regions: list[RegionRecord] = []
    discipline = detected_discipline(sheet_number, drawing_set)
    seen_bboxes: set[tuple[float, ...]] = set()

    for region_number, region_words in enumerate(detect_table_region_word_groups(words), start=1):
        bbox = bbox_from_words(region_words)
        bbox_key = tuple(bbox)
        if bbox_key in seen_bboxes:
            continue
        seen_bboxes.add(bbox_key)
        rows = rows_from_words(region_words)
        region_text = "\n".join(" ".join(row) for row in rows)
        category, confidence, reason, needs_review = classify_schedule_region(
            region_text,
            region_words,
            sheet_title,
            drawing_set,
            discipline,
        )
        regions.append(
            RegionRecord(
                page_index=page_index,
                pdf_page_number=pdf_page_number,
                sheet_number=sheet_number,
                sheet_title=sheet_title,
                region_id=f"{sheet_number or 'PAGE'}_R{region_number}",
                region_bbox=bbox,
                region_category=category,
                confidence=confidence,
                reason=reason,
                needs_manual_review=needs_review,
                extracted_rows=rows if category.endswith("_schedule_table") else [],
                raw_text=region_text,
                evidence_scores=region_evidence_scores(category, confidence, region_text, region_words),
            )
        )

    full_text = words_to_text(words)
    should_add_summary_region = not regions or bool(
        re.search(
            r"\b(elevation|detail|section|notes?|vendor|shop\s+drawing|store\s*front|storefront|door|window|glazing)\b",
            f"{sheet_title}\n{full_text}",
            re.IGNORECASE,
        )
    )
    if should_add_summary_region:
        category, confidence, reason, needs_review = classify_non_table_region(full_text, sheet_title, discipline)
        if category != REGION_REVIEW or not regions:
            regions.append(
                RegionRecord(
                    page_index=page_index,
                    pdf_page_number=pdf_page_number,
                    sheet_number=sheet_number,
                    sheet_title=sheet_title,
                    region_id=f"{sheet_number or 'PAGE'}_R{len(regions) + 1}",
                    region_bbox=bbox_from_words(words) if words else [0.0, 0.0, round(float(page_rect.width), 2), round(float(page_rect.height), 2)],
                    region_category=category,
                    confidence=confidence,
                    reason=reason,
                    needs_manual_review=needs_review,
                    extracted_rows=[],
                    raw_text=full_text,
                    evidence_scores=region_evidence_scores(category, confidence, full_text, words),
                )
            )

    return regions


def index_metadata_allows_schedule_region(
    default_category: str,
    region_category: str,
    sheet_title: str,
    drawing_set: str,
    matched_index: bool,
) -> bool:
    """Keep drawing-index/title-block metadata above table hits when they conflict."""
    if not matched_index:
        return True

    schedule_page_category = REGION_SCHEDULE_TO_PAGE_CATEGORY.get(region_category)
    if schedule_page_category is None:
        return True
    if default_category == schedule_page_category:
        return True

    metadata_text = f"{drawing_set}\n{sheet_title}"
    if title_has_schedule(metadata_text) and default_category in {CATEGORY_REVIEW, CATEGORY_VENDOR_DETAIL}:
        return True
    if region_category in {REGION_DOOR_SCHEDULE, REGION_HARDWARE_SCHEDULE}:
        return bool(
            re.search(r"\b(door|opening|frame|hardware)\b", metadata_text, re.IGNORECASE)
            and title_has_schedule(metadata_text)
        )
    if region_category in {REGION_WINDOW_SCHEDULE, REGION_GLAZING_SCHEDULE}:
        return bool(
            re.search(r"\b(window|glaz(?:ing|ed)|glass)\b", metadata_text, re.IGNORECASE)
            and title_has_schedule(metadata_text)
        )
    if region_category == REGION_STOREFRONT_SCHEDULE:
        return bool(
            re.search(r"\b(store\s*front|storefront|curtain\s+wall|glaz(?:ing|ed)|glass)\b", metadata_text, re.IGNORECASE)
            and title_has_schedule(metadata_text)
        )
    return False


def page_category_from_regions(
    default_category: str,
    default_confidence: float,
    default_reason: str,
    regions: list[RegionRecord],
    sheet_title: str = "",
    drawing_set: str = "",
    matched_index: bool = False,
) -> tuple[str, float, str, bool]:
    high_confidence_regions = [region for region in regions if region.confidence >= MANUAL_REVIEW_THRESHOLD]
    blocked_region_reasons: list[str] = []

    for region_category in [
        REGION_DOOR_SCHEDULE,
        REGION_HARDWARE_SCHEDULE,
        REGION_STOREFRONT_SCHEDULE,
        REGION_GLAZING_SCHEDULE,
        REGION_WINDOW_SCHEDULE,
    ]:
        matches = [region for region in high_confidence_regions if region.region_category == region_category]
        if matches:
            best = max(matches, key=lambda region: region.confidence)
            category = REGION_SCHEDULE_TO_PAGE_CATEGORY[region_category]
            if not index_metadata_allows_schedule_region(
                default_category,
                region_category,
                sheet_title,
                drawing_set,
                matched_index,
            ):
                blocked_region_reasons.append(
                    f"{region_category} was detected, but drawing-index/title metadata points to "
                    f"{category_slug(default_category)}."
                )
                continue
            return (
                category,
                max(default_confidence, best.confidence),
                f"Schedule table region controls page split: {best.reason}",
                False,
            )

    if blocked_region_reasons:
        return (
            default_category,
            min(default_confidence, 0.74),
            "Needs manual review: verified sheet against drawing index/title block before category assignment; "
            + " ".join(blocked_region_reasons),
            True,
        )

    if default_category in {CATEGORY_DOOR_SCHEDULES, CATEGORY_WINDOW_SCHEDULES, CATEGORY_STOREFRONT_SCHEDULES}:
        return (
            CATEGORY_REVIEW,
            min(default_confidence, 0.70),
            "Needs manual review: sheet metadata suggested a schedule, but no high-confidence schedule-style table region was detected.",
            True,
        )

    for region_category, category in [
        (REGION_EXTERIOR_ELEVATION, CATEGORY_EXTERIOR_ELEVATIONS),
        (REGION_STOREFRONT_ELEVATION, CATEGORY_EXTERIOR_ELEVATIONS),
    ]:
        matches = [region for region in high_confidence_regions if region.region_category == region_category]
        if matches and default_category in {CATEGORY_REVIEW, CATEGORY_EXTERIOR_ELEVATIONS, CATEGORY_OPENING_ELEVATIONS}:
            best = max(matches, key=lambda region: region.confidence)
            return category, max(default_confidence, best.confidence), best.reason, False

    return (
        default_category,
        default_confidence,
        default_reason,
        default_confidence < MANUAL_REVIEW_THRESHOLD or default_category == CATEGORY_REVIEW,
    )


def small_plan_mode_decision(
    page_count: int,
    sheet_index: dict[str, SheetIndexEntry],
    index_page_indexes: set[int],
    records: list[PageRecord] | None = None,
) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    if page_count <= SMALL_PLAN_PAGE_THRESHOLD:
        reasons.append(f"low page count ({page_count} pages)")
    if not sheet_index or not index_page_indexes:
        reasons.append("no reliable drawing index")
    elif len(sheet_index) < max(3, min(8, page_count // 2)):
        reasons.append(f"weak drawing index ({len(sheet_index)} entries)")

    if records:
        matched_ratio = sum(1 for record in records if record.matched_index) / max(len(records), 1)
        title_ratio = sum(1 for record in records if record.sheet_number or record.sheet_title) / max(len(records), 1)
        low_conf_ratio = sum(1 for record in records if record.confidence < MANUAL_REVIEW_THRESHOLD) / max(len(records), 1)
        if matched_ratio < WEAK_INDEX_MATCH_RATIO:
            reasons.append(f"low index match ratio ({matched_ratio:.0%})")
        if title_ratio < WEAK_TITLE_BLOCK_RATIO:
            reasons.append(f"weak title-block/title recovery ({title_ratio:.0%})")
        if low_conf_ratio >= LOW_CONFIDENCE_RATIO:
            reasons.append(f"many low-confidence pages ({low_conf_ratio:.0%})")

    return bool(reasons), reasons


def apply_small_plan_mode(records: list[PageRecord], active: bool, reasons: list[str]) -> list[PageRecord]:
    if not active:
        return [
            replace(record, small_plan_mode=False)
            for record in records
        ]

    updated: list[PageRecord] = []
    mode_reason = "Small Plan Mode active: " + "; ".join(reasons)
    for record in records:
        confidence = record.confidence
        needs_manual_review = record.needs_manual_review
        reason = record.reason
        category_files = record.category_files

        has_strong_region = any(region.confidence >= MANUAL_REVIEW_THRESHOLD for region in record.regions)
        weak_metadata = not record.matched_index and not record.sheet_number and record.sheet_title_source == "not found"
        if weak_metadata and not has_strong_region:
            confidence = min(confidence, 0.70)
            needs_manual_review = True
            category_files = [CATEGORY_REVIEW]
            reason = f"Needs manual review: {mode_reason}; no reliable index/title-block/table evidence."
        elif confidence < MANUAL_REVIEW_THRESHOLD:
            needs_manual_review = True
            reason = f"{record.reason} {mode_reason}."

        evidence_scores = dict(record.evidence_scores)
        combined_confidence = confidence
        evidence_scores["combined_score"] = round(clamp_score(combined_confidence), 2)
        top_candidates = list(record.top_candidates)
        if category_files and category_slug(category_files[0]) != (top_candidates[0]["category"] if top_candidates else ""):
            top_candidates = [candidate(category_files[0], combined_confidence)] + [
                item for item in top_candidates if item.get("category") != category_slug(category_files[0])
            ]
            top_candidates = top_candidates[:3]
        updated.append(
            replace(
                record,
                confidence=combined_confidence,
                reason=reason if mode_reason in reason else f"{reason} {mode_reason}.",
                needs_manual_review=needs_manual_review or combined_confidence < MANUAL_REVIEW_THRESHOLD,
                category_files=category_files,
                evidence_scores=evidence_scores,
                top_candidates=top_candidates,
                small_plan_mode=True,
            )
        )
    return updated


def has_wind_pressure_evidence(text: str) -> bool:
    return bool(
        re.search(
            r"\bwind\s+pressure\b|\bwall\s+wind\s+pressure\b|\bcomponent(?:s)?\s+(?:and|&)\s+cladding\b|"
            r"\bC\s*&\s*C\b|\bopening\s+pressures?\b|\bzone\s+[45]\b|"
            r"\bpositive\b.{0,40}\bnegative\b|\bnegative\b.{0,40}\bpositive\b|"
            r"\bpsf\b|\bp\.?\s*s\.?\s*f\.?\b|\btributary\s+area\b",
            text,
            re.IGNORECASE,
        )
    )


def has_kitchen_evidence(text: str, sheet_number: str = "", drawing_set: str = "") -> bool:
    combined = f"{drawing_set}\n{sheet_number}\n{text}"
    if re.search(r"\bvendor\b|\bmanufacturer\b|\bspec\s+sheets?\b|\bshop\s+drawings?\b", combined, re.IGNORECASE):
        if not re.search(r"\bkitchen\b|\bfood\s*service\b|\bfoodservice\b", combined, re.IGNORECASE):
            return False
    if re.search(
        r"\bkitchen\b|\bfood\s*service\b|\bfoodservice\b|\bcommercial\s+kitchen\b|\bkitchen\s+equipment\b",
        combined,
        re.IGNORECASE,
    ):
        return True
    prefix = sheet_prefix(sheet_number)
    if prefix in {"K", "KE", "FS"} and re.search(
        r"\bequipment\b|\bhoods?\b|\bgrease\b|\bdish\s*wash|\bwalk\s*[- ]?in\s+(?:cooler|freezer)\b",
        combined,
        re.IGNORECASE,
    ):
        return True
    if re.search(r"\bhoods?\b|\bgrease\s+(?:interceptor|trap|duct)\b", combined, re.IGNORECASE) and re.search(
        r"\bequipment\b|\bplan\b|\bschedules?\b",
        combined,
        re.IGNORECASE,
    ):
        return True
    return False


def classify_metadata_first(
    text: str,
    words: list[tuple],
    sheet_number: str,
    sheet_title: str,
    drawing_set: str,
    is_index_page: bool,
    matched_index: bool,
    raw_title_block_text: str,
) -> tuple[str, float, str, bool, list[str]]:
    title = sheet_title or ""
    title_context = f"{drawing_set}\n{title}"
    combined_text = f"{raw_title_block_text}\n{title_context}\n{text}"
    prefix = sheet_prefix(sheet_number)
    matched_keywords = matched_index_keywords(combined_text)

    if is_index_page or COVER_OR_INDEX_TITLE_RE.search(title_context) or STRONG_INDEX_PAGE_RE.search(text):
        return CATEGORY_COVER_INDEX, 0.94, "Page is a cover/drawing index page.", False, ["sheet index"]

    if detected_discipline(sheet_number, drawing_set) != "vendor_detail" and has_kitchen_evidence(
        combined_text,
        sheet_number,
        drawing_set,
    ):
        return confidence_or_review(
            CATEGORY_KITCHEN,
            0.91 if matched_index or re.search(r"\bkitchen\b|\bfood\s*service\b|\bfoodservice\b", title_context, re.IGNORECASE) else 0.80,
            "Kitchen/food-service sheet detected from title block, index, or equipment/hood/grease evidence.",
        ) + (matched_keywords,)

    trade_category = discipline_category(sheet_number, drawing_set)
    if trade_category is not None:
        return confidence_or_review(
            trade_category,
            0.90 if matched_index or sheet_number else 0.78,
            f"Sheet prefix/drawing set identifies {category_slug(trade_category)} ({prefix or drawing_set}).",
        ) + (matched_keywords,)

    if has_wind_pressure_evidence(title_context) or (
        is_structural_context(sheet_number, drawing_set) and has_wind_pressure_evidence(combined_text)
    ):
        return confidence_or_review(
            CATEGORY_STRUCTURAL_WIND,
            0.92 if matched_index or has_wind_pressure_evidence(title_context) else 0.80,
            "Title block/index or content identifies wind pressure, C&C, opening pressure, zone, PSF, or tributary area information.",
        ) + (matched_keywords,)

    if is_structural_context(sheet_number, drawing_set):
        return confidence_or_review(
            CATEGORY_STRUCTURAL,
            0.90 if matched_index or sheet_number else 0.78,
            "Sheet prefix or drawing index identifies a structural sheet.",
        ) + (matched_keywords,)

    floor_context = is_architectural_context(sheet_number, drawing_set) or is_floor_reference_context(drawing_set)
    excluded_plan = bool(
        re.search(r"\b(reflected\s+ceiling|RCP|roof|fixture|life\s+safety|ceiling|power|lighting|plumbing|mechanical)\b", title, re.IGNORECASE)
    )
    floor_title = bool(
        re.search(
            r"\b(floor\s+plans?|ground\s+plans?|ground\s+floor|partial\s+floor\s+plans?|overall\s+floor\s+plans?|architectural\s+plans?)\b",
            title,
            re.IGNORECASE,
        )
    ) or (floor_context and title_has_floor_level(title) and not excluded_plan)
    if matched_index and floor_context and floor_title and not excluded_plan:
        floor_category = (
            CATEGORY_PARTIAL_FLOOR_PLANS
            if re.search(r"\b(partial|area|sector|zone|part|portion)\b", title, re.IGNORECASE)
            else CATEGORY_FLOOR_PLANS
        )
        return confidence_or_review(
            floor_category,
            0.92,
            "Drawing index/title block identifies a ground, floor, partial, overall, or architectural plan.",
        ) + (matched_keywords,)

    if matched_index and not title_has_schedule(title) and title_has_opening_elevation(title):
        return confidence_or_review(
            CATEGORY_EXTERIOR_ELEVATIONS,
            0.88,
            "Drawing index/title block identifies storefront/door/window/glazing elevations, types, or details; routed into Exterior Elevations.",
        ) + (matched_keywords,)

    if matched_index and not title_has_schedule(title) and title_has_exterior_elevation(title):
        return confidence_or_review(
            CATEGORY_EXTERIOR_ELEVATIONS,
            0.90,
            "Drawing index/title block identifies exterior/building/front/rear/side elevations.",
        ) + (matched_keywords,)

    title_says_schedule = title_has_schedule(title)
    door_table = has_schedule_table(combined_text, words, "door")
    window_table = has_schedule_table(combined_text, words, "window")
    storefront_table = has_schedule_table(combined_text, words, "storefront")
    storefront_system_table = storefront_table and has_storefront_system_signal(combined_text)

    if door_table and (
        re.search(r"\bdoors?|openings?|frames?|hardware\b", title, re.IGNORECASE)
        or not title_says_schedule
    ):
        return confidence_or_review(
            CATEGORY_DOOR_SCHEDULES,
            0.91 if title_says_schedule else 0.78,
            "Door schedule detected from sheet title or schedule-table columns.",
        ) + (matched_keywords,)

    if storefront_table and (
        re.search(r"\bstore\s*front|storefront|curtain\s+wall\b", title, re.IGNORECASE)
        or (storefront_system_table and re.search(r"\bglaz(?:ing|ed)|glass\b", title, re.IGNORECASE))
        or not title_says_schedule
    ):
        return confidence_or_review(
            CATEGORY_STOREFRONT_SCHEDULES,
            0.91 if title_says_schedule else 0.78,
            "Storefront/curtain-wall schedule detected from sheet title or storefront system table columns.",
        ) + (matched_keywords,)

    if window_table and not storefront_system_table and (
        re.search(r"\bwindows?|glaz(?:ing|ed)|glass\b", title, re.IGNORECASE)
        or not title_says_schedule
    ):
        return confidence_or_review(
            CATEGORY_WINDOW_SCHEDULES,
            0.91 if title_says_schedule else 0.78,
            "Window/glazing schedule detected from sheet title or schedule-table columns.",
        ) + (matched_keywords,)

    if title_has_opening_elevation(title):
        return confidence_or_review(
            CATEGORY_EXTERIOR_ELEVATIONS,
            0.88 if matched_index or sheet_number else 0.77,
            "Sheet title identifies storefront/door/window/glazing elevations, types, or details; routed into Exterior Elevations.",
        ) + (matched_keywords,)

    if title_has_exterior_elevation(title):
        return confidence_or_review(
            CATEGORY_EXTERIOR_ELEVATIONS,
            0.90 if matched_index or sheet_number else 0.78,
            "Sheet title identifies exterior/building/front/rear/side elevations.",
        ) + (matched_keywords,)

    floor_context = is_architectural_context(sheet_number, drawing_set) or is_floor_reference_context(drawing_set)
    excluded_plan = bool(
        re.search(r"\b(reflected\s+ceiling|RCP|roof|fixture|life\s+safety|ceiling|power|lighting|plumbing|mechanical)\b", title, re.IGNORECASE)
    )
    floor_title = bool(
        re.search(
            r"\b(floor\s+plans?|ground\s+plans?|ground\s+floor|partial\s+floor\s+plans?|overall\s+floor\s+plans?|architectural\s+plans?)\b",
            title,
            re.IGNORECASE,
        )
    ) or (floor_context and title_has_floor_level(title) and not excluded_plan)
    if floor_context and floor_title and not excluded_plan:
        floor_category = (
            CATEGORY_PARTIAL_FLOOR_PLANS
            if re.search(r"\b(partial|area|sector|zone|part|portion)\b", title, re.IGNORECASE)
            else CATEGORY_FLOOR_PLANS
        )
        return confidence_or_review(
            floor_category,
            0.92 if matched_index or "plan" in title.lower() else 0.82,
            "Architectural/reference sheet title block identifies a ground, floor, partial, overall, or architectural plan.",
        ) + (matched_keywords,)

    if re.search(r"\b(vendor|shop\s+drawing|details?|sections?)\b", title, re.IGNORECASE):
        return confidence_or_review(
            CATEGORY_VENDOR_DETAIL,
            0.80 if sheet_number or matched_index else 0.72,
            "Sheet title identifies a detail, section, vendor, or shop drawing sheet.",
        ) + (matched_keywords,)

    return confidence_or_review(
        CATEGORY_REVIEW,
        0.40 if not sheet_number and not title else 0.62,
        "No high-confidence title-block/index classification rule matched.",
    ) + (matched_keywords,)


def group_words_into_rows(words: list[tuple]) -> list[list[tuple]]:
    rows: list[list[tuple]] = []
    current_row: list[tuple] = []
    current_y: float | None = None
    tolerance = 4.0

    for word in sorted(words, key=lambda item: (item[1], item[0])):
        y0 = float(word[1])
        if current_y is None or abs(y0 - current_y) <= tolerance:
            current_row.append(word)
            current_y = y0 if current_y is None else (current_y * 0.8) + (y0 * 0.2)
        else:
            rows.append(sorted(current_row, key=lambda item: item[0]))
            current_row = [word]
            current_y = y0

    if current_row:
        rows.append(sorted(current_row, key=lambda item: item[0]))

    return rows


def sheet_number_from_word(word_text: str) -> str:
    cleaned = word_text.strip(".,;:()[]{}")
    if not SHEET_NUMBER_RE.fullmatch(cleaned):
        return ""
    candidate = normalize_sheet_number(cleaned)
    return "" if is_bad_sheet_candidate(candidate) else candidate


def is_false_sheet_token(row: list[tuple], token_index: int, sheet_number: str) -> bool:
    previous_word = row[token_index - 1][4].strip(".,;:()[]{}").upper() if token_index > 0 else ""
    if previous_word in {"UNIT", "TYPE", "MODEL", "APT", "APARTMENT"}:
        return True
    if sheet_prefix(sheet_number) in {"R", "P"} and len(sheet_number) <= 4:
        return True
    return False


def column_bin(x_position: float) -> int:
    return int(round(x_position / 25.0) * 25)


def parse_sheet_index_entries_from_words(words: list[tuple], source_page_number: int) -> dict[str, SheetIndexEntry]:
    rows = group_words_into_rows(words)
    row_candidates: list[list[tuple[int, str, int]]] = []
    column_counts: dict[int, int] = {}

    for row in rows:
        candidates: list[tuple[int, str, int]] = []
        for token_index, word in enumerate(row):
            sheet_number = sheet_number_from_word(str(word[4]))
            if not sheet_number or is_false_sheet_token(row, token_index, sheet_number):
                continue
            bin_value = column_bin(float(word[0]))
            candidates.append((token_index, sheet_number, bin_value))
            column_counts[bin_value] = column_counts.get(bin_value, 0) + 1
        row_candidates.append(candidates)

    if not column_counts:
        return {}

    minimum_count = 2 if len(rows) < 20 else 3
    allowed_columns = {
        bin_value
        for bin_value, count in column_counts.items()
        if count >= minimum_count
    }
    if not allowed_columns:
        allowed_columns = {
            bin_value
            for bin_value, _count in sorted(column_counts.items(), key=lambda item: item[1], reverse=True)[:4]
        }

    entries: dict[str, SheetIndexEntry] = {}
    drawing_set_by_column: dict[int, str] = {}
    current_drawing_set = ""
    for row_index, row in enumerate(rows):
        candidates = [
            candidate
            for candidate in row_candidates[row_index]
            if candidate[2] in allowed_columns
        ]
        for chunk_x, chunk_text in row_text_chunks(row):
            drawing_set = clean_drawing_set_header(chunk_text)
            if drawing_set:
                column = nearest_allowed_column(column_bin(chunk_x), allowed_columns)
                drawing_set_by_column[column] = drawing_set
                current_drawing_set = drawing_set

        if not candidates:
            continue

        candidate_token_indexes = [candidate[0] for candidate in candidates]
        for candidate_position, (token_index, sheet_number, _bin_value) in enumerate(candidates):
            next_token_index = (
                candidate_token_indexes[candidate_position + 1]
                if candidate_position + 1 < len(candidate_token_indexes)
                else len(row)
            )
            title_words = [str(word[4]) for word in row[token_index + 1 : next_token_index]]
            title_text = " ".join(title_words)

            if not is_useful_index_title(clean_index_title(title_text)):
                continuation_words: list[str] = []
                candidate_x = float(row[token_index][0])
                next_x = float(row[next_token_index][0]) if next_token_index < len(row) else float("inf")
                for next_row in rows[row_index + 1 : row_index + 4]:
                    continued = [
                        str(word[4])
                        for word in next_row
                        if float(word[0]) > candidate_x + 15 and float(word[0]) < next_x - 10
                    ]
                    if not continued:
                        continue
                    if any(sheet_number_from_word(word) for word in continued):
                        break
                    continuation_title = clean_index_title(" ".join(continued))
                    if is_useful_index_title(continuation_title):
                        continuation_words.extend(continued)
                        break
                if continuation_words:
                    title_text = " ".join(continuation_words)

            title = clean_index_title(title_text)
            if not is_useful_index_title(title):
                continue

            confidence = 14
            if TITLE_KEYWORD_RE.search(title):
                confidence += 8
            if float(row[token_index][0]) <= 250:
                confidence += 4
            if uppercase_ratio(title) >= 0.5:
                confidence += 3

            column = nearest_allowed_column(_bin_value, allowed_columns)
            drawing_set = drawing_set_by_column.get(column, current_drawing_set)
            if drawing_set:
                confidence += 4

            key = sheet_lookup_key(sheet_number)
            existing = entries.get(key)
            if existing is None or confidence > existing.confidence or (
                confidence == existing.confidence and drawing_set and not existing.drawing_set
            ):
                entries[key] = SheetIndexEntry(
                    sheet_number=sheet_number,
                    sheet_title=title,
                    drawing_set=drawing_set,
                    source_page_number=source_page_number,
                    confidence=confidence,
                )

    return entries


def parse_sheet_index_entries(lines: list[str], source_page_number: int) -> dict[str, SheetIndexEntry]:
    entries: dict[str, SheetIndexEntry] = {}
    current_drawing_set = ""

    for index, line in enumerate(lines):
        line_drawing_set = clean_drawing_set_header(line)
        matches = [
            match
            for match in SHEET_NUMBER_RE.finditer(line)
            if not is_bad_sheet_candidate(normalize_sheet_number(match.group(0)))
        ]
        if not matches:
            if line_drawing_set:
                current_drawing_set = line_drawing_set
            continue

        for match_index, match in enumerate(matches):
            sheet_number = normalize_sheet_number(match.group(0))
            if not sheet_lookup_key(sheet_number):
                continue
            prefix_text = line[: match.start()].strip()
            if match.start() > 12 and not re.search(r"\b(sheet|drawing)\b", prefix_text, re.IGNORECASE):
                continue

            next_start = matches[match_index + 1].start() if match_index + 1 < len(matches) else len(line)
            title_text = line[match.end() : next_start]

            if (not title_text.strip() or not is_useful_index_title(clean_index_title(title_text))) and match.start() <= 12:
                continuation_lines: list[str] = []
                for next_line in lines[index + 1 : index + 4]:
                    if SHEET_NUMBER_RE.fullmatch(next_line.strip()):
                        continue
                    if SHEET_NUMBER_RE.search(next_line):
                        break
                    cleaned_next = clean_index_title(next_line)
                    if not is_useful_index_title(cleaned_next):
                        continue
                    continuation_lines.append(cleaned_next)
                    if TITLE_KEYWORD_RE.search(cleaned_next):
                        break
                if continuation_lines:
                    title_text = " ".join(continuation_lines)

            title = clean_index_title(title_text)
            if not is_useful_index_title(title):
                continue

            confidence = 10
            if INDEX_PAGE_RE.search(line):
                confidence += 10
            if TITLE_KEYWORD_RE.search(title):
                confidence += 8
            if match.start() <= 8:
                confidence += 8
            if uppercase_ratio(title) >= 0.5:
                confidence += 3
            if current_drawing_set:
                confidence += 4

            key = sheet_lookup_key(sheet_number)
            existing = entries.get(key)
            if existing is None or confidence > existing.confidence or (
                confidence == existing.confidence and current_drawing_set and not existing.drawing_set
            ):
                entries[key] = SheetIndexEntry(
                    sheet_number=sheet_number,
                    sheet_title=title,
                    drawing_set=current_drawing_set,
                    source_page_number=source_page_number,
                    confidence=confidence,
                )

    return entries


def looks_like_index_page(lines: list[str], page_index: int, page_count: int, entry_count: int) -> bool:
    text = "\n".join(lines)
    has_index_words = bool(STRONG_INDEX_PAGE_RE.search(text))
    early_page = page_index < min(12, max(4, page_count // 8 + 1))

    if has_index_words and entry_count >= 1:
        return True
    if entry_count >= 8 and early_page:
        return True
    return False


def build_sheet_index(
    page_lines: list[list[str]],
    page_words: list[list[tuple]],
    status_callback: StatusCallback | None = None,
) -> tuple[dict[str, SheetIndexEntry], set[int]]:
    combined: dict[str, SheetIndexEntry] = {}
    index_page_indexes: set[int] = set()
    page_count = len(page_lines)
    parsed_by_page: list[dict[str, SheetIndexEntry]] = []

    scan_limit = min(5, page_count)
    for page_index, lines in enumerate(page_lines[:scan_limit]):
        word_entries = parse_sheet_index_entries_from_words(page_words[page_index], page_index + 1)
        line_entries = parse_sheet_index_entries(lines, page_index + 1)
        entries = word_entries if word_entries else line_entries
        parsed_by_page.append(entries)

    first_strong_index_page: int | None = None
    for page_index, lines in enumerate(page_lines[:scan_limit]):
        if STRONG_INDEX_PAGE_RE.search("\n".join(lines)) and parsed_by_page[page_index]:
            first_strong_index_page = page_index
            break

    pages_to_use: set[int] = set()
    if first_strong_index_page is not None:
        for page_index in range(first_strong_index_page, scan_limit):
            entries = parsed_by_page[page_index]
            explicit_index = bool(STRONG_INDEX_PAGE_RE.search("\n".join(page_lines[page_index])))
            if entries and (explicit_index or len(entries) >= 6):
                pages_to_use.add(page_index)
                continue
            if pages_to_use:
                break

    for page_index, lines in enumerate(page_lines[:scan_limit]):
        explicit_index = bool(STRONG_INDEX_PAGE_RE.search("\n".join(lines)))
        if explicit_index and parsed_by_page[page_index]:
            pages_to_use.add(page_index)

    if not pages_to_use:
        for page_index, entries in enumerate(parsed_by_page):
            if len(entries) >= 8:
                pages_to_use.add(page_index)

    for page_index in sorted(pages_to_use):
        entries = parsed_by_page[page_index]
        lines = page_lines[page_index]
        if not looks_like_index_page(lines, page_index, page_count, len(entries)):
            continue

        index_page_indexes.add(page_index)
        for key, entry in entries.items():
            existing = combined.get(key)
            if existing is None or entry.confidence > existing.confidence or (
                entry.confidence == existing.confidence and entry.drawing_set and not existing.drawing_set
            ):
                combined[key] = entry

    if status_callback is not None:
        status_callback(
            f"Found {len(combined)} sheet-index entries on {len(index_page_indexes)} cover/index page(s)."
        )

    return combined, index_page_indexes


def matched_index_keywords(text: str) -> list[str]:
    matches: list[str] = []
    for label, pattern in INDEX_KEYWORD_PATTERNS:
        if re.search(pattern, text, flags=re.IGNORECASE):
            matches.append(label)
    return matches


def count_pattern(pattern: str, text: str) -> int:
    return len(re.findall(pattern, text, flags=re.IGNORECASE))


def score_categories(
    text: str,
    title: str,
    sheet_number: str,
    drawing_set: str = "",
) -> tuple[dict[str, int], dict[str, int]]:
    title_context = f"{drawing_set}\n{title}".strip()
    search_text = f"{drawing_set}\n{title}\n{text}".strip()
    title_scores = {category: 0 for category in CATEGORY_RULES}
    full_scores = {category: 0 for category in CATEGORY_RULES}

    for category, rules in CATEGORY_RULES.items():
        for _label, pattern, weight in rules:
            title_hits = count_pattern(pattern, title_context)
            full_hits = count_pattern(pattern, search_text)
            if title_hits:
                title_scores[category] += weight * min(title_hits, 3) * 3
            if full_hits:
                full_scores[category] += weight * min(full_hits, 3)

    prefix = sheet_prefix(sheet_number)
    title_has_partial = bool(re.search(r"\b(partial|area|sector|zone|part|portion)\b", title, flags=re.IGNORECASE))
    title_has_overall = bool(re.search(r"\boverall\b", title, flags=re.IGNORECASE))
    title_floor_like = title_is_floor_plan_like(title)
    floor_context = is_architectural_context(sheet_number, drawing_set) or is_floor_reference_context(drawing_set)

    if is_structural_context(sheet_number, drawing_set):
        full_scores[CATEGORY_STRUCTURAL] += 10
        title_scores[CATEGORY_STRUCTURAL] += 10
    if floor_context and title_floor_like and title_has_partial:
        full_scores[CATEGORY_PARTIAL_FLOOR_PLANS] += 10
        title_scores[CATEGORY_PARTIAL_FLOOR_PLANS] += 10
    elif floor_context and title_floor_like:
        full_scores[CATEGORY_FLOOR_PLANS] += 8
        title_scores[CATEGORY_FLOOR_PLANS] += 8
    if title_has_overall:
        full_scores[CATEGORY_FLOOR_PLANS] += 6
        title_scores[CATEGORY_FLOOR_PLANS] += 6
    if prefix.startswith(("G", "CS")) and COVER_OR_INDEX_TITLE_RE.search(title):
        full_scores[CATEGORY_OTHER] = 999

    return title_scores, full_scores


def page_evidence_and_candidates(
    selected_category: str,
    selected_confidence: float,
    text: str,
    words: list[tuple],
    sheet_number: str,
    sheet_title: str,
    drawing_set: str,
    matched_index: bool,
    raw_title_block_text: str,
    regions: list[RegionRecord],
    neighbor_score: float = 0.0,
) -> tuple[dict[str, float], list[dict[str, object]], float]:
    title_scores, full_scores = score_categories(text, sheet_title, sheet_number, drawing_set)
    candidate_scores = {category: 0.0 for category in CATEGORY_ORDER}
    candidate_scores[selected_category] = max(candidate_scores.get(selected_category, 0.0), selected_confidence)

    title_block_score = 0.0
    if sheet_number:
        title_block_score += 0.42
    if sheet_title:
        title_block_score += 0.33
    if raw_title_block_text:
        title_block_score += 0.15
    title_block_score = clamp_score(title_block_score)

    index_match_score = 1.0 if matched_index else 0.0
    keyword_score = 0.0
    for category in CATEGORY_ORDER:
        raw_keyword_score = title_scores.get(category, 0) + full_scores.get(category, 0)
        normalized_keyword_score = min(0.82, raw_keyword_score / 110.0)
        if normalized_keyword_score:
            candidate_scores[category] = max(candidate_scores.get(category, 0.0), normalized_keyword_score)
            keyword_score = max(keyword_score, normalized_keyword_score)

    table_structure_score = min(1.0, table_like_row_count(words) / 6.0)
    visual_layout_score = 0.0
    mark_pattern_score = 0.0

    region_category_map = {
        REGION_DOOR_SCHEDULE: CATEGORY_DOOR_SCHEDULES,
        REGION_HARDWARE_SCHEDULE: CATEGORY_DOOR_SCHEDULES,
        REGION_WINDOW_SCHEDULE: CATEGORY_WINDOW_SCHEDULES,
        REGION_GLAZING_SCHEDULE: CATEGORY_WINDOW_SCHEDULES,
        REGION_STOREFRONT_SCHEDULE: CATEGORY_STOREFRONT_SCHEDULES,
        REGION_EXTERIOR_ELEVATION: CATEGORY_EXTERIOR_ELEVATIONS,
        REGION_STOREFRONT_ELEVATION: CATEGORY_EXTERIOR_ELEVATIONS,
        REGION_VENDOR_DETAIL: CATEGORY_VENDOR_DETAIL,
    }
    for region in regions:
        table_structure_score = max(table_structure_score, region.evidence_scores.get("table_structure_score", 0.0))
        mark_pattern_score = max(mark_pattern_score, region.evidence_scores.get("mark_pattern_score", 0.0))
        visual_layout_score = max(visual_layout_score, region.evidence_scores.get("visual_layout_score", 0.0))
        mapped_category = region_category_map.get(region.region_category)
        if mapped_category is not None:
            candidate_scores[mapped_category] = max(candidate_scores.get(mapped_category, 0.0), region.confidence)

    discipline_category_value = discipline_category(sheet_number, drawing_set)
    if discipline_category_value is not None:
        candidate_scores[discipline_category_value] = max(
            candidate_scores.get(discipline_category_value, 0.0),
            0.78 if not matched_index else 0.90,
        )
    if is_structural_context(sheet_number, drawing_set):
        candidate_scores[CATEGORY_STRUCTURAL] = max(candidate_scores.get(CATEGORY_STRUCTURAL, 0.0), 0.78)
    if has_wind_pressure_evidence(f"{sheet_title}\n{text}"):
        candidate_scores[CATEGORY_STRUCTURAL_WIND] = max(candidate_scores.get(CATEGORY_STRUCTURAL_WIND, 0.0), 0.80)
    if has_kitchen_evidence(f"{sheet_title}\n{text}", sheet_number, drawing_set):
        candidate_scores[CATEGORY_KITCHEN] = max(candidate_scores.get(CATEGORY_KITCHEN, 0.0), 0.80)

    selected_score = max(candidate_scores.get(selected_category, 0.0), selected_confidence)
    candidate_scores[selected_category] = selected_score
    sorted_candidates = sorted(
        [candidate(category, score) for category, score in candidate_scores.items() if score > 0.0],
        key=lambda item: float(item["score"]),
        reverse=True,
    )
    if not sorted_candidates:
        sorted_candidates = [candidate(CATEGORY_REVIEW, selected_confidence)]

    evidence = {
        "title_block_score": round(title_block_score, 2),
        "index_match_score": round(index_match_score, 2),
        "keyword_score": round(keyword_score, 2),
        "table_structure_score": round(table_structure_score, 2),
        "mark_pattern_score": round(mark_pattern_score, 2),
        "visual_layout_score": round(visual_layout_score, 2),
        "neighbor_score": round(clamp_score(neighbor_score), 2),
        "combined_score": round(clamp_score(selected_score), 2),
    }
    return evidence, sorted_candidates[:3], clamp_score(selected_score)


def choose_best_category(scores: dict[str, int]) -> str:
    best_category = CATEGORY_OTHER
    best_score = 0
    for category in CATEGORY_ORDER:
        if category == CATEGORY_OTHER:
            continue
        score = scores.get(category, 0)
        if score > best_score:
            best_category = category
            best_score = score
    return best_category if best_score > 0 else CATEGORY_OTHER


def has_significant_score(scores: dict[str, int], category: str, minimum: int) -> bool:
    return scores.get(category, 0) >= minimum


def has_wind_pressure_context(text: str) -> bool:
    if re.search(r"\bwind\s+pressures?\b|\bdesign\s+pressures?\b", text, re.IGNORECASE):
        return True
    if re.search(r"\bcomponents?\s+(?:and|&)\s+cladding\b|\bC\s*&\s*C\b|\bC\s*/\s*C\b", text, re.IGNORECASE):
        return True
    has_psf = bool(re.search(r"\bpsf\b|\bp\.?\s*s\.?\s*f\.?\b", text, re.IGNORECASE))
    has_pressure_word = bool(re.search(r"\bpressure(?:s)?\b|\bpositive\b|\bnegative\b", text, re.IGNORECASE))
    has_opening_context = bool(
        re.search(r"\bwindows?|doors?|openings?|glaz(?:ing|ed)|storefront|elevations?|facades?\b", text, re.IGNORECASE)
    )
    return has_psf and (has_pressure_word or has_opening_context)


def append_unique(values: list[str], value: str) -> None:
    if value not in values:
        values.append(value)


def classify_page(text: str, title: str, sheet_number: str, drawing_set: str = "") -> list[str]:
    category, _confidence, _reason, _needs_review, _keywords = classify_metadata_first(
        text=text,
        words=[],
        sheet_number=sheet_number,
        sheet_title=title,
        drawing_set=drawing_set,
        is_index_page=False,
        matched_index=bool(drawing_set),
        raw_title_block_text="",
    )
    return [category]


def display_categories(category_files: Iterable[str]) -> str:
    return "; ".join(category_files)


def sheet_sequence_value(sheet_number: str) -> float | None:
    match = re.search(r"(\d+(?:\.\d+)?)", normalize_sheet_number(sheet_number))
    if not match:
        return None
    try:
        return float(match.group(1))
    except ValueError:
        return None


def sheet_numeric_parts(sheet_number: str) -> tuple[int, int | None] | None:
    match = re.search(r"(\d+)(?:\.(\d+))?", normalize_sheet_number(sheet_number))
    if not match:
        return None
    major = int(match.group(1))
    minor = int(match.group(2)) if match.group(2) is not None else None
    return major, minor


def title_similarity(left: str, right: str) -> float:
    def tokens(value: str) -> set[str]:
        return {
            token.lower()
            for token in re.findall(r"[A-Za-z0-9]+", value)
            if token.lower() not in {"sheet", "plan", "plans", "the", "and"}
        }

    left_tokens = tokens(left)
    right_tokens = tokens(right)
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)


def is_continuation_title(title: str) -> bool:
    return bool(re.search(r"\b(continued|continuation|cont\.?)\b", title, re.IGNORECASE))


def same_or_adjacent_sheet(left: str, right: str) -> bool:
    if sheet_prefix(left) != sheet_prefix(right):
        return False
    left_parts = sheet_numeric_parts(left)
    right_parts = sheet_numeric_parts(right)
    if left_parts is None or right_parts is None:
        return False
    left_major, left_minor = left_parts
    right_major, right_minor = right_parts
    if left_minor is not None or right_minor is not None:
        if left_major != right_major or left_minor is None or right_minor is None:
            return False
        return abs(left_minor - right_minor) <= 2
    return abs(left_major - right_major) <= 1


def should_continue_category(anchor: PageRecord, candidate: PageRecord) -> bool:
    if not anchor.category_files:
        return False
    category = anchor.category_files[0]
    if category not in {
        CATEGORY_FLOOR_PLANS,
        CATEGORY_PARTIAL_FLOOR_PLANS,
        CATEGORY_WINDOW_SCHEDULES,
        CATEGORY_STOREFRONT_SCHEDULES,
        CATEGORY_DOOR_SCHEDULES,
        CATEGORY_STRUCTURAL_WIND,
    }:
        return False
    if not candidate.category_files or candidate.category_files[0] not in {CATEGORY_REVIEW, CATEGORY_STRUCTURAL}:
        return False
    if is_other_discipline_context(candidate.sheet_number, candidate.drawing_set) and category != CATEGORY_STRUCTURAL_WIND:
        return False
    if is_continuation_title(candidate.sheet_title):
        return True
    if title_similarity(anchor.sheet_title, candidate.sheet_title) >= 0.55 and same_or_adjacent_sheet(
        anchor.sheet_number, candidate.sheet_number
    ):
        return True
    if category == CATEGORY_STRUCTURAL_WIND and sheet_prefix(candidate.sheet_number).startswith("S"):
        return bool(
            re.search(
                r"\b(wind|pressure|psf|zone|opening|elevation|diagram|continued|cont\.?)\b",
                candidate.sheet_title + "\n" + candidate.raw_title_block_text,
                re.IGNORECASE,
            )
        ) or same_or_adjacent_sheet(anchor.sheet_number, candidate.sheet_number)
    return False


def apply_neighbor_continuations(records: list[PageRecord]) -> list[PageRecord]:
    updated = list(records)
    anchors = [
        record
        for record in records
        if record.category_files
        and record.category_files[0]
        in {
            CATEGORY_FLOOR_PLANS,
            CATEGORY_PARTIAL_FLOOR_PLANS,
            CATEGORY_WINDOW_SCHEDULES,
            CATEGORY_STOREFRONT_SCHEDULES,
            CATEGORY_DOOR_SCHEDULES,
            CATEGORY_STRUCTURAL_WIND,
        }
        and record.confidence >= 0.80
    ]

    for anchor in anchors:
        category = anchor.category_files[0]
        for offset in range(-2, 3):
            if offset == 0:
                continue
            neighbor_index = anchor.page_index + offset
            if neighbor_index < 0 or neighbor_index >= len(updated):
                continue
            candidate = updated[neighbor_index]
            if not should_continue_category(anchor, candidate):
                continue
            confidence = max(candidate.confidence, 0.80)
            evidence_scores = dict(candidate.evidence_scores)
            evidence_scores["neighbor_score"] = max(evidence_scores.get("neighbor_score", 0.0), 0.80)
            evidence_scores["combined_score"] = round(confidence, 2)
            top_candidates = [
                {"category": category_slug(category), "score": round(confidence, 2)},
                *[
                    item
                    for item in candidate.top_candidates
                    if item.get("category") != category_slug(category)
                ],
            ][:3]
            updated[neighbor_index] = replace(
                candidate,
                category_files=[category],
                confidence=confidence,
                needs_manual_review=confidence < MANUAL_REVIEW_THRESHOLD,
                reason=(
                    f"Neighbor continuation from {anchor.sheet_number or 'nearby sheet'}: "
                    f"{anchor.reason}"
                ),
                evidence_scores=evidence_scores,
                top_candidates=top_candidates,
            )
    return updated


def safe_folder_name(name: str) -> str:
    cleaned = re.sub(r"[<>:\"/\\|?*]+", "_", name).strip().strip(".")
    return cleaned or "split_plan_set"


def make_output_dir(pdf_path: Path) -> Path:
    base_name = safe_folder_name(pdf_path.stem)
    output_dir = pdf_path.with_name(base_name)
    if not output_dir.exists():
        output_dir.mkdir(parents=True)
        return output_dir

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = pdf_path.with_name(f"{base_name}_{stamp}")
    output_dir.mkdir(parents=True)
    return output_dir


def debug_relative_path(path: Path, debug_dir: Path) -> str:
    try:
        return str(path.relative_to(debug_dir.parent)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def ratio_rect(page_rect: "fitz.Rect", left: float, top: float, right: float, bottom: float) -> "fitz.Rect":
    return fitz.Rect(
        page_rect.x0 + page_rect.width * left,
        page_rect.y0 + page_rect.height * top,
        page_rect.x0 + page_rect.width * right,
        page_rect.y0 + page_rect.height * bottom,
    )


def safe_debug_name(value: str, fallback: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "_", value.strip())
    return cleaned.strip("_") or fallback


def render_debug_png(page: "fitz.Page", path: Path, clip: "fitz.Rect | None" = None, dpi: int = DEBUG_THUMBNAIL_DPI) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    zoom = dpi / 72.0
    pixmap = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), clip=clip, alpha=False)
    pixmap.save(path)
    pixmap = None


def write_text_file(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def debug_title_block_zones(page_rect: "fitz.Rect") -> list[tuple[str, "fitz.Rect"]]:
    return [
        ("right_vertical_strip", ratio_rect(page_rect, 0.72, 0.00, 1.00, 1.00)),
        ("bottom_right_corner", ratio_rect(page_rect, 0.52, 0.58, 1.00, 1.00)),
        ("bottom_title_strip", ratio_rect(page_rect, 0.00, 0.76, 1.00, 1.00)),
        ("top_right_fallback", ratio_rect(page_rect, 0.58, 0.00, 1.00, 0.28)),
    ]


def write_page_debug_artifacts(
    page: "fitz.Page",
    page_number: int,
    text: str,
    raw_title_block_text: str,
    regions: list[RegionRecord],
    debug_dir: Path | None,
    high_detail: bool,
) -> dict[str, list[str]]:
    if debug_dir is None:
        return {}

    page_label = f"page_{page_number:04d}"
    page_dir = debug_dir / page_label
    page_dir.mkdir(parents=True, exist_ok=True)
    debug_files: dict[str, list[str]] = {"thumbnails": [], "title_block_crops": [], "table_crops": [], "ocr_text": []}

    try:
        thumb_path = page_dir / f"{page_label}_thumbnail.png"
        render_debug_png(page, thumb_path, dpi=DEBUG_THUMBNAIL_DPI)
        debug_files["thumbnails"].append(debug_relative_path(thumb_path, debug_dir))
    except Exception:
        pass

    crop_dpi = DEBUG_SMALL_PLAN_DPI if high_detail else DEBUG_LARGE_PLAN_DPI
    for zone_name, clip in debug_title_block_zones(page.rect):
        try:
            crop_path = page_dir / f"{page_label}_title_{zone_name}.png"
            render_debug_png(page, crop_path, clip=clip, dpi=crop_dpi)
            debug_files["title_block_crops"].append(debug_relative_path(crop_path, debug_dir))
        except Exception:
            continue

    ocr_text_path = page_dir / f"{page_label}_ocr_text.txt"
    write_text_file(
        ocr_text_path,
        "\n\n".join(
            [
                "[native_pdf_text]",
                text or "",
                "[title_block_crop_text]",
                raw_title_block_text or "",
                "[ocr_strategy]",
                "Accuracy Mode v2 uses native PDF text, title-block crop text, table-region text, and high-DPI debug crops. "
                "External OCR is optional and not required for text PDFs.",
            ]
        ),
    )
    debug_files["ocr_text"].append(debug_relative_path(ocr_text_path, debug_dir))

    for region in regions:
        if not region.region_bbox:
            continue
        try:
            x0, y0, x1, y1 = region.region_bbox
            clip = fitz.Rect(x0, y0, x1, y1) & page.rect
            if clip.is_empty or clip.width < 4 or clip.height < 4:
                continue
            region_id = safe_debug_name(region.region_id, f"R{len(debug_files['table_crops']) + 1}")
            crop_path = page_dir / f"{page_label}_{region_id}_{region.region_category}.png"
            render_debug_png(page, crop_path, clip=clip, dpi=crop_dpi)
            debug_files["table_crops"].append(debug_relative_path(crop_path, debug_dir))
            text_path = page_dir / f"{page_label}_{region_id}_{region.region_category}.txt"
            write_text_file(text_path, region.raw_text)
            debug_files["ocr_text"].append(debug_relative_path(text_path, debug_dir))
        except Exception:
            continue

    return {key: value for key, value in debug_files.items() if value}


def write_placeholder_pdf(path: Path, category_label: str) -> None:
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)
    message = (
        f"No original pages were assigned to:\n\n{category_label}\n\n"
        "This placeholder exists so every requested output PDF is present."
    )
    page.insert_textbox(
        fitz.Rect(72, 72, 540, 300),
        message,
        fontsize=14,
        fontname="helv",
        align=0,
    )
    doc.save(path, garbage=1, deflate=True)
    doc.close()


def raster_fallback_zoom(rect: "fitz.Rect") -> float:
    page_pixels_at_72dpi = max(rect.width * rect.height, 1)
    zoom = math.sqrt(MAX_RASTER_FALLBACK_PIXELS / page_pixels_at_72dpi)
    return max(0.25, min(1.0, zoom))


def delete_pages_added_after(out_doc: "fitz.Document", page_count_before: int) -> None:
    while out_doc.page_count > page_count_before:
        out_doc.delete_page(out_doc.page_count - 1)


def add_failed_page_placeholder(
    out_doc: "fitz.Document",
    source_doc: "fitz.Document",
    page_index: int,
    error: Exception,
) -> str:
    try:
        source_page = source_doc.load_page(page_index)
        rect = source_page.rect
        width = rect.width
        height = rect.height
    except Exception:
        width = 612
        height = 792

    page = out_doc.new_page(width=width, height=height)
    message = (
        f"Page {page_index + 1} could not be copied from the source PDF.\n\n"
        "The original PDF was not modified.\n\n"
        f"Error: {error}"
    )
    page.insert_textbox(
        fitz.Rect(72, 72, max(width - 72, 300), min(height - 72, 420)),
        message,
        fontsize=12,
        fontname="helv",
        align=0,
    )
    return "placeholder"


def copy_page_to_document(source_doc: "fitz.Document", out_doc: "fitz.Document", page_index: int) -> str:
    # Copy without links, annotations, and widgets first. These objects are not
    # needed for split plan PDFs and are often what makes large marked-up sets
    # unstable.
    try:
        out_doc.insert_pdf(
            source_doc,
            from_page=page_index,
            to_page=page_index,
            links=False,
            annots=False,
            widgets=False,
        )
        return "direct"
    except Exception as direct_error:
        first_error = direct_error

    page_count_before = out_doc.page_count
    try:
        source_page = source_doc.load_page(page_index)
        rect = source_page.rect
        output_page = out_doc.new_page(width=rect.width, height=rect.height)
        output_page.show_pdf_page(output_page.rect, source_doc, page_index)
        return "vector"
    except Exception as vector_error:
        delete_pages_added_after(out_doc, page_count_before)
        second_error = vector_error

    page_count_before = out_doc.page_count
    try:
        source_page = source_doc.load_page(page_index)
        rect = source_page.rect
        zoom = raster_fallback_zoom(rect)
        pixmap = source_page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
        output_page = out_doc.new_page(width=rect.width, height=rect.height)
        output_page.insert_image(output_page.rect, pixmap=pixmap)
        pixmap = None
        return "raster"
    except Exception as raster_error:
        delete_pages_added_after(out_doc, page_count_before)
        return add_failed_page_placeholder(
            out_doc,
            source_doc,
            page_index,
            RuntimeError(f"{first_error}; {second_error}; {raster_error}"),
        )


def save_category_pdfs(
    source_doc: "fitz.Document",
    records: Iterable[PageRecord],
    output_dir: Path,
    skip_empty_pdfs: bool,
    status_callback: StatusCallback | None = None,
) -> None:
    pages_by_category = {category: [] for category in CATEGORY_ORDER}
    for record in records:
        for category_file in record.category_files:
            pages_by_category[category_file].append(record.page_index)

    for category in CATEGORY_ORDER:
        if status_callback is not None:
            status_callback(f"Writing {CATEGORY_LABELS[category]}...")

        output_path = output_dir / category
        page_indexes = pages_by_category[category]

        if not page_indexes:
            if not skip_empty_pdfs:
                write_placeholder_pdf(output_path, CATEGORY_LABELS[category])
            continue

        out_doc = fitz.open()
        last_status = 0.0
        fallback_counts = {"vector": 0, "raster": 0, "placeholder": 0}
        for copied_count, page_index in enumerate(page_indexes, start=1):
            now = time.monotonic()
            if status_callback is not None and (
                copied_count == 1
                or copied_count == len(page_indexes)
                or now - last_status >= STATUS_UPDATE_SECONDS
            ):
                status_callback(
                    f"Writing {CATEGORY_LABELS[category]} page {copied_count} of {len(page_indexes)}..."
                )
                last_status = now

            copy_method = copy_page_to_document(source_doc, out_doc, page_index)
            if copy_method in fallback_counts:
                fallback_counts[copy_method] += 1

        if status_callback is not None and any(fallback_counts.values()):
            status_callback(
                "Used safe copy fallback for "
                f"{sum(fallback_counts.values())} page(s) in {CATEGORY_LABELS[category]}."
            )

        out_doc.save(output_path, garbage=1, deflate=True)
        out_doc.close()
        gc.collect()


def write_csv_index(records: list[PageRecord], output_dir: Path) -> Path:
    csv_path = output_dir / "page_index.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=[
                "original_page_number",
                "detected_sheet_number",
                "detected_sheet_title",
                "drawing_set",
                "discipline_prefix",
                "detected_discipline",
                "confidence",
                "needs_manual_review",
                "reason",
                "matched_index",
                "matched_keywords",
                "assigned_category",
                "top_candidates",
                "evidence_scores",
                "small_plan_mode",
                "sheet_title_source",
                "index_source_page",
                "raw_title_block_text",
            ],
        )
        writer.writeheader()
        for record in records:
            writer.writerow(
                {
                    "original_page_number": record.original_page_number,
                    "detected_sheet_number": record.sheet_number,
                    "detected_sheet_title": record.sheet_title,
                    "drawing_set": record.drawing_set,
                    "discipline_prefix": record.discipline_prefix,
                    "detected_discipline": record.detected_discipline,
                    "confidence": f"{record.confidence:.2f}",
                    "needs_manual_review": "yes" if record.needs_manual_review else "no",
                    "reason": record.reason,
                    "matched_index": "yes" if record.matched_index else "no",
                    "matched_keywords": "; ".join(record.matched_keywords),
                    "assigned_category": display_categories(record.category_files),
                    "top_candidates": json.dumps(record.top_candidates),
                    "evidence_scores": json.dumps(record.evidence_scores),
                    "small_plan_mode": "yes" if record.small_plan_mode else "no",
                    "sheet_title_source": record.sheet_title_source,
                    "index_source_page": record.index_source_page or "",
                    "raw_title_block_text": record.raw_title_block_text,
                }
            )
    return csv_path


def write_sheet_index_csv(sheet_index: dict[str, SheetIndexEntry], output_dir: Path) -> Path:
    csv_path = output_dir / "extracted_sheet_index.csv"
    entries = sorted(
        sheet_index.values(),
        key=lambda entry: (entry.source_page_number, sheet_lookup_key(entry.sheet_number)),
    )

    with csv_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=[
                "index_source_page",
                "sheet_number",
                "sheet_title",
                "drawing_set",
                "predicted_categories",
                "confidence",
            ],
        )
        writer.writeheader()
        for entry in entries:
            predicted = classify_page("", entry.sheet_title, entry.sheet_number, entry.drawing_set)
            writer.writerow(
                {
                    "index_source_page": entry.source_page_number,
                    "sheet_number": entry.sheet_number,
                    "sheet_title": entry.sheet_title,
                    "drawing_set": entry.drawing_set,
                    "predicted_categories": display_categories(predicted),
                    "confidence": entry.confidence,
                }
            )

    return csv_path


def manifest_from_records(
    source_pdf: Path,
    records: list[PageRecord],
    analysis_summary: dict[str, object] | None = None,
    debug_dir: Path | None = None,
) -> dict[str, object]:
    groups = {slug: [] for slug in CATEGORY_SLUGS.values()}
    pages: list[dict[str, object]] = []
    all_regions: list[dict[str, object]] = []

    for record in records:
        category = record.category_files[0] if record.category_files else CATEGORY_REVIEW
        slug = category_slug(category)
        groups.setdefault(slug, []).append(record.original_page_number)
        page_regions: list[dict[str, object]] = []
        for region in record.regions:
            region_data = {
                "pdf_page_number": region.pdf_page_number,
                "sheet_number": region.sheet_number,
                "sheet_title": region.sheet_title,
                "region_id": region.region_id,
                "region_bbox": region.region_bbox,
                "region_category": region.region_category,
                "confidence": round(region.confidence, 2),
                "reason": region.reason,
                "needs_manual_review": region.needs_manual_review,
                "extracted_rows": region.extracted_rows,
                "evidence_scores": region.evidence_scores,
            }
            page_regions.append(region_data)
            all_regions.append(region_data)
        page = {
            "pdf_page_number": record.original_page_number,
            "sheet_number": record.sheet_number,
            "sheet_title": record.sheet_title,
            "detected_discipline": record.detected_discipline,
            "discipline_prefix": record.discipline_prefix,
            "drawing_set": record.drawing_set,
            "category": slug,
            "matched_index": record.matched_index,
            "index_source_page": record.index_source_page,
            "confidence": round(record.confidence, 2),
            "needs_manual_review": record.needs_manual_review,
            "reason": record.reason,
            "selected_category": slug,
            "top_candidates": record.top_candidates,
            "evidence_scores": record.evidence_scores,
            "small_plan_mode": record.small_plan_mode,
            "raw_title_block_ocr_text": record.raw_title_block_text,
            "debug_files": record.debug_files,
            "regions": page_regions,
        }
        pages.append(page)

    return {
        "source_pdf": source_pdf.name,
        "source_pdf_path": str(source_pdf),
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "manual_review_threshold": MANUAL_REVIEW_THRESHOLD,
        "analysis": analysis_summary or {},
        "debug_folder": str(debug_dir) if debug_dir is not None else "",
        "pages": pages,
        "regions": all_regions,
        "groups": groups,
    }


def write_manifest_json(
    source_pdf: Path,
    records: list[PageRecord],
    output_dir: Path,
    analysis_summary: dict[str, object] | None = None,
    debug_dir: Path | None = None,
) -> Path:
    manifest_path = output_dir / "manifest.json"
    with manifest_path.open("w", encoding="utf-8") as manifest_file:
        json.dump(manifest_from_records(source_pdf, records, analysis_summary, debug_dir), manifest_file, indent=2)
    return manifest_path


def correction_memory_paths(source_pdf: Path) -> list[Path]:
    paths = [source_pdf.with_name("floorplan_reader_corrections.json")]
    try:
        paths.append(Path.home() / ".floorplan_reader_corrections.json")
    except Exception:
        pass
    return paths


def load_correction_memory(source_pdf: Path) -> list[dict[str, object]]:
    corrections: list[dict[str, object]] = []
    for path in correction_memory_paths(source_pdf):
        if not path.exists():
            continue
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(loaded, list):
            corrections.extend(item for item in loaded if isinstance(item, dict))
    return corrections


LEARNING_STOP_WORDS = {
    "and",
    "the",
    "sheet",
    "sheets",
    "plan",
    "plans",
    "schedule",
    "schedules",
    "detail",
    "details",
    "page",
    "floor",
}


def learning_tokens(value: str) -> set[str]:
    return {
        token.lower()
        for token in re.findall(r"[A-Za-z0-9]+", value)
        if len(token) > 1 and token.lower() not in LEARNING_STOP_WORDS
    }


def token_jaccard(left: Iterable[str], right: Iterable[str]) -> float:
    left_set = set(left)
    right_set = set(right)
    if not left_set or not right_set:
        return 0.0
    return len(left_set & right_set) / len(left_set | right_set)


def learning_features_from_manifest_page(page: dict[str, object]) -> dict[str, object]:
    title = str(page.get("sheet_title", ""))
    raw_text = str(page.get("raw_title_block_ocr_text", ""))
    region_categories = [
        str(region.get("region_category", ""))
        for region in page.get("regions", [])
        if isinstance(region, dict) and region.get("region_category")
    ]
    return {
        "sheet_number": str(page.get("sheet_number", "")),
        "sheet_prefix": sheet_prefix(str(page.get("sheet_number", ""))),
        "sheet_title": title,
        "title_tokens": sorted(learning_tokens(f"{title} {raw_text}")),
        "original_category": str(page.get("category") or page.get("selected_category") or ""),
        "top_candidate_categories": [
            str(item.get("category", ""))
            for item in page.get("top_candidates", [])
            if isinstance(item, dict) and item.get("category")
        ],
        "region_categories": sorted(set(region_categories)),
        "evidence_scores": page.get("evidence_scores", {}) if isinstance(page.get("evidence_scores"), dict) else {},
    }


def learning_features_from_record(record: PageRecord) -> dict[str, object]:
    return {
        "sheet_number": record.sheet_number,
        "sheet_prefix": sheet_prefix(record.sheet_number),
        "sheet_title": record.sheet_title,
        "title_tokens": sorted(learning_tokens(f"{record.sheet_title} {record.raw_title_block_text}")),
        "original_category": category_slug(record.category_files[0] if record.category_files else CATEGORY_REVIEW),
        "top_candidate_categories": [
            str(item.get("category", ""))
            for item in record.top_candidates
            if isinstance(item, dict) and item.get("category")
        ],
        "region_categories": sorted({region.region_category for region in record.regions}),
        "evidence_scores": record.evidence_scores,
    }


def upsert_correction(path: Path, entry: dict[str, object]) -> None:
    existing: list[dict[str, object]] = []
    if path.exists():
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(loaded, list):
                existing = [item for item in loaded if isinstance(item, dict)]
        except Exception:
            existing = []
    existing = [
        item
        for item in existing
        if not (item.get("source_pdf") == entry.get("source_pdf") and item.get("pdf_page_number") == entry.get("pdf_page_number"))
    ]
    existing.append(entry)
    path.write_text(json.dumps(existing, indent=2), encoding="utf-8")


def save_manual_correction(
    source_pdf: Path,
    pdf_page_number: int,
    old_category: str,
    corrected_category: str,
    reason: str,
    memory_path: Path | None = None,
    page_features: dict[str, object] | None = None,
) -> Path:
    entry = {
        "source_pdf": source_pdf.name,
        "pdf_page_number": pdf_page_number,
        "old_category": old_category,
        "corrected_category": corrected_category,
        "reason": reason,
        "features": page_features or {},
        "learning_version": 2,
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }
    paths = [memory_path] if memory_path is not None else correction_memory_paths(source_pdf)
    saved_path: Path | None = None
    for path in paths:
        if path is not None:
            try:
                upsert_correction(path, entry)
                saved_path = saved_path or path
            except Exception:
                continue
    return saved_path or (paths[0] if paths[0] is not None else correction_memory_paths(source_pdf)[0])


def learned_correction_score(record: PageRecord, correction: dict[str, object], source_pdf: Path) -> float:
    if correction.get("source_pdf") in {source_pdf.name, str(source_pdf)} and correction.get("pdf_page_number") == record.original_page_number:
        return 1.0
    features = correction.get("features")
    if not isinstance(features, dict):
        return 0.0
    record_features = learning_features_from_record(record)
    score = 0.0
    if features.get("original_category") == record_features.get("original_category"):
        score += 0.18
    if features.get("sheet_prefix") and features.get("sheet_prefix") == record_features.get("sheet_prefix"):
        score += 0.12
    if features.get("sheet_number") and features.get("sheet_number") == record_features.get("sheet_number"):
        score += 0.10
    score += 0.38 * token_jaccard(
        features.get("title_tokens", []) if isinstance(features.get("title_tokens"), list) else [],
        record_features.get("title_tokens", []) if isinstance(record_features.get("title_tokens"), list) else [],
    )
    score += 0.16 * token_jaccard(
        features.get("region_categories", []) if isinstance(features.get("region_categories"), list) else [],
        record_features.get("region_categories", []) if isinstance(record_features.get("region_categories"), list) else [],
    )
    score += 0.10 * token_jaccard(
        features.get("top_candidate_categories", []) if isinstance(features.get("top_candidate_categories"), list) else [],
        record_features.get("top_candidate_categories", []) if isinstance(record_features.get("top_candidate_categories"), list) else [],
    )
    return clamp_score(score)


def apply_single_correction(record: PageRecord, correction: dict[str, object], score: float) -> PageRecord | None:
    corrected_category = str(correction.get("corrected_category", "")).strip()
    category_file = category_from_slug(corrected_category) or corrected_category
    if category_file not in CATEGORY_ORDER:
        return None
    confidence = 0.97 if score >= 0.99 else max(0.82, min(0.92, score + 0.18))
    evidence_scores = dict(record.evidence_scores)
    evidence_scores["combined_score"] = confidence
    evidence_scores["correction_memory_score"] = round(score, 2)
    return replace(
        record,
        category_files=[category_file],
        confidence=confidence,
        needs_manual_review=False,
        reason=f"Applied learned correction ({score:.2f} match): {correction.get('reason', 'No reason provided.')}",
        evidence_scores=evidence_scores,
        top_candidates=[
            {"category": category_slug(category_file), "score": round(confidence, 2)},
            *[
                item
                for item in record.top_candidates
                if item.get("category") != category_slug(category_file)
            ],
        ][:3],
    )


def apply_correction_memory(records: list[PageRecord], source_pdf: Path) -> list[PageRecord]:
    corrections = load_correction_memory(source_pdf)
    if not corrections:
        return records
    updated: list[PageRecord] = []
    for record in records:
        best: tuple[float, dict[str, object]] | None = None
        for correction in corrections:
            score = learned_correction_score(record, correction, source_pdf)
            if score >= 0.72 and (best is None or score > best[0]):
                best = (score, correction)
        if best is None:
            updated.append(record)
            continue
        corrected_record = apply_single_correction(record, best[1], best[0])
        if corrected_record is None:
            updated.append(record)
            continue
        updated.append(corrected_record)
    return updated


def write_debug_reports(
    source_pdf: Path,
    records: list[PageRecord],
    output_dir: Path,
    debug_dir: Path,
    manifest_path: Path,
    analysis_summary: dict[str, object],
) -> None:
    debug_dir.mkdir(parents=True, exist_ok=True)
    confidence_rows = []
    manual_rows = []
    for record in records:
        row = {
            "pdf_page_number": record.original_page_number,
            "sheet_number": record.sheet_number,
            "sheet_title": record.sheet_title,
            "selected_category": category_slug(record.category_files[0] if record.category_files else CATEGORY_REVIEW),
            "confidence": round(record.confidence, 2),
            "needs_manual_review": record.needs_manual_review,
            "reason": record.reason,
            "top_candidates": record.top_candidates,
            "evidence_scores": record.evidence_scores,
            "debug_files": record.debug_files,
        }
        confidence_rows.append(row)
        if record.needs_manual_review:
            manual_rows.append(row)

    (debug_dir / "confidence_report.json").write_text(
        json.dumps({"source_pdf": source_pdf.name, "analysis": analysis_summary, "pages": confidence_rows}, indent=2),
        encoding="utf-8",
    )
    (debug_dir / "manual_review_list.json").write_text(
        json.dumps({"source_pdf": source_pdf.name, "pages": manual_rows}, indent=2),
        encoding="utf-8",
    )
    (debug_dir / "manifest.json").write_text(manifest_path.read_text(encoding="utf-8"), encoding="utf-8")

    correction_template = [
        {
            "source_pdf": source_pdf.name,
            "pdf_page_number": row["pdf_page_number"],
            "old_category": row["selected_category"],
            "corrected_category": "",
            "reason": "",
        }
        for row in manual_rows
    ]
    (debug_dir / "manual_corrections_template.json").write_text(
        json.dumps(correction_template, indent=2),
        encoding="utf-8",
    )

    html_parts = [
        "<!doctype html><html><head><meta charset='utf-8'>",
        "<title>Floorplan Reader Manual Review</title>",
        "<style>body{font-family:Segoe UI,Arial,sans-serif;margin:24px;background:#f6f8fb;color:#17202a}"
        "article{background:white;border:1px solid #d9e2ec;border-radius:8px;padding:16px;margin:0 0 16px}"
        "img{max-width:260px;border:1px solid #ccd6e0;margin:4px 8px 4px 0}"
        "code,pre{background:#eef2f7;padding:2px 4px;border-radius:4px}pre{white-space:pre-wrap}</style>",
        "</head><body>",
        f"<h1>Manual Review Report</h1><p><strong>Source:</strong> {source_pdf.name}</p>",
        f"<p><strong>Small Plan Mode:</strong> {analysis_summary.get('small_plan_mode')}</p>",
    ]
    for row in manual_rows:
        html_parts.append("<article>")
        html_parts.append(
            f"<h2>Page {row['pdf_page_number']} - {row['sheet_number'] or 'No sheet number'}</h2>"
            f"<p><strong>Title:</strong> {row['sheet_title'] or 'Not detected'}<br>"
            f"<strong>Selected:</strong> {row['selected_category']} "
            f"({row['confidence']:.2f})</p>"
            f"<p><strong>Reason:</strong> {row['reason']}</p>"
            f"<pre>{json.dumps(row['top_candidates'], indent=2)}</pre>"
        )
        for thumbnail in row.get("debug_files", {}).get("thumbnails", [])[:1]:
            html_parts.append(f"<img src='../{thumbnail}' alt='Page thumbnail'>")
        for crop in row.get("debug_files", {}).get("title_block_crops", [])[:2]:
            html_parts.append(f"<img src='../{crop}' alt='Title block crop'>")
        for crop in row.get("debug_files", {}).get("table_crops", [])[:3]:
            html_parts.append(f"<img src='../{crop}' alt='Detected table crop'>")
        html_parts.append("</article>")
    html_parts.append("</body></html>")
    (debug_dir / "manual_review_report.html").write_text("\n".join(html_parts), encoding="utf-8")


def analyze_pdf(
    pdf_path: Path,
    status_callback: StatusCallback | None = None,
    debug_dir: Path | None = None,
) -> tuple[list[PageRecord], "fitz.Document", dict[str, SheetIndexEntry], dict[str, object]]:
    source_doc = fitz.open(pdf_path)
    if debug_dir is not None:
        debug_dir.mkdir(parents=True, exist_ok=True)
    records: list[PageRecord] = []
    page_texts: list[str] = []
    page_lines: list[list[str]] = []
    page_words: list[list[tuple]] = []
    page_rects: list["fitz.Rect"] = []
    page_render_notes: list[str] = []
    page_count = source_doc.page_count

    if status_callback is not None and page_count >= 75:
        status_callback(f"Large plan set detected: {page_count} pages. Using low-memory processing.")

    last_status = 0.0
    for page_index in range(page_count):
        now = time.monotonic()
        if status_callback is not None and (
            page_index == 0
            or page_index + 1 == page_count
            or now - last_status >= STATUS_UPDATE_SECONDS
        ):
            status_callback(f"Reading page {page_index + 1} of {page_count}...")
            last_status = now

        page = source_doc.load_page(page_index)
        try:
            page_render_notes.append(render_metadata_image(page))
        except Exception as exc:
            page_render_notes.append(f"metadata render unavailable: {exc}")
        text = page.get_text("text", sort=True) or ""
        words = page.get_text("words", sort=True) or []
        ocr_notes: list[str] = []
        if len(clean_lines(text)) < 3:
            for ocr_dpi in (200, 300):
                ocr_text, ocr_words, ocr_note = extract_page_ocr_text(page, ocr_dpi)
                ocr_notes.append(ocr_note)
                if len(clean_lines(ocr_text)) > len(clean_lines(text)):
                    text = ocr_text
                    words = ocr_words or words
                    break
        if ocr_notes:
            page_render_notes[-1] = page_render_notes[-1] + "; " + "; ".join(ocr_notes)
        lines = clean_lines(text)
        page_texts.append(text)
        page_lines.append(lines)
        page_words.append(words)
        page_rects.append(page.rect)

    if status_callback is not None:
        status_callback("Reading sheet index from cover/index pages...")

    sheet_index, index_page_indexes = build_sheet_index(
        page_lines,
        page_words,
        status_callback=status_callback,
    )
    initial_small_plan_mode, initial_small_plan_reasons = small_plan_mode_decision(
        page_count,
        sheet_index,
        index_page_indexes,
    )
    if status_callback is not None and initial_small_plan_mode:
        status_callback("Accuracy Mode v2: Small Plan Mode active. Using heavier region/table review.")

    for page_index, (text, lines) in enumerate(zip(page_texts, page_lines)):
        title_block_sheet_number = detect_title_block_sheet_number(
            page_words[page_index],
            page_rects[page_index],
            sheet_index,
        )
        if title_block_sheet_number:
            sheet_number = title_block_sheet_number
            sheet_number_index = None
        else:
            word_sheet_number = detect_sheet_number_from_index_words(
                page_words[page_index],
                page_rects[page_index],
                sheet_index,
            )
            if word_sheet_number:
                sheet_number = word_sheet_number
                sheet_number_index = None
            else:
                sheet_number, sheet_number_index = detect_sheet_number_from_index(lines, sheet_index)
        page_title = detect_title_block_sheet_title(
            page_words[page_index],
            page_rects[page_index],
            sheet_number,
        ) or detect_sheet_title(lines, sheet_number_index)

        raw_title_block_text = extract_title_block_text(page_words[page_index], page_rects[page_index])

        if page_index in index_page_indexes:
            sheet_number = ""
            index_title = next((clean_title(line) for line in lines if INDEX_PAGE_RE.search(line)), "")
            sheet_title = index_title or "Cover / Sheet Index"
            drawing_set = ""
            sheet_title_source = "cover/index page"
            index_source_page = None
            matched_index = True
        else:
            index_entry, fuzzy_index_match = find_sheet_index_entry(sheet_number, sheet_index)
            if index_entry is not None:
                sheet_number = index_entry.sheet_number
                sheet_title = index_entry.sheet_title
                drawing_set = index_entry.drawing_set
                sheet_title_source = (
                    f"sheet index page {index_entry.source_page_number}"
                    + (" (fuzzy sheet-number match)" if fuzzy_index_match else "")
                )
                index_source_page = index_entry.source_page_number
                matched_index = True
            elif page_title:
                sheet_title = page_title
                drawing_set = ""
                sheet_title_source = "page text"
                index_source_page = None
                matched_index = False
            else:
                sheet_title = ""
                drawing_set = ""
                sheet_title_source = "not found"
                index_source_page = None
                matched_index = False

        searchable_text = f"{drawing_set}\n{sheet_title}\n{text}"
        category_file, confidence, reason, needs_manual_review, matched_keywords = classify_metadata_first(
            text=searchable_text,
            words=page_words[page_index],
            sheet_number=sheet_number,
            sheet_title=sheet_title,
            drawing_set=drawing_set,
            is_index_page=page_index in index_page_indexes,
            matched_index=matched_index,
            raw_title_block_text=f"{raw_title_block_text}\n{page_render_notes[page_index]}",
        )
        regions = detect_page_regions(
            page_index=page_index,
            pdf_page_number=page_index + 1,
            words=page_words[page_index],
            page_rect=page_rects[page_index],
            sheet_number=sheet_number,
            sheet_title=sheet_title,
            drawing_set=drawing_set,
        )
        category_file, confidence, reason, needs_manual_review = page_category_from_regions(
            category_file,
            confidence,
            reason,
            regions,
            sheet_title=sheet_title,
            drawing_set=drawing_set,
            matched_index=matched_index,
        )
        category_files = [category_file]
        evidence_scores, top_candidates, combined_confidence = page_evidence_and_candidates(
            selected_category=category_file,
            selected_confidence=confidence,
            text=searchable_text,
            words=page_words[page_index],
            sheet_number=sheet_number,
            sheet_title=sheet_title,
            drawing_set=drawing_set,
            matched_index=matched_index,
            raw_title_block_text=raw_title_block_text,
            regions=regions,
        )
        confidence = combined_confidence
        needs_manual_review = needs_manual_review or confidence < MANUAL_REVIEW_THRESHOLD
        page_debug_files = write_page_debug_artifacts(
            page=source_doc.load_page(page_index),
            page_number=page_index + 1,
            text=text,
            raw_title_block_text=raw_title_block_text,
            regions=regions,
            debug_dir=debug_dir,
            high_detail=initial_small_plan_mode,
        )

        records.append(
            PageRecord(
                page_index=page_index,
                original_page_number=page_index + 1,
                sheet_number=sheet_number,
                sheet_title=sheet_title,
                drawing_set=drawing_set,
                discipline_prefix=sheet_prefix(sheet_number),
                detected_discipline=detected_discipline(sheet_number, drawing_set),
                raw_title_block_text=raw_title_block_text,
                matched_index=matched_index,
                confidence=confidence,
                reason=reason,
                needs_manual_review=needs_manual_review,
                matched_keywords=matched_keywords,
                category_files=category_files,
                sheet_title_source=sheet_title_source,
                index_source_page=index_source_page,
                regions=regions,
                evidence_scores=evidence_scores,
                top_candidates=top_candidates,
                small_plan_mode=initial_small_plan_mode,
                debug_files=page_debug_files,
            )
        )

    records = apply_neighbor_continuations(records)
    final_small_plan_mode, final_small_plan_reasons = small_plan_mode_decision(
        page_count,
        sheet_index,
        index_page_indexes,
        records,
    )
    small_plan_mode = initial_small_plan_mode or final_small_plan_mode
    small_plan_reasons = list(dict.fromkeys(initial_small_plan_reasons + final_small_plan_reasons))
    records = apply_small_plan_mode(records, small_plan_mode, small_plan_reasons)
    analysis_summary = {
        "accuracy_mode": "v2",
        "small_plan_mode": small_plan_mode,
        "small_plan_reasons": small_plan_reasons,
        "page_count": page_count,
        "sheet_index_entry_count": len(sheet_index),
        "index_page_count": len(index_page_indexes),
        "matched_index_page_count": sum(1 for record in records if record.matched_index),
        "manual_review_page_count": sum(1 for record in records if record.needs_manual_review),
        "ocr_passes": [
            "native_pdf_text",
            "normal_resolution_metadata_render",
            "high_resolution_debug_render_for_small_plan_mode",
            "title_block_crop_text",
            "detected_table_region_text",
            "rotation_normalized_native_page_text_when_available",
        ],
    }
    return records, source_doc, sheet_index, analysis_summary


def open_output_folder(path: Path) -> None:
    if sys.platform.startswith("win"):
        subprocess.run(["explorer", str(path)], check=False)
    elif sys.platform == "darwin":
        subprocess.run(["open", str(path)], check=False)
    else:
        subprocess.run(["xdg-open", str(path)], check=False)


def split_pdf(
    pdf_path: Path,
    skip_empty_pdfs: bool = False,
    open_folder: bool = False,
    status_callback: StatusCallback | None = None,
) -> SplitResult:
    pdf_path = pdf_path.expanduser().resolve()
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")
    if pdf_path.suffix.lower() != ".pdf":
        raise ValueError(f"Selected file is not a PDF: {pdf_path}")

    if status_callback is not None:
        status_callback(f"Preparing output folder for {pdf_path.name}...")

    output_dir = make_output_dir(pdf_path)
    source_doc = None
    debug_dir = output_dir / "debug_accuracy_v2"
    try:
        records, source_doc, sheet_index, analysis_summary = analyze_pdf(
            pdf_path,
            status_callback=status_callback,
            debug_dir=debug_dir,
        )
        records = apply_correction_memory(records, pdf_path)
        analysis_summary["manual_review_page_count"] = sum(1 for record in records if record.needs_manual_review)
        analysis_summary["correction_memory_count"] = len(load_correction_memory(pdf_path))
        if status_callback is not None:
            status_callback("Writing JSON manifest before splitting PDFs...")
        manifest_path = write_manifest_json(
            pdf_path,
            records,
            output_dir,
            analysis_summary=analysis_summary,
            debug_dir=debug_dir,
        )
        write_debug_reports(pdf_path, records, output_dir, debug_dir, manifest_path, analysis_summary)
        save_category_pdfs(
            source_doc,
            records,
            output_dir,
            skip_empty_pdfs,
            status_callback=status_callback,
        )
        if status_callback is not None:
            status_callback("Writing CSV index...")
        csv_path = write_csv_index(records, output_dir)
        sheet_index_csv_path = write_sheet_index_csv(sheet_index, output_dir)
    finally:
        if source_doc is not None:
            source_doc.close()

    if open_folder:
        open_output_folder(output_dir)

    return SplitResult(
        output_dir=output_dir,
        manifest_path=manifest_path,
        csv_path=csv_path,
        sheet_index_csv_path=sheet_index_csv_path,
        page_count=len(records),
        debug_dir=debug_dir,
    )


def prepare_review_package(
    pdf_path: Path,
    status_callback: StatusCallback | None = None,
) -> SplitResult:
    pdf_path = pdf_path.expanduser().resolve()
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")
    if pdf_path.suffix.lower() != ".pdf":
        raise ValueError(f"Selected file is not a PDF: {pdf_path}")

    if status_callback is not None:
        status_callback(f"Preparing review package for {pdf_path.name}...")

    output_dir = make_output_dir(pdf_path)
    debug_dir = output_dir / "debug_accuracy_v2"
    source_doc = None
    try:
        records, source_doc, sheet_index, analysis_summary = analyze_pdf(
            pdf_path,
            status_callback=status_callback,
            debug_dir=debug_dir,
        )
        records = apply_correction_memory(records, pdf_path)
        analysis_summary["manual_review_page_count"] = sum(1 for record in records if record.needs_manual_review)
        analysis_summary["correction_memory_count"] = len(load_correction_memory(pdf_path))
        analysis_summary["review_before_export"] = True
        if status_callback is not None:
            status_callback("Writing review manifest and debug previews...")
        manifest_path = write_manifest_json(
            pdf_path,
            records,
            output_dir,
            analysis_summary=analysis_summary,
            debug_dir=debug_dir,
        )
        write_debug_reports(pdf_path, records, output_dir, debug_dir, manifest_path, analysis_summary)
        csv_path = write_csv_index(records, output_dir)
        sheet_index_csv_path = write_sheet_index_csv(sheet_index, output_dir)
    finally:
        if source_doc is not None:
            source_doc.close()

    return SplitResult(
        output_dir=output_dir,
        manifest_path=manifest_path,
        csv_path=csv_path,
        sheet_index_csv_path=sheet_index_csv_path,
        page_count=len(records),
        debug_dir=debug_dir,
    )


def update_manifest_groups(manifest: dict[str, object]) -> None:
    groups = {slug: [] for slug in CATEGORY_SLUGS.values()}
    for page in manifest.get("pages", []):
        if not isinstance(page, dict):
            continue
        raw_slug = str(page.get("category") or page.get("selected_category") or category_slug(CATEGORY_REVIEW))
        normalized_category = category_from_slug(raw_slug) or CATEGORY_REVIEW
        category_slug_value = category_slug(normalized_category)
        page["category"] = category_slug_value
        page["selected_category"] = category_slug_value
        groups.setdefault(category_slug_value, []).append(int(page.get("pdf_page_number", 0)))
    manifest["groups"] = groups


def save_manifest_dict(manifest_path: Path, manifest: dict[str, object]) -> None:
    update_manifest_groups(manifest)
    manifest["last_review_update_at"] = datetime.now().isoformat(timespec="seconds")
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def record_from_manifest_page(page: dict[str, object]) -> PageRecord:
    category = category_from_slug(str(page.get("category", ""))) or CATEGORY_REVIEW
    pdf_page_number = int(page.get("pdf_page_number", 0))
    return PageRecord(
        page_index=max(pdf_page_number - 1, 0),
        original_page_number=pdf_page_number,
        sheet_number=str(page.get("sheet_number", "")),
        sheet_title=str(page.get("sheet_title", "")),
        drawing_set=str(page.get("drawing_set", "")),
        discipline_prefix=str(page.get("discipline_prefix", "")),
        detected_discipline=str(page.get("detected_discipline", "")),
        raw_title_block_text=str(page.get("raw_title_block_ocr_text", "")),
        matched_index=bool(page.get("matched_index", False)),
        confidence=float(page.get("confidence", 0.0) or 0.0),
        reason=str(page.get("reason", "")),
        needs_manual_review=bool(page.get("needs_manual_review", False)),
        matched_keywords=[],
        category_files=[category],
        sheet_title_source="reviewed manifest",
        index_source_page=page.get("index_source_page") if isinstance(page.get("index_source_page"), int) else None,
        regions=[],
        evidence_scores=page.get("evidence_scores", {}) if isinstance(page.get("evidence_scores"), dict) else {},
        top_candidates=page.get("top_candidates", []) if isinstance(page.get("top_candidates"), list) else [],
        small_plan_mode=bool(page.get("small_plan_mode", False)),
        debug_files=page.get("debug_files", {}) if isinstance(page.get("debug_files"), dict) else {},
    )


def export_from_manifest(
    manifest_path: Path,
    skip_empty_pdfs: bool = False,
    status_callback: StatusCallback | None = None,
) -> None:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    source_pdf = Path(str(manifest["source_pdf_path"]))
    records = [
        record_from_manifest_page(page)
        for page in manifest.get("pages", [])
        if isinstance(page, dict)
    ]
    if status_callback is not None:
        status_callback("Exporting approved section PDFs...")
    source_doc = fitz.open(source_pdf)
    try:
        save_category_pdfs(
            source_doc,
            records,
            manifest_path.parent,
            skip_empty_pdfs=skip_empty_pdfs,
            status_callback=status_callback,
        )
    finally:
        source_doc.close()
    manifest["exported_at"] = datetime.now().isoformat(timespec="seconds")
    save_manifest_dict(manifest_path, manifest)


def select_pdf_with_dialog() -> Path | None:
    try:
        import tkinter as tk
        from tkinter import filedialog
    except Exception as exc:
        print(f"Could not open file picker: {exc}", file=sys.stderr)
        return None

    root = tk.Tk()
    root.withdraw()
    root.update()
    try:
        root.attributes("-topmost", True)
    except tk.TclError:
        pass

    selected = filedialog.askopenfilename(
        title="Select construction plan-set PDF",
        filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
    )
    root.destroy()
    return Path(selected).expanduser() if selected else None


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Split a construction plan-set PDF into category PDFs and a CSV index."
    )
    parser.add_argument(
        "pdf",
        nargs="?",
        help="Path to the PDF plan set. If omitted, a file picker opens.",
    )
    parser.add_argument(
        "--skip-empty-pdfs",
        action="store_true",
        help="Skip categories that receive no pages instead of writing placeholder PDFs.",
    )
    parser.add_argument(
        "--open-folder",
        action="store_true",
        help="Open the output folder in Finder after processing.",
    )
    parser.add_argument(
        "--cli",
        action="store_true",
        help="Use the command-line flow instead of the desktop app window.",
    )
    parser.add_argument(
        "--worker-json",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--prepare-review",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    return parser.parse_args(argv)


def emit_worker_event(kind: str, **payload: object) -> None:
    print(json.dumps({"kind": kind, **payload}), flush=True)


def run_worker_json(args: argparse.Namespace) -> int:
    if not args.pdf:
        emit_worker_event("error", message="No PDF selected.")
        return 1

    try:
        if args.prepare_review:
            result = prepare_review_package(
                Path(args.pdf),
                status_callback=lambda message: emit_worker_event("status", message=message),
            )
        else:
            result = split_pdf(
                Path(args.pdf),
                skip_empty_pdfs=args.skip_empty_pdfs,
                open_folder=False,
                status_callback=lambda message: emit_worker_event("status", message=message),
            )
    except Exception as exc:
        emit_worker_event("error", message=str(exc))
        return 1

    emit_worker_event(
        "done",
        output_dir=str(result.output_dir),
        manifest_path=str(result.manifest_path),
        csv_path=str(result.csv_path),
        sheet_index_csv_path=str(result.sheet_index_csv_path),
        page_count=result.page_count,
        debug_dir=str(result.debug_dir) if result.debug_dir is not None else "",
    )
    return 0


def worker_command(pdf_path: Path) -> list[str]:
    if getattr(sys, "frozen", False):
        return [sys.executable, "--worker-json", "--prepare-review", str(pdf_path)]
    return [sys.executable, str(Path(__file__).resolve()), "--worker-json", "--prepare-review", str(pdf_path)]


def hidden_subprocess_kwargs() -> dict[str, object]:
    kwargs: dict[str, object] = {
        "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE,
        "text": True,
        "encoding": "utf-8",
        "errors": "replace",
        "bufsize": 1,
    }
    if sys.platform.startswith("win"):
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        kwargs["startupinfo"] = startupinfo
        kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    return kwargs


class ReviewManagerWindow:
    def __init__(self, parent: object, result: SplitResult) -> None:
        import tkinter as tk
        from tkinter import messagebox, ttk

        self.tk = tk
        self.ttk = ttk
        self.messagebox = messagebox
        self.result = result
        self.manifest_path = result.manifest_path
        self.output_dir = result.output_dir
        self.manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        self.pages: list[dict[str, object]] = [
            page for page in self.manifest.get("pages", []) if isinstance(page, dict)
        ]
        self.selected_section = ""
        self.selected_page_number: int | None = None
        self.preview_image = None
        self.preview_cache: dict[str, object] = {}
        self.export_queue: queue.Queue[tuple[str, object]] = queue.Queue()

        self.window = tk.Toplevel(parent)
        self.window.title("Floorplan Reader - Review Manager")
        self.window.geometry("1180x720")
        self.window.minsize(980, 620)
        self.window.configure(bg="#07111F")

        self.status_var = tk.StringVar(value="Review the detected sections. Export only after everything looks right.")
        self.category_var = tk.StringVar()
        self.detail_var = tk.StringVar(value="")
        self.page_pick_var = tk.StringVar()

        style = ttk.Style(self.window)
        style.configure("Review.TFrame", background="#07111F")
        style.configure("ReviewPanel.TFrame", background="#182A3D")
        style.configure("ReviewGlass.TFrame", background="#21364B")
        style.configure("Review.TLabel", background="#07111F", foreground="#EAF4FF")
        style.configure("ReviewPanel.TLabel", background="#182A3D", foreground="#EAF4FF")
        style.configure("ReviewTitle.TLabel", background="#07111F", foreground="#F7FBFF", font=("Segoe UI", 19, "bold"))
        style.configure("Review.TButton", font=("Segoe UI", 9, "bold"), padding=(10, 7))
        style.configure("Treeview", background="#EAF4FF", fieldbackground="#EAF4FF", foreground="#142235", rowheight=28)
        style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"))

        container = ttk.Frame(self.window, padding=14, style="Review.TFrame")
        container.pack(fill="both", expand=True)
        container.rowconfigure(1, weight=1)
        container.columnconfigure(0, weight=1)

        header = ttk.Frame(container, style="Review.TFrame")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        header.columnconfigure(0, weight=1)
        ttk.Label(header, text="Review Manager", style="ReviewTitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(header, textvariable=self.status_var, style="Review.TLabel").grid(row=1, column=0, sticky="w", pady=(2, 0))

        body = ttk.Panedwindow(container, orient="horizontal")
        body.grid(row=1, column=0, sticky="nsew")

        section_frame = ttk.Frame(body, padding=10, style="ReviewPanel.TFrame")
        page_frame = ttk.Frame(body, padding=10, style="ReviewPanel.TFrame")
        preview_frame = ttk.Frame(body, padding=10, style="ReviewPanel.TFrame")
        body.add(section_frame, weight=1)
        body.add(page_frame, weight=3)
        body.add(preview_frame, weight=3)

        ttk.Label(section_frame, text="Sections", style="ReviewPanel.TLabel").pack(anchor="w")
        self.section_list = tk.Listbox(
            section_frame,
            height=20,
            exportselection=False,
            bg="#DDEDFB",
            fg="#102235",
            selectbackground="#6EE7D8",
            selectforeground="#07111F",
            relief="flat",
            highlightthickness=0,
            font=("Segoe UI", 9),
        )
        self.section_list.pack(fill="both", expand=True, pady=(8, 0))
        self.section_list.bind("<<ListboxSelect>>", lambda _event: self.on_section_select())

        ttk.Label(page_frame, text="Pages In Section", style="ReviewPanel.TLabel").pack(anchor="w")
        self.page_tree = ttk.Treeview(
            page_frame,
            columns=("page", "sheet", "title", "confidence"),
            show="headings",
            selectmode="extended",
        )
        for column, label, width in [
            ("page", "Page", 55),
            ("sheet", "Sheet", 90),
            ("title", "Title", 260),
            ("confidence", "Conf.", 70),
        ]:
            self.page_tree.heading(column, text=label)
            self.page_tree.column(column, width=width, anchor="w")
        self.page_tree.pack(fill="both", expand=True, pady=(8, 0))
        self.page_tree.tag_configure("review", background="#FBE7EC")
        self.page_tree.tag_configure("learned", background="#E7F8F4")
        self.page_tree.bind("<<TreeviewSelect>>", lambda _event: self.on_page_select())
        self.page_tree.bind("<Control-a>", self.select_all_section_event)
        self.page_tree.bind("<Escape>", self.clear_page_selection_event)

        pick_frame = ttk.Frame(page_frame, style="ReviewPanel.TFrame")
        pick_frame.pack(fill="x", pady=(8, 0))
        pick_frame.columnconfigure(1, weight=1)
        ttk.Label(
            pick_frame,
            text="Exact pages:",
            style="ReviewPanel.TLabel",
        ).grid(row=0, column=0, sticky="w", padx=(0, 6))
        self.page_pick_entry = ttk.Entry(pick_frame, textvariable=self.page_pick_var)
        self.page_pick_entry.grid(row=0, column=1, sticky="ew", padx=(0, 6))
        self.page_pick_entry.bind("<Return>", lambda _event: self.select_listed_pages())
        ttk.Button(pick_frame, text="Select Listed", command=self.select_listed_pages, style="Review.TButton").grid(row=0, column=2, sticky="ew", padx=(0, 6))
        ttk.Button(pick_frame, text="Clear", command=self.clear_page_selection, style="Review.TButton").grid(row=0, column=3, sticky="ew")
        ttk.Label(
            page_frame,
            text="Ctrl-click individual sheets, Shift-click a range, or type pages like 21, 23, 59-63.",
            style="ReviewPanel.TLabel",
        ).pack(anchor="w", pady=(6, 0))

        ttk.Label(preview_frame, text="Preview", style="ReviewPanel.TLabel").pack(anchor="w")
        self.preview_label = ttk.Label(preview_frame, style="ReviewPanel.TLabel")
        self.preview_label.pack(fill="both", expand=True, pady=(8, 8))

        ttk.Label(preview_frame, textvariable=self.detail_var, wraplength=360, justify="left", style="ReviewPanel.TLabel").pack(anchor="w")
        self.category_combo = ttk.Combobox(preview_frame, textvariable=self.category_var, state="readonly")
        self.category_combo["values"] = [self.category_label(slug) for slug in CATEGORY_SLUGS.values()]
        self.category_combo.pack(fill="x", pady=(10, 8))

        button_grid = ttk.Frame(preview_frame, style="ReviewPanel.TFrame")
        button_grid.pack(fill="x")
        ttk.Button(button_grid, text="Move Selected", command=self.apply_current_category, style="Review.TButton").grid(row=0, column=0, sticky="ew", padx=(0, 6), pady=3)
        ttk.Button(button_grid, text="Try Next for Selected", command=self.retry_current_page, style="Review.TButton").grid(row=0, column=1, sticky="ew", pady=3)
        ttk.Button(button_grid, text="Retry Section", command=self.retry_section, style="Review.TButton").grid(row=1, column=0, sticky="ew", padx=(0, 6), pady=3)
        ttk.Button(button_grid, text="Open Debug Folder", command=self.open_debug_folder, style="Review.TButton").grid(row=1, column=1, sticky="ew", pady=3)
        ttk.Button(button_grid, text="Select All In Section", command=self.select_all_section, style="Review.TButton").grid(row=2, column=0, columnspan=2, sticky="ew", pady=3)
        button_grid.columnconfigure(0, weight=1)
        button_grid.columnconfigure(1, weight=1)

        footer = ttk.Frame(container, style="Review.TFrame")
        footer.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        footer.columnconfigure(0, weight=1)
        ttk.Button(footer, text="Export Approved PDFs", command=self.export_approved, style="Review.TButton").grid(row=0, column=1, padx=(8, 0))
        ttk.Button(footer, text="Open Output Folder", command=lambda: open_output_folder(self.output_dir), style="Review.TButton").grid(row=0, column=2, padx=(8, 0))

        self.refresh_sections()
        self.window.after(100, self.poll_export_queue)

    def category_label(self, slug: str) -> str:
        category = category_from_slug(slug) or CATEGORY_REVIEW
        return f"{CATEGORY_LABELS.get(category, slug)} ({slug})"

    def slug_from_label(self, label: str) -> str:
        match = re.search(r"\(([^()]+)\)\s*$", label)
        return match.group(1) if match else label

    def page_category(self, page: dict[str, object]) -> str:
        raw_slug = str(page.get("category") or page.get("selected_category") or category_slug(CATEGORY_REVIEW))
        normalized = category_from_slug(raw_slug)
        return category_slug(normalized) if normalized is not None else category_slug(CATEGORY_REVIEW)

    def refresh_sections(self) -> None:
        self.section_list.delete(0, "end")
        counts: dict[str, int] = {slug: 0 for slug in CATEGORY_SLUGS.values()}
        for page in self.pages:
            counts[self.page_category(page)] = counts.get(self.page_category(page), 0) + 1
        self.section_rows = [
            slug for slug in CATEGORY_SLUGS.values()
            if counts.get(slug, 0) or slug == category_slug(CATEGORY_REVIEW)
        ]
        for slug in self.section_rows:
            self.section_list.insert("end", f"{self.category_label(slug)} - {counts.get(slug, 0)} page(s)")
        if self.section_rows:
            if self.selected_section not in self.section_rows:
                self.selected_section = self.section_rows[0]
            index = self.section_rows.index(self.selected_section)
            self.section_list.selection_clear(0, "end")
            self.section_list.selection_set(index)
            self.section_list.see(index)
            self.refresh_pages()

    def on_section_select(self) -> None:
        selection = self.section_list.curselection()
        if not selection:
            return
        self.selected_section = self.section_rows[selection[0]]
        self.refresh_pages()

    def refresh_pages(self) -> None:
        for item in self.page_tree.get_children():
            self.page_tree.delete(item)
        for page in self.pages:
            if self.page_category(page) != self.selected_section:
                continue
            page_no = int(page.get("pdf_page_number", 0))
            tags = []
            if page.get("needs_manual_review"):
                tags.append("review")
            if "learned correction" in str(page.get("reason", "")).lower():
                tags.append("learned")
            self.page_tree.insert(
                "",
                "end",
                iid=str(page_no),
                tags=tuple(tags),
                values=(
                    page_no,
                    page.get("sheet_number", ""),
                    page.get("sheet_title", ""),
                    f"{float(page.get('confidence', 0) or 0):.2f}",
                ),
            )
        children = self.page_tree.get_children()
        if children:
            self.page_tree.selection_set(children[0])
            self.page_tree.focus(children[0])
            self.on_page_select()
        else:
            self.selected_page_number = None
            self.preview_label.configure(image="", text="No pages in this section.")
            self.detail_var.set("")

    def current_page(self) -> dict[str, object] | None:
        if self.selected_page_number is None:
            return None
        for page in self.pages:
            if int(page.get("pdf_page_number", 0)) == self.selected_page_number:
                return page
        return None

    def selected_pages(self) -> list[dict[str, object]]:
        selected_numbers = {int(item_id) for item_id in self.page_tree.selection()}
        return [
            page
            for page in self.pages
            if int(page.get("pdf_page_number", 0)) in selected_numbers
        ]

    def on_page_select(self) -> None:
        selection = self.page_tree.selection()
        if not selection:
            return
        self.selected_page_number = int(selection[-1])
        page = self.current_page()
        if page is None:
            return
        slug = self.page_category(page)
        self.category_var.set(self.category_label(slug))
        top_candidates = json.dumps(page.get("top_candidates", []), indent=2)
        self.detail_var.set(
            f"Page {page.get('pdf_page_number')} | Sheet {page.get('sheet_number') or 'not detected'}\n"
            f"{page.get('sheet_title') or 'No title detected'}\n\n"
            f"Confidence: {float(page.get('confidence', 0) or 0):.2f}\n"
            f"Manual review: {'yes' if page.get('needs_manual_review') else 'no'}\n"
            f"Selected sheets: {len(selection)}\n"
            f"Reason: {page.get('reason', '')}\n\nTop candidates:\n{top_candidates}"
        )
        self.show_preview(page)

    def preview_path_for_page(self, page: dict[str, object]) -> Path | None:
        debug_files = page.get("debug_files", {})
        if not isinstance(debug_files, dict):
            return None
        thumbnails = debug_files.get("thumbnails", [])
        if not thumbnails:
            return None
        first = Path(str(thumbnails[0]))
        if first.is_absolute():
            return first
        candidate_path = self.output_dir / first
        return candidate_path if candidate_path.exists() else None

    def show_preview(self, page: dict[str, object]) -> None:
        path = self.preview_path_for_page(page)
        if path is None or not path.exists():
            self.preview_label.configure(image="", text="No preview thumbnail found.")
            self.preview_image = None
            return
        try:
            cache_key = str(path)
            if cache_key in self.preview_cache:
                image = self.preview_cache[cache_key]
            else:
                image = self.tk.PhotoImage(file=str(path))
                max_width = 420
                max_height = 360
                factor = max(1, int(max(image.width() / max_width, image.height() / max_height)))
                if factor > 1:
                    image = image.subsample(factor, factor)
                self.preview_cache[cache_key] = image
            self.preview_image = image
            self.preview_label.configure(image=image, text="")
        except Exception as exc:
            self.preview_label.configure(image="", text=f"Could not load preview: {exc}")
            self.preview_image = None

    def apply_category_to_page(self, page: dict[str, object], slug: str, reason: str) -> None:
        old_category = self.page_category(page)
        page["category"] = slug
        page["selected_category"] = slug
        page["needs_manual_review"] = False
        page["confidence"] = max(float(page.get("confidence", 0) or 0), 0.95)
        page["reason"] = reason
        source_pdf = Path(str(self.manifest.get("source_pdf_path", "")))
        if source_pdf.exists():
            save_manual_correction(
                source_pdf,
                int(page.get("pdf_page_number", 0)),
                old_category,
                slug,
                reason,
                page_features=learning_features_from_manifest_page(page),
            )

    def apply_current_category(self) -> None:
        selected_pages = self.selected_pages()
        if not selected_pages:
            return
        slug = self.slug_from_label(self.category_var.get())
        for page in selected_pages:
            self.apply_category_to_page(page, slug, "Manual review assignment in Review Manager.")
        save_manifest_dict(self.manifest_path, self.manifest)
        self.selected_section = slug
        self.status_var.set(f"Moved {len(selected_pages)} page(s) to {slug}.")
        self.refresh_sections()

    def next_candidate_slug(self, page: dict[str, object]) -> str | None:
        current = self.page_category(page)
        for item in page.get("top_candidates", []):
            if not isinstance(item, dict):
                continue
            slug = str(item.get("category", ""))
            if slug and slug != current and category_from_slug(slug) is not None:
                return slug
        return None

    def retry_current_page(self) -> None:
        selected_pages = self.selected_pages()
        if not selected_pages:
            return
        changed = 0
        for page in selected_pages:
            next_slug = self.next_candidate_slug(page)
            if not next_slug:
                continue
            self.apply_category_to_page(page, next_slug, "Retried page using next best candidate.")
            changed += 1
            self.selected_section = next_slug
        save_manifest_dict(self.manifest_path, self.manifest)
        self.status_var.set(f"Retried {changed} selected page(s).")
        self.refresh_sections()

    def select_all_section(self) -> None:
        children = self.page_tree.get_children()
        if not children:
            return
        self.page_tree.selection_set(children)
        self.page_tree.focus(children[0])
        self.on_page_select()

    def select_all_section_event(self, _event: object) -> str:
        self.select_all_section()
        return "break"

    def clear_page_selection(self) -> None:
        self.page_tree.selection_remove(self.page_tree.selection())
        self.selected_page_number = None
        self.detail_var.set("No sheets selected. Ctrl-click, Shift-click, or type exact page numbers to pick sheets.")
        self.preview_label.configure(image="", text="Select one or more sheets to preview.")

    def clear_page_selection_event(self, _event: object) -> str:
        self.clear_page_selection()
        return "break"

    def parse_page_pick_text(self) -> set[int]:
        selected: set[int] = set()
        text = self.page_pick_var.get().strip()
        if not text:
            return selected
        normalized = re.sub(r"\s*-\s*", "-", text)
        for part in re.split(r"[,\s]+", normalized):
            if not part:
                continue
            range_match = re.fullmatch(r"(\d+)\s*-\s*(\d+)", part)
            if range_match:
                start = int(range_match.group(1))
                end = int(range_match.group(2))
                if start > end:
                    start, end = end, start
                selected.update(range(start, end + 1))
                continue
            if part.isdigit():
                selected.add(int(part))
        return selected

    def select_listed_pages(self) -> None:
        requested = self.parse_page_pick_text()
        visible = set(self.page_tree.get_children())
        matching = [str(number) for number in sorted(requested) if str(number) in visible]
        self.page_tree.selection_remove(self.page_tree.selection())
        if not matching:
            self.status_var.set("No typed page numbers were found in the current section.")
            self.detail_var.set("Type page numbers that are visible in this section, for example: 21, 23, 59-63.")
            return
        self.page_tree.selection_set(matching)
        self.page_tree.focus(matching[-1])
        self.page_tree.see(matching[-1])
        self.selected_page_number = int(matching[-1])
        self.status_var.set(f"Selected {len(matching)} exact page(s) in this section.")
        self.on_page_select()

    def retry_section(self) -> None:
        current = self.selected_section
        changed = 0
        for page in self.pages:
            if self.page_category(page) != current:
                continue
            next_slug = self.next_candidate_slug(page)
            if not next_slug:
                continue
            self.apply_category_to_page(page, next_slug, "Retried section using each page's next best candidate.")
            changed += 1
        save_manifest_dict(self.manifest_path, self.manifest)
        self.status_var.set(f"Retried {changed} page(s) from this section.")
        self.refresh_sections()

    def open_debug_folder(self) -> None:
        debug_folder = self.manifest.get("debug_folder") or str(self.result.debug_dir or "")
        if debug_folder:
            open_output_folder(Path(str(debug_folder)))

    def export_approved(self) -> None:
        self.status_var.set("Exporting approved PDFs...")
        thread = threading.Thread(target=self.run_export, daemon=True)
        thread.start()

    def run_export(self) -> None:
        try:
            export_from_manifest(
                self.manifest_path,
                skip_empty_pdfs=True,
                status_callback=lambda message: self.export_queue.put(("status", message)),
            )
            self.export_queue.put(("done", None))
        except Exception as exc:
            self.export_queue.put(("error", exc))

    def poll_export_queue(self) -> None:
        while True:
            try:
                kind, payload = self.export_queue.get_nowait()
            except queue.Empty:
                break
            if kind == "status":
                self.status_var.set(str(payload))
            elif kind == "done":
                self.status_var.set(f"Export complete. Approved PDFs are in {self.output_dir}")
                self.messagebox.showinfo("Floorplan Reader", f"Export complete.\n\nFolder:\n{self.output_dir}")
            elif kind == "error":
                self.status_var.set(f"Export failed: {payload}")
                self.messagebox.showerror("Floorplan Reader", str(payload))
        self.window.after(150, self.poll_export_queue)


class FloorpanReaderApp:
    def __init__(self) -> None:
        import tkinter as tk
        from tkinter import ttk

        self.tk = tk
        self.root = tk.Tk()
        self.root.title("Floorplan Reader")
        self.root.geometry("760x520")
        self.root.minsize(680, 480)
        self.root.configure(bg="#101820")

        self.messages: queue.Queue[tuple[str, object]] = queue.Queue()
        self.selected_pdf: Path | None = None
        self.last_output_dir: Path | None = None
        self.animation_running = False
        self.animation_frame = 0
        self.abort_requested = False
        self.worker_process: subprocess.Popen[str] | None = None

        self.status_text = tk.StringVar(value="Choose a construction plan-set PDF to begin.")
        self.file_text = tk.StringVar(value="No PDF selected")
        self.detail_text = tk.StringVar(value="Index-aware sorting is ready.")

        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("App.TFrame", background="#101820")
        style.configure("Panel.TFrame", background="#162332")
        style.configure("Title.TLabel", background="#101820", foreground="#F5F7FA", font=("Segoe UI", 24, "bold"))
        style.configure("Subtitle.TLabel", background="#101820", foreground="#9FB3C8", font=("Segoe UI", 10))
        style.configure("File.TLabel", background="#162332", foreground="#E7EDF4", font=("Segoe UI", 10))
        style.configure("Status.TLabel", background="#101820", foreground="#E7EDF4", font=("Segoe UI", 11, "bold"))
        style.configure("Detail.TLabel", background="#101820", foreground="#9FB3C8", font=("Segoe UI", 9))
        style.configure("Accent.TButton", font=("Segoe UI", 10, "bold"), padding=(16, 10))
        style.map(
            "Accent.TButton",
            background=[("active", "#37C7B5"), ("disabled", "#415066")],
            foreground=[("disabled", "#9FB3C8")],
        )
        style.configure("Horizontal.TProgressbar", troughcolor="#203044", background="#37C7B5")

        container = ttk.Frame(self.root, padding=26, style="App.TFrame")
        container.pack(fill="both", expand=True)
        container.columnconfigure(0, weight=1)
        container.rowconfigure(2, weight=1)

        title = ttk.Label(container, text="Floorplan Reader", style="Title.TLabel")
        title.grid(row=0, column=0, sticky="w")

        subtitle = ttk.Label(
            container,
            text="Reads cover sheets, sheet indexes, and plan pages before splitting the set.",
            style="Subtitle.TLabel",
        )
        subtitle.grid(row=1, column=0, sticky="w", pady=(4, 18))

        scan_panel = ttk.Frame(container, padding=14, style="Panel.TFrame")
        scan_panel.grid(row=2, column=0, sticky="nsew")
        scan_panel.columnconfigure(0, weight=1)
        scan_panel.rowconfigure(0, weight=1)

        self.scan_canvas = tk.Canvas(
            scan_panel,
            height=220,
            bg="#0D1724",
            highlightthickness=0,
            bd=0,
        )
        self.scan_canvas.grid(row=0, column=0, sticky="nsew")
        self.scan_canvas.bind("<Configure>", lambda _event: self.draw_scan_scene())

        self.file_label = ttk.Label(
            container,
            textvariable=self.file_text,
            wraplength=700,
            style="File.TLabel",
            padding=(14, 10),
        )
        self.file_label.grid(row=3, column=0, sticky="ew", pady=(16, 12))

        button_row = ttk.Frame(container, style="App.TFrame")
        button_row.grid(row=4, column=0, sticky="w", pady=(0, 16))

        self.choose_button = ttk.Button(
            button_row,
            text="Choose PDF",
            command=self.choose_pdf,
            style="Accent.TButton",
        )
        self.choose_button.pack(side="left")

        self.open_button = ttk.Button(
            button_row,
            text="Open Output Folder",
            command=self.open_last_output,
            state="disabled",
            style="Accent.TButton",
        )
        self.open_button.pack(side="left", padx=(10, 0))

        self.abort_button = ttk.Button(
            button_row,
            text="Abort Scan",
            command=self.abort_scan,
            state="disabled",
            style="Accent.TButton",
        )
        self.abort_button.pack(side="left", padx=(10, 0))

        self.progress = ttk.Progressbar(container, mode="indeterminate", style="Horizontal.TProgressbar")
        self.progress.grid(row=5, column=0, sticky="ew", pady=(0, 12))

        self.status_label = ttk.Label(container, textvariable=self.status_text, wraplength=700, style="Status.TLabel")
        self.status_label.grid(row=6, column=0, sticky="ew")

        footer = ttk.Label(
            container,
            textvariable=self.detail_text,
            style="Detail.TLabel",
        )
        footer.grid(row=7, column=0, sticky="w", pady=(6, 0))

        self.draw_scan_scene()
        self.root.after(100, self.poll_messages)

    def draw_scan_scene(self) -> None:
        canvas = self.scan_canvas
        width = max(canvas.winfo_width(), 500)
        height = max(canvas.winfo_height(), 200)
        canvas.delete("all")

        canvas.create_rectangle(0, 0, width, height, fill="#07111F", outline="")

        frame = self.animation_frame
        wave_offset = frame * 0.08 if self.animation_running else 0.0
        upper_wave = []
        lower_wave = []
        for step in range(0, width + 50, 50):
            y1 = 42 + math.sin(step * 0.018 + wave_offset) * 14
            y2 = height - 34 + math.cos(step * 0.015 + wave_offset * 0.8) * 18
            upper_wave.append((step, y1))
            lower_wave.append((step, y2))
        canvas.create_polygon(
            [(0, 0), *upper_wave, (width, 0)],
            fill="#0E2A3A",
            outline="",
            smooth=True,
        )
        canvas.create_polygon(
            [(0, height), *lower_wave, (width, height)],
            fill="#12364A",
            outline="",
            smooth=True,
        )

        for index in range(5):
            x = (frame * (2 + index) + index * 132) % (width + 180) - 90 if self.animation_running else index * width / 5
            y = 22 + (index % 3) * 43 + math.sin(frame * 0.05 + index) * 7
            canvas.create_line(x, y, x + 180, y + 34, fill="#244A63", width=8)
            canvas.create_line(x + 8, y - 2, x + 188, y + 32, fill="#5AD7E8", width=2)

        center_x = width // 2
        top = 30
        page_w = min(270, width - 170)
        page_h = min(158, height - 72)
        left = center_x - page_w // 2
        right = center_x + page_w // 2
        bottom = top + page_h

        shadow_shift = 14 + (math.sin(frame * 0.08) * 4 if self.animation_running else 0)
        canvas.create_rectangle(left + shadow_shift, top + 15, right + shadow_shift, bottom + 15, fill="#0B1A2B", outline="")
        canvas.create_rectangle(left + 9, top + 7, right + 9, bottom + 7, fill="#244158", outline="#6EAFC7", width=1)
        canvas.create_rectangle(left, top, right, bottom, fill="#EAF7FF", outline="#B8F1FF", width=2)
        canvas.create_line(left + 10, top + 12, right - 12, top + 12, fill="#FFFFFF", width=2)
        canvas.create_line(left + 14, top + 18, left + 14, bottom - 16, fill="#C7F5FF", width=2)

        title_y = top + 22
        canvas.create_text(left + 18, title_y, anchor="w", text="REVIEW-FIRST SCAN", fill="#17304A", font=("Segoe UI", 12, "bold"))
        for row in range(5):
            y = top + 48 + row * 19
            pulse = (math.sin(frame * 0.12 + row) + 1) / 2 if self.animation_running else 0.35
            accent = "#5AD7E8" if pulse > 0.5 else "#71E7C6"
            canvas.create_rectangle(left + 18, y, left + 74, y + 8, fill=accent, outline="")
            canvas.create_rectangle(left + 86, y, right - 22, y + 8, fill="#8AB4CF", outline="")

        if self.animation_running:
            span = max(page_h - 28, 1)
            scan_y = top + 18 + (frame * 4 % span)
            canvas.create_rectangle(left - 12, scan_y - 5, right + 12, scan_y + 5, fill="#91F5FF", outline="")
            canvas.create_line(left - 8, scan_y + 10, right + 8, scan_y + 10, fill="#D8FFF8", width=2)
            ribbon_y = bottom + 26
            points = []
            for step in range(0, page_w + 50, 18):
                points.append((left + step, ribbon_y + math.sin(step * 0.08 + frame * 0.18) * 8))
            canvas.create_line(*[coord for point in points for coord in point], fill="#71E7C6", width=4, smooth=True)
            canvas.create_text(
                center_x,
                height - 20,
                text="Building review previews and section candidates...",
                fill="#EAF7FF",
                font=("Segoe UI", 11, "bold"),
            )
        else:
            canvas.create_text(
                center_x,
                height - 20,
                text="Ready for a review-first scan",
                fill="#B8D8EA",
                font=("Segoe UI", 11, "bold"),
            )

    def start_scan_animation(self) -> None:
        if self.animation_running:
            return
        self.animation_running = True
        self.animation_frame = 0
        self.animate_scan()

    def animate_scan(self) -> None:
        if not self.animation_running:
            self.draw_scan_scene()
            return
        self.animation_frame += 1
        self.draw_scan_scene()
        self.progress.step(3)
        self.root.after(33, self.animate_scan)

    def stop_scan_animation(self) -> None:
        self.animation_running = False
        self.draw_scan_scene()
        self.progress["value"] = 0

    def choose_pdf(self) -> None:
        from tkinter import filedialog

        selected = filedialog.askopenfilename(
            title="Select construction plan-set PDF",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
        )
        if not selected:
            return

        self.selected_pdf = Path(selected)
        self.file_text.set(str(self.selected_pdf))
        self.last_output_dir = None
        self.abort_requested = False
        self.open_button.configure(state="disabled")
        self.choose_button.configure(state="disabled")
        self.abort_button.configure(state="normal")
        self.progress.start(12)
        self.status_text.set("Starting...")
        self.detail_text.set("Analyzing sheet numbers, titles, cover pages, and drawing indexes.")
        self.start_scan_animation()
        self.root.update_idletasks()

        self.root.after(125, self.start_worker_thread, self.selected_pdf)

    def start_worker_thread(self, pdf_path: Path) -> None:
        if self.selected_pdf != pdf_path:
            return
        if self.abort_requested:
            self.messages.put(("aborted", None))
            return
        self.messages.put(("status", "Starting the PDF reader engine..."))
        worker = threading.Thread(target=self.run_split, args=(pdf_path,), daemon=True)
        worker.start()

    def abort_scan(self) -> None:
        self.abort_requested = True
        self.abort_button.configure(state="disabled")
        self.status_text.set("Aborting scan...")
        self.detail_text.set("Stopping the reader engine. No approved PDFs will be exported.")
        process = self.worker_process
        if process is not None and process.poll() is None:
            try:
                process.terminate()
            except Exception:
                pass
            self.root.after(1500, self.force_kill_worker, process)
        else:
            self.messages.put(("aborted", None))

    def force_kill_worker(self, process: subprocess.Popen[str]) -> None:
        if self.abort_requested and process.poll() is None:
            try:
                process.kill()
            except Exception:
                pass

    def run_split(self, pdf_path: Path) -> None:
        try:
            if self.abort_requested:
                self.messages.put(("aborted", None))
                return
            process = subprocess.Popen(worker_command(pdf_path), **hidden_subprocess_kwargs())
            self.worker_process = process
            result: SplitResult | None = None

            assert process.stdout is not None
            for raw_line in process.stdout:
                if self.abort_requested:
                    if process.poll() is None:
                        process.terminate()
                    break
                line = raw_line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue

                kind = event.get("kind")
                if kind == "status":
                    self.messages.put(("status", event.get("message", "")))
                elif kind == "done":
                    result = SplitResult(
                        output_dir=Path(str(event["output_dir"])),
                        manifest_path=Path(str(event["manifest_path"])),
                        csv_path=Path(str(event["csv_path"])),
                        sheet_index_csv_path=Path(str(event["sheet_index_csv_path"])),
                        page_count=int(event["page_count"]),
                        debug_dir=Path(str(event.get("debug_dir", ""))) if event.get("debug_dir") else None,
                    )
                elif kind == "error":
                    raise RuntimeError(str(event.get("message", "The PDF reader engine stopped.")))

            stderr_text = ""
            if process.stderr is not None:
                stderr_text = process.stderr.read().strip()
            return_code = process.wait()
            self.worker_process = None

            if self.abort_requested:
                self.messages.put(("aborted", None))
                return
            if return_code != 0 and result is None:
                detail = stderr_text or f"The PDF reader engine exited with code {return_code}."
                raise RuntimeError(detail)
            if result is None:
                raise RuntimeError("The PDF reader engine ended before sending results.")

            self.messages.put(("done", result))
        except Exception as exc:
            self.worker_process = None
            if self.abort_requested:
                self.messages.put(("aborted", None))
            else:
                self.messages.put(("error", exc))

    def poll_messages(self) -> None:
        from tkinter import messagebox

        while True:
            try:
                kind, payload = self.messages.get_nowait()
            except queue.Empty:
                break

            if kind == "status":
                self.status_text.set(str(payload))
            elif kind == "done":
                result = payload
                assert isinstance(result, SplitResult)
                self.abort_requested = False
                self.last_output_dir = result.output_dir
                self.progress.stop()
                self.stop_scan_animation()
                self.choose_button.configure(state="normal")
                self.abort_button.configure(state="disabled")
                self.open_button.configure(state="normal")
                self.status_text.set(
                    f"Review ready. Read {result.page_count} pages. Nothing is exported until you approve it."
                )
                self.detail_text.set(
                    "Use the Review Manager to move pages, retry sections, and export approved PDFs."
                )
                ReviewManagerWindow(self.root, result)
            elif kind == "error":
                self.abort_requested = False
                self.progress.stop()
                self.stop_scan_animation()
                self.choose_button.configure(state="normal")
                self.abort_button.configure(state="disabled")
                self.open_button.configure(state="disabled")
                self.status_text.set(f"Error: {payload}")
                self.detail_text.set("The run stopped before outputs were completed.")
                messagebox.showerror("Floorplan Reader", str(payload))
            elif kind == "aborted":
                self.abort_requested = False
                self.worker_process = None
                self.progress.stop()
                self.stop_scan_animation()
                self.choose_button.configure(state="normal")
                self.abort_button.configure(state="disabled")
                self.open_button.configure(state="disabled")
                self.status_text.set("Scan aborted.")
                self.detail_text.set("Choose a PDF again when you are ready to restart the scan.")

        self.root.after(100, self.poll_messages)

    def open_last_output(self) -> None:
        if self.last_output_dir is not None:
            open_output_folder(self.last_output_dir)

    def run(self) -> int:
        self.root.mainloop()
        return 0


def run_gui() -> int:
    if fitz is None:
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Floorplan Reader",
            "PyMuPDF is required. Install it with: python -m pip install PyMuPDF",
        )
        root.destroy()
        return 1

    app = FloorpanReaderApp()
    return app.run()


def main(argv: list[str] | None = None) -> int:
    if fitz is None:
        print(
            "PyMuPDF is required. Install it with: python3 -m pip install PyMuPDF",
            file=sys.stderr,
        )
        return 1

    args = parse_args(argv or sys.argv[1:])
    if args.worker_json:
        return run_worker_json(args)

    if not args.cli and not args.pdf:
        return run_gui()

    pdf_path = Path(args.pdf).expanduser() if args.pdf else select_pdf_with_dialog()
    if pdf_path is None:
        print("No PDF selected.")
        return 1

    print(f"Reading: {pdf_path}")
    try:
        result = split_pdf(
            pdf_path,
            skip_empty_pdfs=args.skip_empty_pdfs,
            open_folder=args.open_folder,
            status_callback=print,
        )
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"Pages read: {result.page_count}")
    print(f"Manifest JSON: {result.manifest_path}")
    print(f"CSV index: {result.csv_path}")
    print(f"Extracted sheet index: {result.sheet_index_csv_path}")
    if result.debug_dir is not None:
        print(f"Debug folder: {result.debug_dir}")
    print(f"Output folder: {result.output_dir}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
