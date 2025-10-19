import subprocess
import sys

from splurge_sql_generator import __version__


def test_cli_version_output():
    """Run the CLI module with --version and assert output contains the package version."""
    # Use the -m module invocation to exercise the argparse version action
    proc = subprocess.run(
        [sys.executable, "-m", "splurge_sql_generator.cli", "--version"],
        capture_output=True,
        text=True,
        check=False,
    )

    # argparse's version action prints to stdout and exits with code 0
    assert proc.returncode == 0
    assert f"splurge-sql-generator {__version__}" in proc.stdout.strip()
