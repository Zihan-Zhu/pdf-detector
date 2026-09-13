"""Compatibility entry point; implementation is bundled inside the shared skill."""
from pathlib import Path
import runpy

if __name__ == '__main__':
    runpy.run_path(str(Path(__file__).resolve().parent / 'plugins/pdf-detector/skills/current-pdf/scripts/pdf_detect.py'), run_name='__main__')
