# Exclusions, Security, and Curation Decisions

## Excluded from the final portfolio

- IDE/build material: `.vs`, `.venv`, `venv`, `__pycache__`, Debug, Release, `x64`, `obj`, `bin`, build caches, test caches, PDBs, and most generated binaries.
- Third-party Arduino libraries, including the bundled ArduinoJson tree.
- Installed applications, SDKs, games, emulator data, telemetry logs, personal finance/business files, and unrelated schoolwork.
- The downloaded/cloned `claw-code` repository because available evidence did not establish it as original work.
- Unreal `StorageHouse` and `StarterContent` trees, caches, autosaves, crash dumps, and the older near-duplicate prototype. This avoided copying roughly 6 GB of mostly template/marketplace content.
- Duplicate smart-parking proposal copy containing a student PID; the otherwise equivalent copy without that field was retained.
- A file named `application passwords.txt` and all unrelated credentials/private records.

## Credential handling

Live-looking Losant access secrets and Wi-Fi credentials were detected in two Arduino sketches. In the portfolio copies, SSID, Wi-Fi password, Losant device ID, access key, and access secret declarations were replaced with `<REDACTED_FOR_PORTFOLIO>`. The original sketches remain unchanged.

Recommended action: rotate the Losant credentials and the corresponding Wi-Fi password if they are still active. Redaction prevents portfolio disclosure but does not invalidate credentials already exposed elsewhere.

## Privacy review still required before public upload

- Inspect PDFs, Word documents, screenshots, and Unreal metadata for student IDs, personal email addresses, collaborator names, instructor names, local paths, private dashboard URLs, and school portal information.
- Confirm that website branding/images and Unreal marketplace assets can be redistributed.
- Add contribution statements for every group or AI-assisted project.
- Do not publish the whole coursework archive as-is; select the strongest items and remove supplied assignment instructions when they are not part of the authored work.
