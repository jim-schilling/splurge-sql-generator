# splurge-sql-generator

![PyPI](https://img.shields.io/pypi/v/splurge-sql-generator.svg)
![Build Status](https://img.shields.io/github/actions/workflow/status/jim-schilling/splurge-sql-generator/ci.yml?branch=main)
![Coverage Status](https://img.shields.io/codecov/c/github/jim-schilling/splurge-sql-generator?branch=main)
![License](https://img.shields.io/badge/license-MIT-green.svg)

A compact summary of splurge-sql-generator — a tool to generate Python (SQLAlchemy-friendly) classes from SQL template files with schema-aware type inference.

See the full documentation and details in the repository:

- Detailed docs: `docs/README-DETAILS.md`
- Full changelog: `CHANGELOG.md`

Key features

- SQL template parsing and method extraction from commented templates
- Schema-based type inference for accurate Python type annotations
- Configurable SQL-to-Python type mapping via YAML files (`types.yaml` / `--types`)
- CLI for batch generation with automatic schema discovery and `--generate-types`
- Strong SQL parsing with sqlparse and explicit error reporting

Getting started

1. Install: `pip install splurge-sql-generator` or `pip install -e .` for development
2. Read the full docs in `docs/README-DETAILS.md`

For examples and advanced usage see `examples/` in the repository.
Parse column definitions from table body using sqlparse tokens. Raises `SqlValidationError` if parsing fails or no valid columns are found.

#### `extract_table_names(sql_query: str) -> list[str]`
Extract table names from SQL query using sqlparse. Raises `SqlValidationError` if parsing fails or no table names are found.

#### `generate_types_file(*, output_path: str | None = None) -> str`
Generate the default SQL type mapping YAML file.

## Supported SQL Features

- **Basic DML**: SELECT, INSERT, UPDATE, DELETE
- **CTEs**: Common Table Expressions (WITH clauses)
- **Complex Queries**: Subqueries, JOINs, aggregations
- **Database-Specific**: SHOW, EXPLAIN, DESCRIBE, VALUES
- **Parameters**: Named parameters with `:param_name` syntax
- **Comments**: Single-line (`--`) and multi-line (`/* */`) comments

## Generated Code Features

- **Accurate Type Hints**: Schema-based type inference for precise parameter and return value annotations
- **Custom Type Support**: Configurable SQL-to-Python type mappings for project-specific needs
- **Parameter Validation**: Optional validation of SQL parameters against schema definitions
- **Multi-Database Types**: Built-in support for SQLite, PostgreSQL, MySQL, MSSQL, and Oracle types
- **Docstrings**: Comprehensive documentation for each method
- **Error Handling**: Proper SQLAlchemy result handling with fail-fast validation
- **Parameter Mapping**: Automatic mapping of SQL parameters to Python arguments with inferred types
- **Statement Type Detection**: Correct return types based on SQL statement type
- **Auto-Generated Headers**: Clear identification of generated files

## Error Handling and Validation

The library provides robust error handling with a fail-fast approach to ensure data integrity and clear error reporting:

### SQL Parsing Validation
- **Strict SQL Parsing**: Functions like `parse_table_columns()` and `extract_table_names()` use sqlparse for reliable parsing
- **No Fallback Mechanisms**: Eliminates unreliable regex-based fallback parsing in favor of clear error reporting
- **Clear Error Messages**: Functions raise `SqlValidationError` with descriptive messages when parsing fails
- **Validation Checks**: Ensures valid column definitions and table names are found before processing

### Error Types
- **`SqlValidationError`**: Raised when SQL parsing fails or validation checks fail
- **`SqlFileError`**: Raised for file operation errors (file not found, permission denied, etc.)
- **Clear Context**: Error messages include file paths, referenced tables, and available columns for debugging

### Example Error Handling
```python
from splurge_sql_generator.errors import SqlValidationError, SqlFileError

try:
    # This will raise SqlValidationError if no valid columns are found
    columns = parse_table_columns("CONSTRAINT pk_id PRIMARY KEY (id)")
except SqlValidationError as e:
    print(f"SQL validation failed: {e}")

try:
    # This will raise SqlValidationError if no table names are found
    tables = extract_table_names("SELECT 1 as value")
except SqlValidationError as e:
    print(f"SQL validation failed: {e}")

try:
    # This will raise SqlValidationError for empty input
    columns = parse_table_columns("")
except SqlValidationError as e:
    print(f"SQL validation failed: {e}")
```

## Development

### Running Tests

```bash
python -m unittest discover -s tests -v
```

### Project Structure

```
splurge-sql-generator/
├── splurge_sql_generator/
│   ├── __init__.py          # Main package exports
│   ├── sql_helper.py        # SQL parsing utilities
│   ├── sql_parser.py        # SQL template parser
│   ├── schema_parser.py     # SQL schema parser for type inference
│   ├── code_generator.py    # Python code generator
│   ├── cli.py               # Command-line interface
│   └── templates/           # Jinja2 templates (python_class.j2)
├── tests/                   # Test suite
├── examples/                # Example SQL templates and schemas
│   ├── *.sql                # SQL template files
│   ├── *.schema             # SQL schema files for type inference
│   └── custom_types.yaml    # Example custom type mapping
├── output/                  # Generated code examples
└── types.yaml               # Default SQL type mappings
```

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

---
