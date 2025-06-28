"""
jpy_sql_generator CLI - Command-line interface for SQL code generation.

Copyright (c) 2025, Jim Schilling

This module is licensed under the MIT License.
"""

import argparse
import sys
from pathlib import Path
from jpy_sql_generator.code_generator import PythonCodeGenerator


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate Python SQLAlchemy classes from SQL template files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate a single class
  python -m jpy_sql_generator.cli examples/UserRepository.sql -o generated/
  
  # Generate multiple classes
  python -m jpy_sql_generator.cli examples/*.sql -o generated/
  
  # Print generated code to stdout
  python -m jpy_sql_generator.cli examples/ProductRepository.sql
        """
    )
    
    parser.add_argument(
        'sql_files',
        nargs='+',
        help='SQL template file(s) to process'
    )
    
    parser.add_argument(
        '-o', '--output',
        help='Output directory for generated Python files'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Print generated code to stdout without saving files'
    )
    
    args = parser.parse_args()
    
    # Validate input files
    sql_files = []
    for file_path in args.sql_files:
        path = Path(file_path)
        if not path.exists():
            print(f"Error: SQL file not found: {file_path}", file=sys.stderr)
            sys.exit(1)
        if not path.suffix.lower() == '.sql':
            print(f"Warning: File {file_path} doesn't have .sql extension", file=sys.stderr)
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
                args.output if not args.dry_run else None
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


if __name__ == '__main__':
    main() 