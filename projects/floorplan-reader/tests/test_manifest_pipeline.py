import json
import sys
import tempfile
import unittest
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from floorpan_reader import (  # noqa: E402
    CATEGORY_DOOR_SCHEDULES,
    CATEGORY_FLOOR_PLANS,
    CATEGORY_KITCHEN,
    CATEGORY_MEP_DETAIL,
    CATEGORY_OPENING_ELEVATIONS,
    CATEGORY_STOREFRONT_SCHEDULES,
    CATEGORY_STRUCTURAL_WIND,
    CATEGORY_VENDOR_DETAIL,
    CATEGORY_WINDOW_SCHEDULES,
    PageRecord,
    apply_correction_memory,
    category_slug,
    find_sheet_index_entry,
    prepare_review_package,
    export_from_manifest,
    parse_sheet_index_entries,
    save_manual_correction,
    sheet_lookup_key,
    split_pdf,
)


def add_title_block(page, sheet_number, title):
    page.insert_text((72, 92), f"Detail callout mentions door storefront window {sheet_number}", fontsize=8)
    page.insert_text((360, 500), "SHEET TITLE", fontsize=8)
    page.insert_text((360, 518), title, fontsize=13)
    page.insert_text((570, 560), "SHEET NUMBER", fontsize=8)
    page.insert_text((600, 580), sheet_number, fontsize=16)


def add_text_lines(page, lines, x=72, y=140, step=18, fontsize=10):
    for line in lines:
        page.insert_text((x, y), line, fontsize=fontsize)
        y += step


def create_sample_pdf(path: Path) -> None:
    doc = fitz.open()

    index = doc.new_page(width=792, height=612)
    add_text_lines(
        index,
        [
            "INDEX OF DRAWINGS",
            "ARCHITECTURAL SET",
            "A-101 GROUND FLOOR PLAN",
            "A-601 WINDOW SCHEDULE",
            "A-602 STOREFRONT SCHEDULE",
            "A-603 DOOR SCHEDULE",
            "A-201 EXTERIOR ELEVATIONS",
            "A-701 STOREFRONT ELEVATIONS",
            "STRUCTURAL SET",
            "S-1.12 WALL WIND PRESSURE DIAGRAM",
            "S-2.01 FOUNDATION PLAN",
            "MECHANICAL SET",
            "M-101 GROUND FLOOR PLAN",
            "VENDOR / DETAIL SET",
            "V-101 DOOR INSTALLATION DETAILS",
        ],
        y=60,
    )

    pages = [
        ("A-101", "GROUND FLOOR PLAN", ["ROOMS AND WALL LAYOUT"]),
        ("A-601", "WINDOW SCHEDULE", ["MARK SIZE GLASS TYPE FRAME REMARKS", "W1 36x60 IMPACT ALUM OK"]),
        ("A-602", "STOREFRONT SCHEDULE", ["OPENING MARK FRAME FINISH GLASS MAKEUP", "SF1 CLEAR ANODIZED LAMINATED"]),
        ("A-603", "DOOR SCHEDULE", ["MARK WIDTH HEIGHT TYPE FRAME HARDWARE", "101 3-0 7-0 HM HM HW-1"]),
        ("A-201", "EXTERIOR ELEVATIONS", ["FRONT ELEVATION", "REAR ELEVATION"]),
        ("A-701", "STOREFRONT ELEVATIONS", ["OPENING MARK SF1 SF2 ELEVATION DRAWINGS"]),
        ("S-1.12", "WALL WIND PRESSURE DIAGRAM", ["ZONE 4 ZONE 5 POSITIVE NEGATIVE PSF"]),
        ("S-1.13", "WALL PRESSURE CONTINUED", ["PRESSURE ZONES CONTINUED"]),
        ("S-2.01", "FOUNDATION PLAN", ["FOOTING SCHEDULE STRUCTURAL NOTES"]),
        ("M-101", "GROUND FLOOR PLAN", ["DUCTWORK AND DIFFUSER LAYOUT"]),
        ("V-101", "DOOR INSTALLATION DETAILS", ["DOOR ANCHOR DETAIL", "DOOR FASTENER SECTION"]),
        ("X-001", "MATERIAL BOARD", ["FINISH MATERIALS AND GENERAL ITEMS"]),
    ]
    for sheet_number, title, lines in pages:
        page = doc.new_page(width=792, height=612)
        add_title_block(page, sheet_number, title)
        add_text_lines(page, lines)

    doc.save(path)
    doc.close()


def add_table_rows(page, rows, x=72, y=150, col_width=82, row_height=18):
    for row_index, row in enumerate(rows):
        for col_index, value in enumerate(row):
            page.insert_text((x + col_index * col_width, y + row_index * row_height), value, fontsize=8)


def create_schedule_region_pdf(path: Path) -> None:
    doc = fitz.open()
    index = doc.new_page(width=792, height=612)
    add_text_lines(
        index,
        [
            "INDEX OF DRAWINGS",
            "ARCHITECTURAL SET",
            "A-801 SCHEDULES AND DETAILS",
            "A-802 STOREFRONT ELEVATIONS",
            "A-803 STOREFRONT SCHEDULE",
            "A-804 GLAZING NOTES",
            "A-805 GLAZING SCHEDULE",
            "A-806 HARDWARE SCHEDULE",
            "A-807 GLAZING SCHEDULE",
            "K-101 KITCHEN EQUIPMENT PLAN",
            "VENDOR / DETAIL SET",
            "V-201 FREEZER DOOR SPECIFICATIONS",
        ],
        y=60,
    )

    page = doc.new_page(width=792, height=612)
    add_title_block(page, "A-801", "SCHEDULES AND DETAILS")
    page.insert_text((72, 132), "DOOR SCHEDULE", fontsize=11)
    add_table_rows(
        page,
        [
            ["MARK", "WIDTH", "HEIGHT", "TYPE", "FRAME", "HARDWARE", "REMARKS"],
            ["100", "3-0", "7-0", "A", "HM", "HW-1", "LOBBY"],
            ["101", "3-0", "7-0", "B", "AL", "HW-2", "OFFICE"],
            ["200", "3-6", "7-0", "C", "HM", "HW-3", "STAIR"],
        ],
    )
    add_text_lines(page, ["DOOR HEAD DETAIL", "DOOR JAMB DETAIL", "DOOR THRESHOLD DETAIL"], x=72, y=260)

    page = doc.new_page(width=792, height=612)
    add_title_block(page, "A-802", "STOREFRONT ELEVATIONS")
    add_text_lines(page, ["SF-1 STOREFRONT ELEVATION", "GRAPHIC OPENING MARKS WITH DIMENSIONS", "NO SCHEDULE TABLE"], y=145)

    page = doc.new_page(width=792, height=612)
    add_title_block(page, "A-803", "STOREFRONT SCHEDULE")
    page.insert_text((72, 132), "ALUMINUM STOREFRONT SCHEDULE", fontsize=11)
    add_table_rows(
        page,
        [
            ["MARK", "WIDTH", "HEIGHT", "FRAME FINISH", "GLASS MAKEUP", "DOOR TYPE", "REMARKS"],
            ["SF-1", "12-0", "9-0", "CLEAR", "1 IMPACT", "PAIR", "ENTRY"],
            ["SF-2", "8-0", "8-0", "BRONZE", "1 IMPACT", "NONE", "LOBBY"],
        ],
    )

    page = doc.new_page(width=792, height=612)
    add_title_block(page, "A-804", "GLAZING NOTES")
    add_text_lines(page, ["GENERAL GLAZING NOTES", "ALL GLASS SHALL BE IMPACT RATED", "COORDINATE WITH STOREFRONT DETAILS"], y=145)

    page = doc.new_page(width=792, height=612)
    add_title_block(page, "A-805", "GLAZING SCHEDULE")
    page.insert_text((72, 132), "GLAZING SCHEDULE", fontsize=11)
    add_table_rows(
        page,
        [
            ["MARK", "TYPE", "WIDTH", "HEIGHT", "GLASS", "U-FACTOR", "SHGC", "REMARKS"],
            ["R-A", "FIXED", "3-0", "5-0", "LAM", "0.45", "0.25", "ROOM"],
            ["R-B", "FIXED", "4-0", "5-0", "LAM", "0.45", "0.25", "ROOM"],
        ],
    )

    page = doc.new_page(width=792, height=612)
    add_title_block(page, "A-806", "HARDWARE SCHEDULE")
    page.insert_text((72, 132), "HARDWARE SCHEDULE", fontsize=11)
    add_table_rows(
        page,
        [
            ["SET", "DOOR", "GROUP", "HARDWARE", "REMARKS"],
            ["HW-1", "100", "A", "HINGE LOCK CLOSER", "LOBBY"],
            ["HW-2", "101", "B", "HINGE LOCK STOP", "OFFICE"],
        ],
    )

    page = doc.new_page(width=792, height=612)
    add_title_block(page, "A-807", "GLAZING SCHEDULE")
    page.insert_text((72, 132), "GLAZING SCHEDULE", fontsize=11)
    add_table_rows(
        page,
        [
            ["MARK", "WIDTH", "HEIGHT", "FRAME FINISH", "GLASS MAKEUP", "SYSTEM", "REMARKS"],
            ["SF-3", "10-0", "9-0", "BLACK", "1 IMPACT", "ALUMINUM STOREFRONT", "ENTRY"],
            ["CW-1", "12-0", "10-0", "BRONZE", "1 IMPACT", "CURTAIN WALL", "LOBBY"],
        ],
    )

    page = doc.new_page(width=792, height=612)
    add_title_block(page, "K-101", "KITCHEN EQUIPMENT PLAN")
    add_text_lines(page, ["KITCHEN EQUIPMENT PLAN", "FOOD SERVICE EQUIPMENT", "TYPE I HOOD AND GREASE INTERCEPTOR"], y=145)

    page = doc.new_page(width=792, height=612)
    add_title_block(page, "V-201", "FREEZER DOOR SPECIFICATIONS")
    page.insert_text((72, 132), "FREEZER DOOR SPEC SHEET", fontsize=11)
    add_table_rows(
        page,
        [
            ["DOOR", "WIDTH", "HEIGHT", "TYPE", "FRAME", "HARDWARE"],
            ["FZ-1", "3-0", "7-0", "COOLER", "SS", "VENDOR"],
            ["FZ-2", "4-0", "8-0", "FREEZER", "SS", "VENDOR"],
        ],
    )

    doc.save(path)
    doc.close()


def create_small_no_index_pdf(path: Path) -> None:
    doc = fitz.open()

    page = doc.new_page(width=792, height=612)
    add_title_block(page, "A1", "GROUND FLOOR PLAN")
    add_text_lines(page, ["GROUND FLOOR PLAN", "ROOM LAYOUT AND WALLS"], y=145)

    page = doc.new_page(width=792, height=612)
    page.insert_text((72, 90), "SCHEDULES / DETAILS", fontsize=11)
    page.insert_text((72, 132), "DOOR SCHEDULE", fontsize=11)
    add_table_rows(
        page,
        [
            ["MARK", "WIDTH", "HEIGHT", "TYPE", "FRAME", "HARDWARE", "REMARKS"],
            ["100", "3-0", "7-0", "A", "HM", "HW-1", "ENTRY"],
            ["101", "3-0", "7-0", "B", "AL", "HW-2", "OFFICE"],
        ],
    )
    add_text_lines(page, ["DOOR JAMB DETAIL", "DOOR HEAD DETAIL"], x=72, y=230)

    page = doc.new_page(width=792, height=612)
    page.insert_text((72, 90), "STOREFRONT ELEVATION", fontsize=11)
    add_text_lines(page, ["SF-1 STOREFRONT ELEVATION", "GRAPHIC OPENING MARKS", "NO SCHEDULE TABLE"], y=145)

    page = doc.new_page(width=792, height=612)
    page.insert_text((72, 90), "FREEZER DOOR SPEC SHEET", fontsize=11)
    add_table_rows(
        page,
        [
            ["DOOR", "WIDTH", "HEIGHT", "TYPE", "FRAME", "HARDWARE"],
            ["FZ-1", "3-0", "7-0", "COOLER", "SS", "VENDOR"],
            ["FZ-2", "4-0", "8-0", "FREEZER", "SS", "VENDOR"],
        ],
        y=145,
    )

    page = doc.new_page(width=792, height=612)
    add_text_lines(page, ["GENERAL PROJECT NOTES", "COORDINATE ALL WORK", "REFER TO MANUFACTURER DATA"], y=90)

    doc.save(path)
    doc.close()


def create_large_index_pdf(path: Path) -> None:
    doc = fitz.open()
    index = doc.new_page(width=792, height=612)
    lines = ["INDEX OF DRAWINGS", "ARCHITECTURAL SET"]
    for number in range(101, 122):
        title = "GROUND FLOOR PLAN" if number == 101 else f"FLOOR PLAN AREA {number - 100}"
        lines.append(f"A-{number} {title}")
    add_text_lines(index, lines, y=50, step=16, fontsize=9)

    for number in range(101, 122):
        title = "GROUND FLOOR PLAN" if number == 101 else f"FLOOR PLAN AREA {number - 100}"
        page = doc.new_page(width=792, height=612)
        add_title_block(page, f"A-{number}", title)
        add_text_lines(page, [title, "ROOM LAYOUT AND WALLS"], y=145)

    doc.save(path)
    doc.close()


def create_index_guard_pdf(path: Path) -> None:
    doc = fitz.open()
    index = doc.new_page(width=792, height=612)
    add_text_lines(
        index,
        [
            "INDEX OF DRAWINGS",
            "ARCHITECTURAL SET",
            "A-101 GROUND FLOOR PLAN",
        ],
        y=60,
    )

    page = doc.new_page(width=792, height=612)
    add_title_block(page, "A-101", "GROUND FLOOR PLAN")
    page.insert_text((72, 132), "DOOR SCHEDULE", fontsize=11)
    add_table_rows(
        page,
        [
            ["MARK", "WIDTH", "HEIGHT", "TYPE", "FRAME", "HARDWARE", "REMARKS"],
            ["100", "3-0", "7-0", "A", "HM", "HW-1", "ENTRY"],
            ["101", "3-0", "7-0", "B", "AL", "HW-2", "OFFICE"],
            ["102", "3-6", "7-0", "C", "HM", "HW-3", "STAIR"],
        ],
    )

    doc.save(path)
    doc.close()


class ManifestPipelineTests(unittest.TestCase):
    def test_sheet_number_normalization_matches_formats(self):
        self.assertEqual(sheet_lookup_key("S1.12"), sheet_lookup_key("S-1.12"))
        self.assertEqual(sheet_lookup_key("S 1.12"), sheet_lookup_key("S-1.12"))
        self.assertEqual(sheet_lookup_key("A1.1"), sheet_lookup_key("A-1.1"))

    def test_fuzzy_index_match_handles_small_ocr_error(self):
        entries = parse_sheet_index_entries(["INDEX OF DRAWINGS", "S-1.12 WALL WIND PRESSURE DIAGRAM"], 1)
        entry, fuzzy = find_sheet_index_entry("S-I.12", entries)
        self.assertIsNotNone(entry)
        self.assertTrue(fuzzy)

    def test_metadata_first_manifest_and_expected_categories(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = Path(temp_dir) / "sample_construction_set.pdf"
            create_sample_pdf(pdf_path)

            result = split_pdf(pdf_path, skip_empty_pdfs=True)
            manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
            expected = json.loads(
                (ROOT / "tests" / "fixtures" / "expected_manifest_sample.json").read_text(encoding="utf-8")
            )["expected_categories_by_page"]

            actual = {
                str(page["pdf_page_number"]): page["category"]
                for page in manifest["pages"]
            }
            self.assertEqual(actual, expected)
            self.assertTrue(all("confidence" in page for page in manifest["pages"]))
            self.assertTrue(any(page["matched_index"] for page in manifest["pages"]))

    def test_large_plan_with_index_stays_metadata_first(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = Path(temp_dir) / "large_index_set.pdf"
            create_large_index_pdf(pdf_path)
            result = split_pdf(pdf_path, skip_empty_pdfs=True)
            manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))

            self.assertFalse(manifest["analysis"]["small_plan_mode"])
            self.assertGreaterEqual(manifest["analysis"]["sheet_index_entry_count"], 20)
            self.assertTrue(all(page["top_candidates"] for page in manifest["pages"]))
            self.assertTrue(any(page["matched_index"] for page in manifest["pages"]))

    def test_drawing_index_blocks_conflicting_schedule_region(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = Path(temp_dir) / "index_guard_set.pdf"
            create_index_guard_pdf(pdf_path)
            result = split_pdf(pdf_path, skip_empty_pdfs=True)
            manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
            page = next(item for item in manifest["pages"] if item["sheet_number"] == "A-101")

            self.assertTrue(page["matched_index"])
            self.assertEqual(page["category"], category_slug(CATEGORY_FLOOR_PLANS))
            self.assertNotEqual(page["category"], category_slug(CATEGORY_DOOR_SCHEDULES))
            self.assertTrue(page["needs_manual_review"])
            self.assertIn("drawing index", page["reason"].lower())

    def test_detail_sheet_mentions_door_but_is_not_door_schedule(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = Path(temp_dir) / "sample_construction_set.pdf"
            create_sample_pdf(pdf_path)
            result = split_pdf(pdf_path, skip_empty_pdfs=True)
            manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
            vendor_page = next(page for page in manifest["pages"] if page["sheet_number"] == "V-101")

            self.assertEqual(vendor_page["category"], category_slug(CATEGORY_MEP_DETAIL))
            self.assertNotEqual(vendor_page["category"], category_slug(CATEGORY_DOOR_SCHEDULES))

    def test_structural_wind_continuation_is_caught(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = Path(temp_dir) / "sample_construction_set.pdf"
            create_sample_pdf(pdf_path)
            result = split_pdf(pdf_path, skip_empty_pdfs=True)
            manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
            page = next(page for page in manifest["pages"] if page["sheet_number"] == "S-1.13")

            self.assertEqual(page["category"], category_slug(CATEGORY_STRUCTURAL_WIND))
            self.assertIn("Neighbor continuation", page["reason"])

    def test_schedule_regions_are_classified_independently(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = Path(temp_dir) / "schedule_region_set.pdf"
            create_schedule_region_pdf(pdf_path)
            result = split_pdf(pdf_path, skip_empty_pdfs=True)
            manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))

            regions = manifest["regions"]
            categories = {region["region_category"] for region in regions}

            self.assertIn("door_schedule_table", categories)
            self.assertIn("door_detail", categories)
            self.assertIn("storefront_schedule_table", categories)
            self.assertIn("storefront_elevation", categories)
            self.assertIn("glazing_schedule_table", categories)
            self.assertIn("hardware_schedule_table", categories)
            self.assertIn("general_notes", categories)
            self.assertIn("vendor_detail_sheet", categories)
            storefront_glazing_region = next(
                item for item in regions
                if item["sheet_number"] == "A-807" and item["region_category"] == "storefront_schedule_table"
            )
            self.assertIn("storefront", storefront_glazing_region["reason"].lower())

            for category in {
                "door_schedule_table",
                "storefront_schedule_table",
                "glazing_schedule_table",
                "hardware_schedule_table",
            }:
                region = next(item for item in regions if item["region_category"] == category)
                self.assertIn("pdf_page_number", region)
                self.assertIn("sheet_number", region)
                self.assertIn("sheet_title", region)
                self.assertIn("region_bbox", region)
                self.assertIn("confidence", region)
                self.assertIn("reason", region)
                self.assertIn("extracted_rows", region)
                self.assertGreaterEqual(region["confidence"], 0.75)
                self.assertTrue(region["extracted_rows"])

    def test_schedule_pages_follow_detected_schedule_tables_only(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = Path(temp_dir) / "schedule_region_set.pdf"
            create_schedule_region_pdf(pdf_path)
            result = split_pdf(pdf_path, skip_empty_pdfs=True)
            manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
            pages = {page["sheet_number"]: page for page in manifest["pages"]}

            self.assertEqual(pages["A-801"]["category"], category_slug(CATEGORY_DOOR_SCHEDULES))
            self.assertEqual(pages["A-802"]["category"], category_slug(CATEGORY_OPENING_ELEVATIONS))
            self.assertEqual(pages["A-803"]["category"], category_slug(CATEGORY_STOREFRONT_SCHEDULES))
            self.assertEqual(pages["A-805"]["category"], category_slug(CATEGORY_WINDOW_SCHEDULES))
            self.assertEqual(pages["A-806"]["category"], category_slug(CATEGORY_DOOR_SCHEDULES))
            self.assertEqual(pages["A-807"]["category"], category_slug(CATEGORY_STOREFRONT_SCHEDULES))
            self.assertEqual(pages["K-101"]["category"], category_slug(CATEGORY_KITCHEN))
            self.assertEqual(pages["V-201"]["category"], category_slug(CATEGORY_VENDOR_DETAIL))
            self.assertNotEqual(pages["A-802"]["category"], category_slug(CATEGORY_STOREFRONT_SCHEDULES))
            self.assertNotEqual(pages["V-201"]["category"], category_slug(CATEGORY_DOOR_SCHEDULES))

            glazing_notes = pages["A-804"]
            self.assertNotEqual(glazing_notes["category"], category_slug(CATEGORY_WINDOW_SCHEDULES))

    def test_small_plan_mode_outputs_candidates_debug_and_manual_review(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = Path(temp_dir) / "small_no_index_set.pdf"
            create_small_no_index_pdf(pdf_path)
            result = split_pdf(pdf_path, skip_empty_pdfs=True)
            manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))

            self.assertTrue(manifest["analysis"]["small_plan_mode"])
            self.assertTrue(Path(manifest["debug_folder"]).exists())
            self.assertTrue((Path(manifest["debug_folder"]) / "confidence_report.json").exists())
            self.assertTrue((Path(manifest["debug_folder"]) / "manual_review_list.json").exists())
            self.assertTrue((Path(manifest["debug_folder"]) / "manual_review_report.html").exists())

            for page in manifest["pages"]:
                self.assertIn("top_candidates", page)
                self.assertTrue(page["top_candidates"])
                self.assertIn("evidence_scores", page)
                self.assertIn("table_structure_score", page["evidence_scores"])
                self.assertIn("debug_files", page)

            pages = {page["pdf_page_number"]: page for page in manifest["pages"]}
            self.assertEqual(pages[2]["category"], category_slug(CATEGORY_DOOR_SCHEDULES))
            self.assertEqual(pages[3]["category"], category_slug(CATEGORY_OPENING_ELEVATIONS))
            self.assertNotEqual(pages[3]["category"], category_slug(CATEGORY_STOREFRONT_SCHEDULES))
            self.assertTrue(any(page["needs_manual_review"] for page in manifest["pages"]))

    def test_review_package_exports_only_after_approval_step(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = Path(temp_dir) / "review_first_set.pdf"
            create_schedule_region_pdf(pdf_path)

            result = prepare_review_package(pdf_path)
            self.assertTrue(result.manifest_path.exists())
            self.assertFalse((result.output_dir / CATEGORY_DOOR_SCHEDULES).exists())

            manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
            page = next(item for item in manifest["pages"] if item["sheet_number"] == "A-802")
            page["category"] = category_slug(CATEGORY_STOREFRONT_SCHEDULES)
            page["selected_category"] = category_slug(CATEGORY_STOREFRONT_SCHEDULES)
            result.manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

            export_from_manifest(result.manifest_path, skip_empty_pdfs=True)
            self.assertTrue((result.output_dir / CATEGORY_STOREFRONT_SCHEDULES).exists())

    def test_correction_memory_learns_from_similar_future_pages(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            future_pdf = temp_path / "future.pdf"
            memory_path = temp_path / "floorplan_reader_corrections.json"
            page_features = {
                "sheet_number": "A-802",
                "sheet_prefix": "A",
                "sheet_title": "STOREFRONT ELEVATION",
                "title_tokens": ["elevation", "storefront"],
                "original_category": category_slug(CATEGORY_STOREFRONT_SCHEDULES),
                "top_candidate_categories": [
                    category_slug(CATEGORY_STOREFRONT_SCHEDULES),
                    category_slug(CATEGORY_OPENING_ELEVATIONS),
                ],
                "region_categories": ["storefront_elevation"],
            }
            save_manual_correction(
                temp_path / "old.pdf",
                3,
                category_slug(CATEGORY_STOREFRONT_SCHEDULES),
                category_slug(CATEGORY_OPENING_ELEVATIONS),
                "This is an elevation, not a schedule.",
                memory_path=memory_path,
                page_features=page_features,
            )

            record = PageRecord(
                page_index=0,
                original_page_number=1,
                sheet_number="A-902",
                sheet_title="STOREFRONT ELEVATION",
                drawing_set="ARCHITECTURAL SET",
                discipline_prefix="A",
                detected_discipline="architectural",
                raw_title_block_text="STOREFRONT ELEVATION",
                matched_index=False,
                confidence=0.78,
                reason="Initial storefront schedule guess.",
                needs_manual_review=False,
                matched_keywords=[],
                category_files=[CATEGORY_STOREFRONT_SCHEDULES],
                sheet_title_source="page text",
                index_source_page=None,
                regions=[],
                evidence_scores={},
                top_candidates=[
                    {"category": category_slug(CATEGORY_STOREFRONT_SCHEDULES), "score": 0.78},
                    {"category": category_slug(CATEGORY_OPENING_ELEVATIONS), "score": 0.70},
                ],
                small_plan_mode=True,
                debug_files={},
            )

            updated = apply_correction_memory([record], future_pdf)
            self.assertEqual(updated[0].category_files[0], CATEGORY_OPENING_ELEVATIONS)
            self.assertIn("learned correction", updated[0].reason.lower())


if __name__ == "__main__":
    unittest.main()
