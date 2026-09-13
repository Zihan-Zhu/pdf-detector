# AI integration

Install the native Codex or Claude Code plugin using the instructions in [README.md](README.md).
The shared [current-pdf skill](plugins/pdf-detector/skills/current-pdf/SKILL.md) resolves its bundled detector relative to its installed location, so it works across machines and plugin caches.

For another local agent with command execution and PDF reading, run `python3 "<absolute checkout path>/plugins/pdf-detector/skills/current-pdf/scripts/pdf_detect.py" --json` on demand. Follow the result-handling contract in the skill. Remote chat environments cannot inspect your Mac through this script.
