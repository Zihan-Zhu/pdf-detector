# Changelog

Versions follow Semantic Versioning. Changes are recorded before tagging a release.

## [0.1.2] - 2026-09-13

### Fixed
- Require direct reading of the detected local PDF in Codex and Claude Code.
- Use computer use only when explicitly requested, never as an automatic reading fallback.
- Explain unavailable or failed direct reading without guessing from window metadata.
- Clarify that local PDF page rendering is distinct from screen capture.

## [0.1.1] - 2026-09-13

### Fixed
- Distinguish unavailable automation, Apple Events refusal, assistive-access refusal, and other failures.
- Request one host-approved retry for sandboxed automation failures without claiming macOS denied permission.
- Stop retries after refusal or repeated failure; do not fall back to another computer-use channel.
- Preserve original errors and add structured recovery fields with regression coverage.

## [0.1.0] - 2026-09-13

### Added
- Shared current-PDF skill for Codex and Claude Code with native marketplace manifests.
- Read-only macOS detection through document URLs and conservative window-title matching.
- PDF Expert support, optional Preview adapter, structured errors, and ambiguity handling.
- Portable CLI, unit tests, release version checks, reproducible archives, and SHA-256 checksums.
- CI on macOS and Linux and tag-triggered GitHub releases.
