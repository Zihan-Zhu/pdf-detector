import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'plugins/pdf-detector/skills/current-pdf/scripts'))
import pdf_detect as d

class DetectorTests(unittest.TestCase):
    def test_duplicates_are_ambiguous(self):
        self.assertEqual(d.match_title('paper.pdf', ['/a/paper.pdf', '/b/paper.pdf'], 'PDF Expert')[0], 'ambiguous')
    def test_edited_document_marker(self):
        self.assertEqual(d.match_title('* paper', ['/a/paper.pdf'], 'PDF Expert')[1], '/a/paper.pdf')
        self.assertEqual(d.match_title('* paper.pdf', ['/a/* paper.pdf', '/a/paper.pdf'], 'PDF Expert')[1], '/a/* paper.pdf')
    def test_home_does_not_select_only_open_pdf(self):
        self.assertIsNone(d.match_title('Home', ['/a/paper.pdf'], 'PDF Expert')[1])
    def test_unicode_and_suffix(self):
        self.assertEqual(d.match_title('研究 — PDF Expert', ['/a/研究.pdf'], 'PDF Expert')[:2], ('high', '/a/研究.pdf'))
    def test_nul_paths_and_pdf_validation(self):
        with tempfile.TemporaryDirectory() as root:
            p = Path(root) / 'a\nb 研究.pdf'
            p.write_bytes(b'%PDF-1.7\n')
            self.assertEqual(d.parse_lsof(b'p123\0\nn' + bytes(p) + b'\0\n'), [str(p.resolve())])
            self.assertEqual(d.pdf_path(p.as_uri()), str(p.resolve()))
            p.write_text('not a PDF')
            self.assertIsNone(d.pdf_path(str(p)))
    def test_switch_clears_result(self):
        a = dict(pid=123, frontmost=False, title='a.pdf', document='/a.pdf')
        b = dict(a, title='b.pdf')
        with patch.object(d, 'snapshot', side_effect=[a,b]), patch.object(d, 'pdf_path', return_value='/a.pdf'):
            result = d.detect()
        self.assertIsNone(result['path'])
        self.assertEqual(result['status'], 'window_changed_retry')
    def test_frontmost_policy(self):
        with patch.object(d, 'snapshot', return_value=dict(pid=1, frontmost=False, title='x', document='')):
            self.assertEqual(d.detect(require_frontmost=True)['status'], 'reader_not_frontmost')
    def test_no_reader(self):
        with patch.object(d, 'snapshot', return_value={'status':'not_running'}):
            self.assertIsNone(d.detect()['path'])

if __name__ == '__main__':
    unittest.main()
