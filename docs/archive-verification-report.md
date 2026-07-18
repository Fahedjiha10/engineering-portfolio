# Verification Report

Verification was performed on the curated copies on July 16, 2026.

## Passed checks

- Portfolio inventory after curation: 410 project files, approximately 160.48 MB, before adding audit documents.
- Credential scan: zero unredacted matches for discovered Wi-Fi/Losant credential declarations, common OpenAI key patterns, and simple password assignments.
- Python compilation: Floorplan Reader source/launcher, both Floorplan test copies, and Hangman all passed `py_compile` using the bundled Python runtime.
- Floorplan Reader: 12 `unittest` tests passed in 23.282 seconds using the original project's dependency environment.
- C++17 syntax checks passed for Everglades Revised, Course Summary, iMobile Calculator, Paint Estimator, Lo Shu Project 4, Soccer, and StockTrade.
- Originals were copied rather than moved; source locations remain intact.

## Failed or incomplete checks

- The developed loan-calculator source failed `g++ -std=c++17 -fsyntax-only` because `pow` is used without including `<cmath>`.
- The Word COM automation prototype was not compiled and contains visible portability/correctness concerns.
- Arduino firmware was not compiled because board cores and project-specific library versions were not validated in this task.
- FPGA assignments were not synthesized or implemented because project-specific HDL/Vivado projects were not found.
- Unreal assets were not opened in Unreal Editor; authorship and runtime behavior remain unverified.
- Hangman expects a `words.txt` file that was not located with the project.
- The Al Tallow and Deal Scout interfaces were retained as source but were not browser-tested during this filesystem curation pass.

## Reproducibility notes

- The portfolio file inventory contains SHA-256 hashes for integrity checking.
- Floorplan's packaged `.exe` is included as found; it was not rebuilt during this task.
- Firmware credentials were sanitized only in portfolio copies. Hashes therefore intentionally differ from the originals for those files.
