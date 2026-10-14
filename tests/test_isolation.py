import subprocess
import sys
from pathlib import Path
import tempfile
import unittest


class IsolationTests(unittest.TestCase):
    def test_core_imports_with_no_site_packages_and_no_files_created(self):
        source = str(Path(__file__).resolve().parents[1] / "src")
        program = """
import importlib
import pathlib
import sys
sys.path.insert(0, sys.argv[1])
modules = ['', '.config', '.logging', '.tasks', '.storage', '.http', '.notify', '.browser', '.ai', '.dingtalk', '.dingtalk_work']
for suffix in modules:
    importlib.import_module('ecommerce_automation' + suffix)
assert not list(pathlib.Path.cwd().iterdir())
from ecommerce_automation.errors import MissingDependencyError
from ecommerce_automation.http import HttpClient
try:
    HttpClient('https://example.test')
except MissingDependencyError as error:
    assert '[http]' in str(error)
else:
    raise AssertionError('Optional dependency should not be present')
print('isolated import passed')
"""
        with tempfile.TemporaryDirectory() as directory:
            completed = subprocess.run(
                [sys.executable, "-S", "-B", "-c", program, source], cwd=directory,
                capture_output=True, text=True, check=False,
            )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)


if __name__ == "__main__":
    unittest.main()
