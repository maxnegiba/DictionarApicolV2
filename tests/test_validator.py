import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]

class ValidatorTests(unittest.TestCase):
    def test_example_record_has_both_editions_and_is_not_approved(self):
        r = json.loads((ROOT / "data/records/TER-0001.json").read_text())
        self.assertEqual(set(r["editions"]), {"ro", "en"})
        self.assertNotEqual(r["status"], "APPROVED")
    def test_structural_validator_passes(self):
        p = subprocess.run([sys.executable, str(ROOT / "scripts/validate.py")], capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)

if __name__ == "__main__":
    unittest.main()
