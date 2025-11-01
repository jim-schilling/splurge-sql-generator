import re
import subprocess
import sys
from pathlib import Path

from tests.unit.test_utils import create_basic_schema, create_sql_with_schema


def run_cli(args: list[str]) -> subprocess.CompletedProcess:
    """Run the CLI as a module rather than as a script."""
    return subprocess.run([sys.executable, "-m", "splurge_sql_generator.cli", *args], capture_output=True, text=True)


def test_end_to_end_single_file_output_dir(tmp_path: Path):
    sql = """# UserRepo
#get_user
SELECT * FROM users WHERE id = :user_id;
"""
    sql_file, schema_file = create_sql_with_schema(tmp_path, "user.sql", sql, create_basic_schema("users"))

    outdir = tmp_path / "out"
    proc = run_cli([str(sql_file), "-o", str(outdir), "--schema", str(schema_file)])

    assert proc.returncode == 0, proc.stderr
    assert (outdir / "user_repo.py").exists()
    assert "Generated 1 Python classes" in proc.stdout


def test_end_to_end_multiple_files_single_schema(tmp_path: Path):
    # Shared schema referenced via --schema
    shared_schema = tmp_path / "shared.schema"
    shared_schema.write_text(create_basic_schema("users"))

    sql1 = """# Aaa
#get
SELECT * FROM users;
"""
    sql2 = """# Bbb
#get
SELECT * FROM users;
"""

    f1, _ = create_sql_with_schema(tmp_path, "a.sql", sql1, create_basic_schema("users"))
    f2, _ = create_sql_with_schema(tmp_path, "b.sql", sql2, create_basic_schema("users"))

    outdir = tmp_path / "out2"
    proc = run_cli([str(f1), str(f2), "-o", str(outdir), "--schema", str(shared_schema)])

    assert proc.returncode == 0, proc.stderr
    assert (outdir / "aaa.py").exists()
    assert (outdir / "bbb.py").exists()
    assert re.search(r"Generated \d+ Python classes?", proc.stdout)


def test_end_to_end_dry_run_prints_code(tmp_path: Path):
    sql = """# DryRun
#get
SELECT 1;
"""
    sql_file, schema_file = create_sql_with_schema(tmp_path, "dry.sql", sql, create_basic_schema("dummy"))
    proc = run_cli([str(sql_file), "--dry-run", "--schema", str(schema_file)])

    assert proc.returncode == 0, proc.stderr
    assert "class DryRun" in proc.stdout
    assert "def get(" in proc.stdout


def test_cli_generate_types_creates_file(tmp_path: Path):
    # Run --generate-types with explicit file path in tmp directory
    types_path = tmp_path / "my_types.yaml"
    proc = run_cli(["--generate-types", str(types_path)])

    assert proc.returncode == 0, proc.stderr
    assert types_path.exists()
    assert "Generated SQL type mapping file:" in proc.stdout
