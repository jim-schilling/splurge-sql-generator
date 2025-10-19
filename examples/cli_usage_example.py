#!/usr/bin/env python3
"""
CLI Usage Example for splurge-sql-generator

This example demonstrates how to use the splurge-sql-generator via the command line interface.
It shows various CLI options and how to integrate CLI usage into Python scripts.
"""

import logging
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from sqlalchemy import create_engine, text

# Add the project root to the path so we can import from 'output' and the package
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)


def setup_logging():
    """Configure logging to see the class-level logger in action."""
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def run_cli_command(args: list[str]) -> tuple[int, str, str]:
    """
    Run the splurge-sql-generator CLI command.

    Args:
        args: List of command line arguments

    Returns:
        Tuple of (return_code, stdout, stderr)
    """
    cmd = [sys.executable, "-m", "splurge_sql_generator.cli"] + args
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr


def demonstrate_cli_help():
    """Demonstrate CLI help functionality."""
    print("=== CLI Help Demonstration ===")

    return_code, stdout, stderr = run_cli_command(["--help"])

    print(f"Return code: {return_code}")
    print("Help output:")
    print(stdout)
    print()


def demonstrate_dry_run():
    """Demonstrate CLI dry-run functionality."""
    print("=== CLI Dry-Run Demonstration ===")

    # Use the User.sql example
    sql_file = os.path.join(PROJECT_ROOT, "examples", "User.sql")

    return_code, stdout, stderr = run_cli_command([sql_file, "--dry-run"])

    print(f"Return code: {return_code}")
    if return_code == 0:
        print("Generated code (dry-run):")
        print(stdout)
    else:
        print("Error:")
        print(stderr)
    print()


def demonstrate_output_directory():
    """Demonstrate CLI output directory functionality."""
    print("=== CLI Output Directory Demonstration ===")

    # Create a temporary directory for output
    with tempfile.TemporaryDirectory() as temp_dir:
        sql_file = os.path.join(PROJECT_ROOT, "examples", "User.sql")

        return_code, stdout, stderr = run_cli_command([sql_file, "-o", temp_dir])

        print(f"Return code: {return_code}")
        if return_code == 0:
            print("Generated files:")
            print(stdout)

            # List generated files
            output_files = list(Path(temp_dir).glob("*.py"))
            print(f"Files created in {temp_dir}:")
            for file_path in output_files:
                print(f"  - {file_path.name}")
                # Show first few lines of generated file
                with open(file_path) as f:
                    lines = f.readlines()[:10]
                    print("    First 10 lines:")
                    for line in lines:
                        print(f"      {line.rstrip()}")
        else:
            print("Error:")
            print(stderr)
    print()


def demonstrate_multiple_files():
    """Demonstrate CLI multiple files functionality."""
    print("=== CLI Multiple Files Demonstration ===")

    # Create a temporary directory for output
    with tempfile.TemporaryDirectory() as temp_dir:
        # Use multiple SQL files
        sql_files = [
            os.path.join(PROJECT_ROOT, "examples", "User.sql"),
            os.path.join(PROJECT_ROOT, "examples", "ProductRepository.sql"),
            os.path.join(PROJECT_ROOT, "examples", "OrderService.sql"),
        ]

        return_code, stdout, stderr = run_cli_command(sql_files + ["-o", temp_dir])

        print(f"Return code: {return_code}")
        if return_code == 0:
            print("Generated files:")
            print(stdout)

            # List generated files
            output_files = list(Path(temp_dir).glob("*.py"))
            print(f"Files created in {temp_dir}:")
            for file_path in output_files:
                print(f"  - {file_path.name}")
        else:
            print("Error:")
            print(stderr)
    print()


def demonstrate_custom_sql_types():
    """Demonstrate CLI custom SQL types functionality."""
    print("=== CLI Custom SQL Types Demonstration ===")

    # Create a temporary custom SQL types file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        custom_types = """
# Custom SQL type mappings
CUSTOM_INT: int
CUSTOM_STRING: str
CUSTOM_BOOL: bool
CUSTOM_FLOAT: float
CUSTOM_JSON: dict
"""
        f.write(custom_types)
        custom_types_file = f.name

    try:
        # Create a temporary SQL file with custom types
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sql", delete=False) as f:
            sql_content = """# CustomTypeExample
#get_custom_data
SELECT id, name, is_active, data FROM custom_table WHERE type = :type;
"""
            f.write(sql_content)
            sql_file = f.name

        # Create a temporary directory for output
        with tempfile.TemporaryDirectory() as temp_dir:
            return_code, stdout, stderr = run_cli_command([sql_file, "-o", temp_dir, "--types", custom_types_file])

            print(f"Return code: {return_code}")
            if return_code == 0:
                print("Generated files with custom SQL types:")
                print(stdout)
            else:
                print("Error:")
                print(stderr)

    finally:
        # Clean up temporary files
        os.unlink(custom_types_file)
        os.unlink(sql_file)

    print()


def demonstrate_strict_mode():
    """Demonstrate CLI strict mode functionality."""
    print("=== CLI Strict Mode Demonstration ===")

    # Try to process a non-SQL file with strict mode
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("This is not a SQL file")
        non_sql_file = f.name

    try:
        return_code, stdout, stderr = run_cli_command([non_sql_file, "--strict"])

        print(f"Return code: {return_code}")
        print("Strict mode error (expected):")
        print(stderr)

        # Now try without strict mode
        return_code, stdout, stderr = run_cli_command([non_sql_file])

        print(f"\nWithout strict mode - Return code: {return_code}")
        print("Warning (non-strict mode):")
        print(stderr)

    finally:
        os.unlink(non_sql_file)

    print()


def demonstrate_error_handling():
    """Demonstrate CLI error handling."""
    print("=== CLI Error Handling Demonstration ===")

    # Try to process a non-existent file
    return_code, stdout, stderr = run_cli_command(["nonexistent_file.sql"])

    print(f"Return code: {return_code}")
    print("Error handling:")
    print(stderr)
    print()


def demonstrate_integration_with_generated_code():
    """Demonstrate using CLI-generated code in a Python script."""
    print("=== CLI Integration with Generated Code ===")

    # Create a temporary directory for output
    with tempfile.TemporaryDirectory() as temp_dir:
        sql_file = os.path.join(PROJECT_ROOT, "examples", "User.sql")

        # Generate the code using CLI
        return_code, stdout, stderr = run_cli_command([sql_file, "-o", temp_dir])

        if return_code == 0:
            print("Successfully generated code using CLI")

            # Add the output directory to Python path
            sys.path.insert(0, temp_dir)

            # Import and use the generated class
            try:
                from user import User

                print("Successfully imported generated User class")

                # Create a test database
                engine = create_engine("sqlite:///:memory:")

                with engine.connect() as conn:
                    # Create users table
                    conn.execute(
                        text("""
                        CREATE TABLE users (
                            id INTEGER PRIMARY KEY,
                            username TEXT UNIQUE NOT NULL,
                            email TEXT UNIQUE NOT NULL,
                            password_hash TEXT NOT NULL,
                            status TEXT DEFAULT 'active',
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    )

                    # Insert test data
                    conn.execute(
                        text("""
                        INSERT INTO users (id, username, email, password_hash, status) VALUES 
                        (1, 'john_doe', 'john@example.com', 'hashed_password_123', 'active')
                    """)
                    )
                    conn.commit()

                    # Use the generated class
                    users = User.get_user_by_id(connection=conn, user_id=1)
                    if users:
                        user = users[0]
                        print(f"Retrieved user via CLI-generated code: {user.username}")

                print("CLI integration test completed successfully!")

            except ImportError as e:
                print(f"Failed to import generated class: {e}")
            except OSError as e:
                print(f"Error accessing files: {e}")
            except Exception as e:
                print(f"Unexpected error using generated class: {e}")
        else:
            print("Failed to generate code using CLI")
            print(stderr)


def main():
    """Main example function."""
    print("splurge-sql-generator CLI Usage Example")
    print("=" * 60)
    print()

    # Setup logging
    setup_logging()

    # Demonstrate various CLI features
    demonstrate_cli_help()
    demonstrate_dry_run()
    demonstrate_output_directory()
    demonstrate_multiple_files()
    demonstrate_custom_sql_types()
    demonstrate_strict_mode()
    demonstrate_error_handling()
    demonstrate_integration_with_generated_code()

    print("=" * 60)
    print("CLI usage example completed successfully!")
    print("\nKey benefits of using the CLI:")
    print("- Simple command-line interface")
    print("- Batch processing of multiple files")
    print("- Integration with build scripts and CI/CD")
    print("- Consistent output formatting")
    print("- Error handling and validation")
    print("- Custom SQL type mapping support")


if __name__ == "__main__":
    main()
