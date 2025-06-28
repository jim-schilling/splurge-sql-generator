import unittest
import subprocess
import sys
import tempfile
import os
from pathlib import Path

class TestCLI(unittest.TestCase):
    def run_cli(self, args, input_sql=None):
        cmd = [sys.executable, '-m', 'jpy_sql_generator.cli'] + args
        if input_sql:
            with tempfile.NamedTemporaryFile('w+', delete=False, suffix='.sql') as f:
                f.write(input_sql)
                fname = f.name
            args = [fname] + args[1:]
            cmd = [sys.executable, '-m', 'jpy_sql_generator.cli'] + args
        result = subprocess.run(cmd, capture_output=True, text=True)
        if input_sql:
            os.remove(fname)
        return result

    def test_cli_help(self):
        result = subprocess.run([sys.executable, '-m', 'jpy_sql_generator.cli', '--help'], capture_output=True, text=True)
        self.assertIn('usage', result.stdout.lower())
        self.assertEqual(result.returncode, 0)

    def test_cli_missing_file(self):
        result = self.run_cli(['nonexistent_file.sql'], input_sql=None)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Error: SQL file not found', result.stderr)

    def test_cli_wrong_extension(self):
        with tempfile.NamedTemporaryFile('w+', delete=False, suffix='.txt') as f:
            f.write('SELECT 1;')
            fname = f.name
        try:
            result = subprocess.run([sys.executable, '-m', 'jpy_sql_generator.cli', fname], capture_output=True, text=True)
            self.assertIn("doesn't have .sql extension", result.stderr)
        finally:
            os.remove(fname)

    def test_cli_dry_run(self):
        sql = """# TestClass
#get_foo
SELECT 1;
        """
        with tempfile.NamedTemporaryFile('w+', delete=False, suffix='.sql') as f:
            f.write(sql)
            fname = f.name
        try:
            result = subprocess.run([sys.executable, '-m', 'jpy_sql_generator.cli', fname, '--dry-run'], capture_output=True, text=True)
            self.assertIn('class TestClass', result.stdout)
            self.assertIn('def get_foo', result.stdout)
            self.assertEqual(result.returncode, 0)
        finally:
            os.remove(fname)

if __name__ == '__main__':
    unittest.main() 