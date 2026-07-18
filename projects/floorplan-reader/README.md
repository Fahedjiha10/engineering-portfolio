# Floorplan Reader

Python desktop/CLI tool that organizes construction plan-set PDFs. It extracts page text and title-block clues, classifies architectural and engineering sheets, exports category PDFs and CSV/JSON manifests, prepares review packages, remembers corrections, and never edits the source PDF.

```bash
python -m venv .venv
python -m pip install -r requirements.txt
python floorpan_reader.py input.pdf --output output
```

The retained suite contains 12 tests covering parsing, classification, manifests, correction memory, splitting, and exports; all previously passed. Executables, bytecode, and duplicate tests are excluded.
