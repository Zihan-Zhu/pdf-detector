# PDF Detector

Ask **“Summarize the paper I’m reading”** in Codex or Claude Code, without dragging in the PDF.

PDF Detector identifies the selected local document in PDF Expert on your Mac, even after you switch to your AI app. The bundled skill then asks the host to read that file. Multiple open tabs are supported when the selected title uniquely identifies an observable file; ambiguous matches are reported instead of guessed.

**macOS · Python 3.9+ · no third-party Python dependencies · no background service**

## Install in Codex

```sh
codex plugin marketplace add Zihan-Zhu/pdf-detector
```

Open `/plugins`, install **PDF Detector** from the `pdf-detector` marketplace, and start a new session. In the desktop app, refresh/restart if the newly added marketplace is not visible.

Ask naturally, or invoke the skill:

```text
$current-pdf summarize the paper I’m reading
```

## Install in Claude Code

```text
/plugin marketplace add Zihan-Zhu/pdf-detector
/plugin install pdf-detector@pdf-detector
/reload-plugins
/pdf-detector:current-pdf summarize the paper I’m reading
```

For local development, start `claude --plugin-dir ./plugins/pdf-detector` from a checkout.

This release supports **Claude Code with local command/file access**. It is not a Claude web chat integration, and it does not provide a Claude Desktop MCP server. A `.skill` archive cannot access your Mac when executed in a remote sandbox.

## First use

1. Keep the intended document selected in PDF Expert.
2. Switch to Codex or Claude Code and ask about the current PDF.
3. If macOS requests it, allow the launching app to control System Events. Check **System Settings → Privacy & Security → Accessibility** and **Automation → System Events** for that app.

Terminal and each AI host can require separate permissions. Sandboxed command execution may need the host's approval to access macOS automation. PDF read permission is separate from detection. The plugin never changes permissions or uploads files itself; the host processes document text according to its normal configuration.

## CLI

From a cloned repository or extracted plugin ZIP:

```sh
./pdf-detect --json
./pdf-detect
./pdf-detect --app Preview --json
./pdf-detect --require-frontmost --json
```

The default is PDF Expert’s selected window, even when it is behind another app. It does not remember a previous tab after you select another one. Preview uses the same interface but has not been live-verified.

JSON includes `path`, `match`, `source`, `status`, `app`, and available window metadata. Plain output is an absolute path on success. Exit codes: **0** identified; **1** unavailable/error; **2** ambiguous.

## How detection works

1. Read the reader’s focused window (or first window) and its `AXDocument` attribute.
2. If a readable local PDF URL is available, return `exact`.
3. Otherwise inspect the reader process’s open files using NUL-separated `lsof` output. Match the complete filename or stem to the selected window title, including PDF Expert’s observed edited-document marker. A unique match is `high`.
4. Recheck window metadata to reject a result if the document changed during detection.

The file must be readable and contain a PDF header. There is no filesystem-wide search or fuzzy matching. `high` is an inference, not a guarantee: readers may close file descriptors after loading or use metadata titles unrelated to filenames. Duplicate matches are ambiguous. Unmatched Home/settings windows return no result. Cloud files must be locally readable. Unsaved annotations may differ from the on-disk PDF your AI reads.

Current-page detection, selection extraction, browser PDFs, and continuous monitoring are future work. A live PDF Expert check succeeded among multiple open PDFs; host installation and end-to-end model behavior still depend on each host's permissions and PDF tools.

## Development and release control

```sh
python3 scripts/release.py check
python3 -m unittest discover -s tests -v
python3 scripts/release.py build
```

`VERSION` is canonical. Manifest versions must match it. CI tests Python 3.9 and 3.13 on Linux and macOS; the tests mock desktop automation and do not require a GUI session. Builds emit a self-contained plugin ZIP, a portable `.skill` bundle, and `SHA256SUMS` in `dist/`. ZIP timestamps and permissions are fixed for reproducibility.

To release:

```sh
python3 scripts/release.py bump 0.1.1
# Add a 0.1.1 entry to CHANGELOG.md, then test and commit the changes.
python3 scripts/release.py check
python3 -m unittest discover -s tests -v
git add VERSION CHANGELOG.md plugins/pdf-detector/.codex-plugin/plugin.json plugins/pdf-detector/.claude-plugin/plugin.json .claude-plugin/marketplace.json
git commit -m "Release v0.1.1"
git push origin main
# Wait for CI to pass before tagging.
git tag -a v0.1.1 -m "PDF Detector v0.1.1"
git push origin v0.1.1
```

The tag workflow checks version consistency and tests on both operating systems before publishing archives and checksums to GitHub Releases. Never move an existing release tag; publish a new patch version. Marketplace installs track the registered repository revision; publishing a tag does not automatically pin marketplace users to it. For a reproducible local install, check out the desired tag and register that checkout as a local marketplace.

## License and references

Copyright © 2026 Zihan Zhu. Licensed under [CC BY-NC 4.0](LICENSE), matching [CS Paper Toolkit](https://github.com/Zihan-Zhu/cs-paper-toolkit), whose dual-host packaging and release conventions informed this project.

- [Codex plugin packaging](https://developers.openai.com/plugins/build/plugins)
- [Claude Code plugin reference](https://code.claude.com/docs/en/plugins-reference)
- [Claude Code marketplaces](https://code.claude.com/docs/en/plugin-marketplaces)
- [Apple AXDocument attribute](https://developer.apple.com/documentation/applicationservices/kaxdocumentattribute?language=objc)
