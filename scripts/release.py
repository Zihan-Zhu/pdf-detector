"""Version synchronization, validation and deterministic release packaging."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = Path('plugins/pdf-detector')
MANIFESTS = [PLUGIN / '.codex-plugin/plugin.json', PLUGIN / '.claude-plugin/plugin.json', Path('.claude-plugin/marketplace.json')]

def version(root=ROOT):
    value = (root / 'VERSION').read_text().strip()
    if not re.fullmatch(r'(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)', value):
        raise ValueError('VERSION must be a stable semantic version X.Y.Z')
    return value

def check(root=ROOT, tag=None):
    value = version(root)
    if tag is not None and tag != 'v' + value:
        raise ValueError(f'Tag {tag!r} does not match v{value}')
    for relative in MANIFESTS:
        manifest = json.loads((root / relative).read_text())
        if manifest['name'] != 'pdf-detector' or manifest['version'] != value:
            raise ValueError(f'Manifest drift: {relative}')
        if 'plugins' in manifest:
            entry = manifest['plugins'][0]
            if entry['version'] != value or entry['source'] != './plugins/pdf-detector':
                raise ValueError('Claude marketplace drift')
    marketplace = json.loads((root / '.agents/plugins/marketplace.json').read_text())
    entry = marketplace['plugins'][0]
    if entry['source'] != {'source':'local', 'path':'./plugins/pdf-detector'}:
        raise ValueError('Codex marketplace source drift')
    if entry['name'] != 'pdf-detector' or entry['policy'] != {'installation':'AVAILABLE','authentication':'ON_INSTALL'}:
        raise ValueError('Invalid Codex marketplace entry')
    if f'## [{value}]' not in (root / 'CHANGELOG.md').read_text():
        raise ValueError('Add a CHANGELOG entry before releasing')
    for relative in ['LICENSE', 'README.md', str(PLUGIN / 'skills/current-pdf/SKILL.md'), str(PLUGIN / 'skills/current-pdf/scripts/pdf_detect.py')]:
        if not (root / relative).is_file():
            raise ValueError(f'Missing {relative}')
    return value

def bump(value, root=ROOT):
    if not re.fullmatch(r'(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)', value):
        raise ValueError('Expected stable semantic version X.Y.Z')
    if tuple(map(int, value.split('.'))) <= tuple(map(int, version(root).split('.'))):
        raise ValueError('New version must increase')
    manifests = [(path, json.loads((root / path).read_text())) for path in MANIFESTS]
    for path, data in manifests:
        data['version'] = value
        for entry in data.get('plugins', []):
            entry['version'] = value
        (root / path).write_text(json.dumps(data, indent=2) + '\n')
    (root / 'VERSION').write_text(value + '\n')

def write_zip(target, entries):
    with zipfile.ZipFile(target, 'w', compression=zipfile.ZIP_STORED) as archive:
        for name, data, executable in sorted(entries):
            info = zipfile.ZipInfo(name, date_time=(2026,1,1,0,0,0))
            info.create_system = 3
            info.external_attr = (0o100755 if executable else 0o100644) << 16
            archive.writestr(info, data)

def build(root=ROOT, dist=None):
    value = check(root)
    dist = dist or root / 'dist'
    dist.mkdir(parents=True, exist_ok=True)
    entries = []
    for relative in [Path('README.md'), Path('LICENSE'), Path('CHANGELOG.md'), Path('VERSION'), Path('pdf-detect')]:
        entries.append((str(relative), (root / relative).read_bytes(), relative.name == 'pdf-detect'))
    for directory in [PLUGIN, Path('.agents'), Path('.claude-plugin')]:
        for file in sorted((root / directory).rglob('*')):
            if file.is_file() and '__pycache__' not in file.parts and file.suffix != '.pyc' and file.name != '.DS_Store':
                entries.append((file.relative_to(root).as_posix(), file.read_bytes(), False))
    archive = dist / f'pdf-detector-{value}.zip'
    write_zip(archive, [('pdf-detector/' + name, data, mode) for name,data,mode in entries])
    skill = dist / f'current-pdf-{value}.skill'
    prefix = (PLUGIN / 'skills/current-pdf').as_posix() + '/'
    skill_entries = [('current-pdf/' + name[len(prefix):], data, mode) for name,data,mode in entries if name.startswith(prefix)]
    skill_entries.append(('current-pdf/LICENSE', (root/'LICENSE').read_bytes(), False))
    write_zip(skill, skill_entries)
    (dist / 'SHA256SUMS').write_text(''.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}\n' for p in [archive, skill]))
    return archive, skill

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('check').add_argument('--tag')
    sub.add_parser('bump').add_argument('version')
    sub.add_parser('build')
    args = parser.parse_args()
    try:
        if args.command == 'check': print('Validated', check(tag=args.tag))
        elif args.command == 'bump': bump(args.version); print('Updated versions; add a CHANGELOG entry next.')
        else:
            for path in build(): print(path)
    except (ValueError, KeyError, OSError) as exc:
        parser.exit(1, str(exc) + '\n')

if __name__ == '__main__': main()
