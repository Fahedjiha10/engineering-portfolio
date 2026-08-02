# Detailed Project Catalog

## 1. Floorplan Reader

**Location:** `01_Featured_Projects/Floorplan_Reader`

**What it is:** A Python desktop tool for reading construction-plan PDFs, finding sheet-index entries, classifying drawing pages, splitting/exporting PDFs, preparing review packages, and remembering manual corrections. The folder includes source, a small `.pyw` launcher, PyInstaller packaging metadata, tests/fixtures, documentation, and a Windows executable.

**Technologies evidenced:** Python, PyMuPDF/`fitz`, PDF parsing, regex/text heuristics, manifest generation, Tkinter-style desktop packaging, PyInstaller, JSON fixtures, and `unittest`.

**Verification:** Both source files and both test copies pass Python bytecode compilation. The principal test suite ran 12 tests successfully in 23.282 seconds using the original project environment.

**Assessment:** Strongest portfolio item. It has a concrete user problem, nontrivial document-processing logic, an executable deliverable, regression tests, and documentation. Before public release, remove the duplicated nested `tests/tests` copy and add representative before/after screenshots.

## 2. ESP8266 MQTT / Losant IoT Firmware

**Location:** `02_Hardware_Embedded_and_Electrical/ESP8266_MQTT_IoT`

**What it is:** A progression of Arduino sketches from introductory MQTT connectivity to Losant-connected telemetry, including temperature/humidity evidence and course reports.

**Technologies evidenced:** ESP8266/Arduino C++, Wi-Fi, MQTT, Losant device authentication, JSON payloads, sensor telemetry, and serial diagnostics.

**Security treatment:** Two sketches contained live-looking Wi-Fi/cloud credentials. Every credential declaration found in the portfolio copies was replaced with `<REDACTED_FOR_PORTFOLIO>`; originals were not modified. Those credentials should be rotated in Losant and on the relevant Wi-Fi network if still active.

**Assessment:** Good embedded/IoT story because it shows a learning progression and evidence of a working dashboard. Improve it by consolidating the sketches into one clean repository, adding a wiring diagram/BOM, and documenting the exact sensor and board model.

## 3. Everglades Rescue Game

**Location:** `01_Featured_Projects/Everglades_Rescue_Game`

**What it is:** A C++ console game using a 5Ã—5 map, ranger/tourist objectives, hazards, user decisions, and a countdown/resource mechanic. The archive contains the revised Visual Studio solution and IPO/design documentation.

**Technologies evidenced:** C++, arrays, structs, functions, menus, state transitions, random events, input validation, and Visual Studio project organization.

**Verification:** The revised source passes `g++ -std=c++17 -fsyntax-only`.

**Authorship:** The documentation calls this a group project and lists Fahed Jiha, Kerweins Astre, Xzavian Patrick, and Kavencci Saint Jean. Public portfolio text must identify Fahed's specific contribution rather than implying sole authorship.

**Assessment:** Strong coursework item with more depth than the smaller calculators. Add a gameplay capture and a short contribution statement.

## 4. FPGA Smart Parking Garage Counter

**Location:** `projects/fpga-smart-parking` and `02_Hardware_Embedded_and_Electrical/FPGA_Smart_Parking_Garage`

**What it is:** An individual EEL4740 VHDL-2008 parking-capacity controller implemented for the Zybo Z7-20. Switches set capacity, reset loads it, debounced buttons simulate entry and exit events, LD0-LD3 show remaining spaces, and RGB LD5 indicates available or full status.

**Technologies evidenced:** VHDL-2008, FPGA, Zybo Z7-20, Vivado, finite-state machines, input synchronization, debouncing, edge-to-pulse conversion, bounded counters, PWM, XDC constraints, Tcl automation, and self-checking simulation.

**Completion status:** Completed Summer 2026. The retained evidence includes synthesizable VHDL, a self-checking testbench, project-specific constraints, simulation and build scripts, a generated bitstream, timing/utilization/DRC reports, and successful hardware-programming evidence. The testbench passed its functional and boundary cases; implementation met timing at +3.967 ns WNS and 0.000 ns TNS.

**Assessment:** One of the strongest hardware portfolio projects because it shows the complete FPGA flow from behavioral design and verification through constraints, implementation, timing closure, bitstream generation, and board programming. A public hardware demonstration video would be the best remaining addition.

## 5. Al Tallow Website

**Location:** `01_Featured_Projects/Al_Tallow_Website`

**What it is:** A compact two-page site prototype with shared styling, JavaScript behavior, a product page, a README, and a visual mockup.

**Technologies evidenced:** HTML, CSS, vanilla JavaScript, responsive/front-end layout, and simple asset management.

**Assessment:** Useful web sample, but its portfolio value depends on whether the branding/content is authorized for public use. Add screenshots, accessibility checks, mobile QA, and deployment instructions.

## 6. Python Hangman

**Location:** `01_Featured_Projects/Python_Hangman`

**What it is:** A console Hangman game with validated single-letter input, guessed-letter tracking, mistake limits, win/loss handling, and external word-list support. Code and output screenshots are included.

**Verification:** The source passes Python bytecode compilation.

**Known gap:** The source expects `words.txt`, but that supporting file was not found alongside the project. Add a licensed sample word list or a built-in fallback before publishing it as immediately runnable.

## 7. Deal Scout

**Location:** `01_Featured_Projects/Deal_Scout`

**What it is:** A self-contained web interface plus PowerShell server scripts for displaying and serving deal information locally.

**Technologies evidenced:** HTML/CSS/JavaScript, local HTTP serving, PowerShell, RSS/data handling, and UI state management.

**Assessment:** Visually substantial and practical, but generated during an AI-assisted Codex task. Present it transparently as AI-assisted and be prepared to explain the code, data flow, and security model.

## 8. RIMS State-Machine Coursework

**Location:** `02_Hardware_Embedded_and_Electrical/RIMS_State_Machine_Coursework`

**What it is:** A broad EEL4730 archive of C implementations, RIMS `.sm` machine files, assignment reports, and sequential/state-machine exercises.

**Technologies evidenced:** Embedded C, synchronous state machines, timers, PWM, frequency measurement, latches, and RIMS simulation.

**Assessment:** Valuable technical evidence but too broad to present raw. Select two or three strongest assignments, add state diagrams and demo captures, and keep `Reference_Samples` explicitly separated from authored work.

## 9. FPGA and Zybo Z7 Coursework

**Location:** `02_Hardware_Embedded_and_Electrical/FPGA_and_Zybo_Z7_Coursework`

**What it is:** EEL4740 assignment documents for custom processors and Vivado/Vitis bare-metal work, a Zybo Z7 constraints file, and scripts/logs used to detect/configure the Digilent Zybo Z7-20 board in Vivado.

**Technologies evidenced:** Vivado, Vitis, Zynq/Zybo Z7, AXI GPIO, ARM bare-metal concepts, Tcl automation, and constraint management.

**Assessment:** Strong supporting evidence, but the available assignment documents may combine instructions with student screenshots. Review each page before public use and distinguish completed work from supplied course material. The board-setup utilities are AI-assisted.

## 10. Circuit and Computer-Architecture Labs

**Location:** `02_Hardware_Embedded_and_Electrical/Circuit_and_Computer_Architecture_Labs`

**What it is:** Selected EEL3110C and EEL4709C reports, including multiple circuit labs and a final Lab 3 report.

**Technologies evidenced:** Circuit analysis, laboratory measurement/reporting, and computer-architecture coursework.

**Assessment:** Good evidence for electrical/computer-engineering breadth. Public presentation should extract one-page summaries with objective, schematic, measurements, error analysis, and conclusions.

## 11. Digital Design Research

**Location:** `02_Hardware_Embedded_and_Electrical/Digital_Design_Research`

**What it is:** The latest/final-labeled EEL3712 research-paper copy located during the scan.

**Assessment:** Include only after checking citations, team/instructor details, and whether the paper is original individual work.

## 12. C++ Visual Studio Coursework Archive

**Location:** `03_Software_Coursework_Archive/Visual_Studio_CPP`

**What it is:** Clean copies of 27 Visual Studio project folders, restricted to source, solution, project metadata, and selected documentation. Compiled binaries, PDBs, `.vs`, `x64`, Debug, and Release folders were excluded.

**Notable programs:** Course Summary App, iMobile calculator, loan calculator, paint estimator, Everglades variants, Lo Shu magic-square validators, soccer roster tool, stock-trade calculator, rectangular-solid calculator, and introductory exercises.

**Verification sample:** Everglades Revised, Course Summary, iMobile Calculator, Paint Estimator, Lo Shu Project 4, Soccer, and StockTrade passed C++17 syntax checks. The most developed loan-calculator version failed because `pow` is used without including `<cmath>`.

**Assessment:** Use as an archive, not as a single polished project. Several folders are duplicates, empty experiments, or early revisions. Promote only programs you can demonstrate and clean up.

## 13. Software Design Documentation

**Location:** `03_Software_Coursework_Archive/Software_Design_Documentation`

**What it is:** A window-quote class diagram, a COP2210 project proposal, and a completed Assignment 7 document produced from recent coursework materials.

**Assessment:** Review for correctness and personal information before publishing. Pair design diagrams with source code if that code exists elsewhere.

## 14. Unreal First-Person Prototype

**Location:** `04_Prototype_and_Experimental_Work/Unreal_First_Person_Prototype`

**What it is:** A curated snapshot of the newer of two near-duplicate Unreal Engine projects. It includes project/configuration files, first-person/weapon assets, level-prototyping content, and external actor/object data.

**Exclusions:** Approximately 2.9 GB per project of `StorageHouse` and `StarterContent` assets were omitted, along with caches, autosaves, logs, and the older near-duplicate project. These are predominantly template/marketplace or generated assets and would obscure personal contribution.

**Assessment:** Low authorship confidence until custom changes are identified in the Unreal Editor. Do not claim template assets as original work.

## 15. Word COM Automation Prototype

**Location:** `04_Prototype_and_Experimental_Work/Word_COM_Automation_Prototype`

**What it is:** A C++ experiment intended to automate opening/printing a Word service-report document via Windows COM.

**Known issues:** The source appears incomplete/nonportable: it references Word types without visible generated imports, uses suspicious `IDispatch::InvokeHelper` calls, and embeds an unescaped local path. Treat it as an experiment, not a working deliverable.
