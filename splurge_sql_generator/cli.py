"""
splurge_sql_generator CLI - Command-line interface for SQL code generation.

Copyright (c) 2025, Jim Schilling

This module is licensed under the MIT License.
"""

import argparse
import sys
from pathlib import Path

from splurge_sql_generator.code_generator import PythonCodeGenerator


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate Python SQLAlchemy classes from SQL template files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate a single class
  python -m splurge_sql_generator.cli examples/User.sql -o generated/
  
  # Generate multiple classes
  python -m splurge_sql_generator.cli examples/*.sql -o generated/
  
  # Print generated code to stdout
  python -m splurge_sql_generator.cli examples/ProductRepository.sql
        """,
    )

    parser.add_argument("sql_files", nargs="+", help="SQL template file(s) to process")

    parser.add_argument(
        "-o", "--output", help="Output directory for generated Python files"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print generated code to stdout without saving files",
    )

    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings (e.g., non-.sql inputs, empty directory) as errors",
    )

    args = parser.parse_args()

    # Validate input files or expand directories
    sql_files: list[str] = []
    for file_path in args.sql_files:
        path = Path(file_path)
        if not path.exists():
            print(f"Error: SQL file not found: {file_path}", file=sys.stderr)
            sys.exit(1)

        if path.is_dir():
            discovered = [str(p) for p in path.rglob("*.sql")]
            if not discovered:
                msg = f"Warning: No .sql files found in directory {file_path}"
                if args.strict:
                    print(f"Error: {msg}", file=sys.stderr)
                    sys.exit(1)
                print(msg, file=sys.stderr)
                continue
            sql_files.extend(discovered)
            continue

        if path.is_file():
            if path.suffix.lower() != ".sql":
                msg = f"Warning: File {file_path} doesn't have .sql extension"
                if args.strict:
                    print(f"Error: {msg}", file=sys.stderr)
                    sys.exit(1)
                print(msg, file=sys.stderr)
            sql_files.append(str(path))

    # Create output directory if specified
    if args.output and not args.dry_run:
        output_dir = Path(args.output)
        output_dir.mkdir(parents=True, exist_ok=True)

    # Generate classes
    generator = PythonCodeGenerator()

    try:
        if len(sql_files) == 1 and args.dry_run:
            # Single file, print to stdout
            code = generator.generate_class(sql_files[0])
            print(code)
        else:
            # Multiple files or save to directory
            generated_classes = generator.generate_multiple_classes(
                sql_files,
                output_dir=args.output if not args.dry_run else None,
            )

            if args.dry_run:
                # Print all generated code
                for class_name, code in generated_classes.items():
                    print(f"# Generated class: {class_name}")
                    print("=" * 50)
                    print(code)
                    print("\n" + "=" * 50 + "\n")
            else:
                # Report what was generated
                print(f"Generated {len(generated_classes)} Python classes:")
                for class_name in generated_classes.keys():
                    print(f"  - {class_name}.py")

    except Exception as e:
        print(f"Error generating classes: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
