"""Read-only macOS PDF context detection. No third-party dependencies."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import unicodedata
from urllib.parse import unquote, urlsplit

SCRIPT = r'''
on run argv
    set readerName to item 1 of argv
    set separatorChar to character id 0
    tell application "System Events"
        if not (exists application process readerName) then return "not_running"
        tell application process readerName
            set processID to unix id
            set isFront to frontmost
            if not (exists window 1) then return "no_window"
            set selectedWindow to window 1
            try
                set selectedWindow to value of attribute "AXFocusedWindow"
            end try
            set windowTitle to name of selectedWindow
            set documentURL to ""
            try
                set documentURL to value of attribute "AXDocument" of selectedWindow
                if documentURL is missing value then set documentURL to ""
            end try
            return (processID as text) & separatorChar & (isFront as text) & separatorChar & windowTitle & separatorChar & documentURL
        end tell
    end tell
end run
'''

class DetectionError(Exception):
    pass

def run(command):
    try:
        return subprocess.run(command, capture_output=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise DetectionError(str(exc)) from exc

def snapshot(app):
    result = run(['/usr/bin/osascript', '-e', SCRIPT, app])
    if result.returncode:
        raise DetectionError(result.stderr.decode('utf-8', 'replace').strip())
    raw = result.stdout.decode('utf-8').removesuffix('\n')
    if raw in ('not_running', 'no_window'):
        return {'status': raw}
    parts = raw.split('\0')
    if len(parts) != 4:
        raise DetectionError('Unexpected window metadata response.')
    pid, frontmost, title, document = parts
    return dict(pid=int(pid), frontmost=frontmost == 'true', title=title, document=document)

def pdf_path(value):
    if value.startswith('file:'):
        url = urlsplit(value)
        if url.netloc not in ('', 'localhost'):
            return None
        value = unquote(url.path)
    path = Path(value)
    if not path.is_absolute() or path.suffix.lower() != '.pdf':
        return None
    try:
        if not path.is_file():
            return None
        with path.open('rb') as stream:
            if b'%PDF-' not in stream.read(1024):
                return None
        return str(path.resolve())
    except OSError:
        return None

def parse_lsof(data):
    paths = set()
    for field in data.split(b'\0'):
        field = field.lstrip(b'\n')
        if field.startswith(b'n/'):
            path = pdf_path(os.fsdecode(field[1:]))
            if path:
                paths.add(path)
    return sorted(paths)

def normalize(value):
    return unicodedata.normalize('NFC', value)

def match_title(title, candidates, app):
    titles = {normalize(title)}
    for suffix in (' — ' + app, ' - ' + app):
        if title.endswith(suffix):
            titles.add(normalize(title[:-len(suffix)]))
    matches = [p for p in candidates if normalize(Path(p).name) in titles]
    if not matches:
        matches = [p for p in candidates if normalize(Path(p).stem) in titles]
    # PDF Expert prefixes edited documents with '* '. Prefer literal names first.
    if not matches and title.startswith('* '):
        return match_title(title[2:], candidates, app)
    if len(matches) == 1:
        return 'high', matches[0], matches
    return ('ambiguous' if matches else 'not_found'), None, matches or candidates

def detect(app='PDF Expert', require_frontmost=False):
    output = dict(schema_version=1, app=app, match='not_found', path=None, candidates=[])
    before = snapshot(app)
    output.update(before)
    output.pop('document', None)
    if 'status' in before:
        return output
    if require_frontmost and not before['frontmost']:
        return dict(output, status='reader_not_frontmost')
    direct = pdf_path(before['document']) if before['document'] else None
    if direct:
        output.update(match='exact', path=direct, source='AXDocument')
    else:
        files = run(['/usr/sbin/lsof', '-nP', '-a', '-p', str(before['pid']), '-Fn0'])
        if files.returncode not in (0, 1) or (files.returncode == 1 and files.stderr):
            raise DetectionError(files.stderr.decode('utf-8', 'replace') or 'Cannot inspect open files.')
        quality, path, candidates = match_title(before['title'], parse_lsof(files.stdout), app)
        output.update(match=quality, path=path, candidates=candidates, source='window_title+lsof')
    # Avoid returning a path if the user switched documents during inspection.
    if snapshot(app) != before:
        output.update(match='not_found', path=None, candidates=[], status='window_changed_retry')
    else:
        output['status'] = 'ok' if output['path'] else output['match']
    return output

def main(argv=None):
    parser = argparse.ArgumentParser(description='Identify the selected local PDF without uploading it.')
    parser.add_argument('--json', action='store_true', help='Emit structured results, including failures')
    parser.add_argument('--app', choices=['PDF Expert', 'Preview'], default='PDF Expert')
    parser.add_argument('--require-frontmost', action='store_true')
    args = parser.parse_args(argv)
    try:
        if sys.platform != 'darwin':
            raise DetectionError('Live detection requires macOS.')
        result = detect(args.app, args.require_frontmost)
    except DetectionError as exc:
        result = dict(schema_version=1, app=args.app, match='not_found', path=None,
                      status='detection_error', error=str(exc), candidates=[],
                      hint='Check System Settings → Privacy & Security → Accessibility and Automation for the app launching this command. Run again from Terminal if needed.')
    if args.json:
        print(json.dumps(result, ensure_ascii=False))
    elif result.get('path'):
        print(result['path'])
    else:
        print(json.dumps(result, ensure_ascii=False), file=sys.stderr)
    return 0 if result.get('path') else (2 if result.get('match') == 'ambiguous' else 1)

if __name__ == '__main__':
    sys.exit(main())
