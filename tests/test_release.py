import hashlib
import importlib.util
from pathlib import Path
import shutil
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('release', ROOT / 'scripts/release.py')
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)

class ReleaseTests(unittest.TestCase):
    def test_tag_must_match(self):
        self.assertEqual(r.check(tag='v'+r.version()), r.version())
        with self.assertRaises(ValueError): r.check(tag='v99.0.0')
    def test_archives_reproducible_and_self_contained(self):
        with tempfile.TemporaryDirectory() as tmp:
            a = r.build(dist=Path(tmp)/'a')
            b = r.build(dist=Path(tmp)/'b')
            self.assertEqual([p.read_bytes() for p in a], [p.read_bytes() for p in b])
            with zipfile.ZipFile(a[0]) as z:
                self.assertIn('pdf-detector/plugins/pdf-detector/.claude-plugin/plugin.json', z.namelist())
                self.assertTrue(all('__pycache__' not in n for n in z.namelist()))
            with zipfile.ZipFile(a[1]) as z:
                self.assertIn('current-pdf/scripts/pdf_detect.py', z.namelist())
            sums = (a[0].parent/'SHA256SUMS').read_text()
            for p in a: self.assertIn(hashlib.sha256(p.read_bytes()).hexdigest(), sums)
    def test_bump_requires_increase_and_syncs_manifests(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'repo'
            shutil.copytree(ROOT, root, ignore=shutil.ignore_patterns('.git','dist','__pycache__'))
            with self.assertRaises(ValueError): r.bump(r.version(root), root)
            r.bump('99.0.0', root)
            with self.assertRaises(ValueError): r.check(root)
            with (root/'CHANGELOG.md').open('a') as f: f.write('\n## [99.0.0]\n')
            self.assertEqual(r.check(root), '99.0.0')
