"""
splurge_sql_generator CLI - Command-line interface for SQL code generation.

Copyright (c) 2025, Jim Schilling

This module is licensed under the MIT License.
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

from splurge_sql_generator.code_generator import PythonCodeGenerator


def _find_schema_files(sql_files: list[str]) -> Optional[str]:
    """
    Find schema files when no --schema option is specified.
    
    Looks for *.schema files in the current directory and directories containing SQL files.
    
    Args:
        sql_files: List of SQL file paths
        
    Returns:
        Path to the first found schema file, or None if no schema files found
    """
    # Get unique directories from SQL files
    sql_dirs = {Path(sql_file).parent for sql_file in sql_files}
    # Add current directory
    search_dirs = {Path.cwd()} | sql_dirs
    
    # Look for *.schema files in each directory
    for search_dir in search_dirs:
        schema_files = list(search_dir.glob("*.schema"))
        if schema_files:
            # Return the first schema file found
            return str(schema_files[0])
    
    return None


def main() -> None:
    """
    Main CLI entry point for the SQL code generator.
    
    Parses command line arguments and generates Python SQLAlchemy classes from SQL template files.
    Supports single file generation, multiple file processing, and custom output directories.
    
    Command line options:
        sql_files: One or more SQL template files to process
        -o, --output: Output directory for generated Python files
        --dry-run: Print generated code to stdout without saving files
        --strict: Treat warnings as errors
        -t, --types: Path to custom SQL type mapping YAML file
    """
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
  
  # Use custom SQL type mapping file
  python -m splurge_sql_generator.cli examples/User.sql -o generated/ --types custom_types.yaml
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

    parser.add_argument(
        "-t", "--types",
        help="Path to custom SQL type mapping YAML file (default: types.yaml)",
    )

    parser.add_argument(
        "--schema",
        help="Path to schema file to use for all SQL files (default: look for *.schema files in current directory and SQL file directories)",
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
    output_dir: Path | None = None
    if args.output and not args.dry_run:
        output_dir = Path(args.output)
        output_dir.mkdir(parents=True, exist_ok=True)

    # Determine schema file to use
    schema_file = args.schema
    if schema_file is None and sql_files:
        schema_file = _find_schema_files(sql_files)
        if schema_file is None:
            print("Error: No schema file specified and no *.schema files found in current directory or SQL file directories", file=sys.stderr)
            print("Use --schema to specify a schema file or ensure *.schema files exist", file=sys.stderr)
            sys.exit(1)

    # Generate classes
    generator = PythonCodeGenerator(sql_type_mapping_file=args.types)

    try:
        # If no SQL files were found, we're done
        if not sql_files:
            return
            
        if len(sql_files) == 1 and args.dry_run:
            # Single file, print to stdout
            code = generator.generate_class(sql_files[0], schema_file_path=schema_file)
            print(code)
        else:
            # Multiple files or save to directory
            generated_classes = generator.generate_multiple_classes(
                sql_files,
                output_dir=args.output if not args.dry_run else None,
                schema_file_path=schema_file,
            )

            if args.dry_run:
                # Print all generated code
                for class_name, code in generated_classes.items():
                    snake_case_name = generator._to_snake_case(class_name)
                    print(f"# Generated class: {class_name}: {snake_case_name}.py")
                    print("=" * 50)
                    print(code)
                    print("\n" + "=" * 50 + "\n")
            else:
                # Report what was generated
                print(f"Generated {len(generated_classes)} Python classes:")
                for class_name in generated_classes.keys():
                    snake_case_name = generator._to_snake_case(class_name)
                    if output_dir:
                        print(f"    - {class_name}: {output_dir / f'{snake_case_name}.py'}")
                    else:
                        print(f"    - {class_name}: {snake_case_name}.py")

    except (OSError, IOError, FileNotFoundError) as e:
        print(f"Error accessing files: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Error in SQL file format: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error generating classes: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
