# Development

Runtime code lives in plugins/pdf-detector/skills/current-pdf/scripts/pdf_detect.py.
Run `python3 scripts/release.py check` and `python3 -m unittest discover -s tests -v` before release.
VERSION is canonical. Use `python3 scripts/release.py bump X.Y.Z` to synchronize package versions, then add a changelog entry. Never retag a published release.
Keep detection read-only, preserve ambiguity, and keep private paths and PDF content out of fixtures and release artifacts.
