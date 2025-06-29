import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
import shutil
import pytest

SCRIPT = os.path.join(os.path.dirname(__file__), '..', 'jpy_sql_generator', 'cli.py')


def run_cli(args, input_sql=None):
    cmd = [sys.executable, SCRIPT] + args
    if input_sql:
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".sql") as f:
            f.write(input_sql)
            fname = f.name
        args = [fname] + args[1:]
        cmd = [sys.executable, SCRIPT] + args
    result = subprocess.run(cmd, capture_output=True, text=True)
    if input_sql:
        os.remove(fname)
    return result


def test_cli_help():
    result = subprocess.run(
        [sys.executable, SCRIPT, "--help"],
        capture_output=True,
        text=True,
    )
    assert "usage" in result.stdout.lower()
    assert result.returncode == 0


def test_cli_missing_file():
    result = run_cli(['not_a_file.sql'])
    assert result.returncode != 0
    assert 'Error: SQL file not found' in result.stderr


def test_cli_wrong_extension(tmp_path):
    with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".txt") as f:
        f.write("SELECT 1;")
        fname = f.name
    try:
        result = run_cli([fname])
        assert "doesn't have .sql extension" in result.stderr
    finally:
        os.remove(fname)


def test_cli_dry_run(tmp_path):
    sql = """# TestClass
#get_foo
SELECT 1;
    """
    with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".sql") as f:
        f.write(sql)
        fname = f.name
    try:
        result = run_cli([fname, "--dry-run"])
        assert "class TestClass" in result.stdout
        assert "def get_foo" in result.stdout
        assert result.returncode == 0
    finally:
        os.remove(fname)


def test_cli_non_sql_extension(tmp_path):
    file = tmp_path / 'foo.txt'
    file.write_text('# TestClass\n# test_method\nSELECT 1;')
    result = run_cli([str(file)])
    # Should warn but still run
    assert 'Warning: File' in result.stderr
    assert result.returncode == 0
    # Should report generated file
    assert 'TestClass.py' in result.stdout


def test_cli_output_dir(tmp_path):
    sql_file = tmp_path / 'bar.sql'
    sql_file.write_text('# TestClass\n# test_method\nSELECT 1;')
    outdir = tmp_path / 'outdir'
    result = run_cli([str(sql_file), '-o', str(outdir)])
    assert result.returncode == 0
    assert outdir.exists()
    py_file = outdir / 'TestClass.py'
    assert py_file.exists()
    assert 'class TestClass' in py_file.read_text()


def test_cli_report_generated_classes(tmp_path):
    sql_file = tmp_path / 'baz.sql'
    sql_file.write_text('# TestClass\n# test_method\nSELECT 1;')
    outdir = tmp_path / 'outdir2'
    result = run_cli([str(sql_file), '-o', str(outdir)])
    assert result.returncode == 0
    assert f'Generated 1 Python classes:' in result.stdout
    assert 'TestClass.py' in result.stdout


if __name__ == "__main__":
    unittest.main()
