# API Reference — splurge_sql_generator

Version: 2025.5.0 (release/2025.5.0-prep)

This document is a comprehensive reference for the public Python API provided by the `splurge_sql_generator` package. It includes class and function signatures, descriptions, return values, raised exceptions, short usage examples, and migration notes from 2025.4.x → 2025.5.0.

## Table of contents

- Overview
- Public constants
- Convenience functions (module-level)
- Core classes
  - `SqlParser`
  - `SchemaParser`
  - `PythonCodeGenerator`
- SQL helpers
  - `detect_statement_type`
  - `remove_sql_comments`
  - `parse_sql_statements`
  - `split_sql_file`
  - `is_fetch_statement`, `is_execute_statement`
- Errors and Exceptions
- Migration notes: 2025.4.x → 2025.5.0
- Examples

## Overview

`splurge_sql_generator` is a code generation utility that reads annotated SQL template files and generates Python classes (SQLAlchemy-ready) with methods that correspond to SQL statements. It also provides utilities to parse SQL, detect statement type (fetch/execute), and generate a default type mapping YAML file.

All public APIs are re-exported at the package level in `splurge_sql_generator.__init__`.

## Public constants

- `FETCH_STATEMENT` — internal constant used by helpers to indicate a statement returns rows.
- `EXECUTE_STATEMENT` — internal constant used by helpers to indicate a statement executes without returning rows.

(See `splurge_sql_generator.sql_helper` for details.)

## Convenience functions (package-level)

These functions are available from `import splurge_sql_generator as ssg` (or from `splurge_sql_generator` directly):

### `generate_class(sql_file_path: str, *, output_file_path: str | None = None, schema_file_path: str) -> str`
Generate a single Python class from a SQL template file.

- Args:
  - `sql_file_path`: Path to SQL template file (required)
  - `output_file_path`: Optional path to save the generated python file (if provided, file is written)
  - `schema_file_path`: Path to schema file (required)
- Returns: Generated Python code as a string.
- Raises: `FileError`, `SqlValidationError`, `ConfigurationError` in file/schema issues, parsing errors, etc.

### `generate_multiple_classes(sql_files: list[str], *, output_dir: str | None = None, schema_file_path: str) -> dict[str, str]`
Process multiple SQL files and generate classes for each.

- Args:
  - `sql_files`: list of SQL file paths
  - `output_dir`: directory to write generated files (if None, returns the code without writing)
  - `schema_file_path`: Path to shared schema file
- Returns: mapping of class name → generated code string

### `generate_types_file(*, output_path: str | None = None) -> str`
Generate the default `types.yaml` SQL→Python mapping file.

- Args: `output_path` optional path for the file (default: `types.yaml`)
- Returns: Path to the generated file.

## Core classes

### `SqlParser`

Purpose: Parse a SQL template file (annotated with comments for class and method names) and extract:
- Class name (from top-level comment)
- Method names and corresponding SQL strings

Key methods (public):

- `parse_file(file_path: str | Path) -> tuple[str, dict[str, str]]`
  - Read SQL file and return `(class_name, method_queries)`
  - Raises `FileError` on read errors, `SqlValidationError` on format issues

- `parse_string(content: str, file_path: str | Path | None = None) -> tuple[str, dict[str, str]]`
  - Parse SQL string content directly (useful in tests or generated content)

Usage example:

```py
from splurge_sql_generator import SqlParser
parser = SqlParser()
class_name, methods = parser.parse_file('examples/User.sql')
```

### `SchemaParser`

Purpose: Parse schema files (.schema) and maintain SQL→Python type mapping. Also used to generate a default `types.yaml` mapping file.

Key methods (public):

- `load_schema(schema_file_path: Path | str) -> dict[str, dict[str, str]]`
  - Reads the schema file and returns table → columns mapping
  - Returns `{}` if file not present (by design)
  - Raises `FileError` for permission/IO errors, `SqlValidationError` for malformed SQL

- `generate_types_file(*, output_path: str | None = None) -> str`
  - Produces a YAML file with common SQL→Python mappings (Postgres/MSSQL/Oracle sections)
  - Uses file I/O and will raise `FileError` on write problems

- `load_sql_type_mapping(mapping_file: str | Path) -> dict[str, str]`
  - Load a YAML mapping file and validate contents.

Usage example:

```py
from splurge_sql_generator import SchemaParser
sp = SchemaParser()
sp.load_schema('examples/database.schema')
sp.generate_types_file(output_path='types.yaml')
```

### `PythonCodeGenerator`

Purpose: High-level API to generate Python code (SQLAlchemy-friendly) using jinja2 templates.

Constructor:
```
PythonCodeGenerator(sql_type_mapping_file: str | None = None, validate_parameters: bool = False)
```
- `sql_type_mapping_file`: optional custom types YAML (default `types.yaml` if not provided).
- `validate_parameters`: if True, validate SQL parameters against schema columns.

Key methods:

- `generate_class(sql_file_path: str | Path, *, output_file_path: str | None = None, schema_file_path: str) -> str`
  - Generates a single class and optionally writes to `output_file_path`.
  - Raises `FileError`, `SqlValidationError`, `ConfigurationError` as appropriate.

- `generate_multiple_classes(sql_files: list[str], *, output_dir: str | None = None, schema_file_path: str) -> dict[str, str]`
  - Generate multiple classes, optionally writing files into `output_dir`.

Usage example:

```py
from splurge_sql_generator import PythonCodeGenerator
gen = PythonCodeGenerator(sql_type_mapping_file='types.yaml')
code = gen.generate_class('examples/User.sql', schema_file_path='examples/User.schema')
print(code)
```

## SQL helper functions (module: `splurge_sql_generator.sql_helper`)

These helpers help tokenizing, cleaning, and splitting SQL files.

### `detect_statement_type(sql: str) -> str`
Detect whether SQL statement is `fetch` (returns rows) or `execute` (does not return rows).

### `remove_sql_comments(sql: str) -> str`
Strip SQL comments while preserving comments inside string literals.

### `parse_sql_statements(sql: str, *, strip_semicolon: bool = True) -> list[str]`
Parse SQL text into individual statements using `sqlparse` and the package's logic.

### `split_sql_file(file_path: str | Path, *, strip_semicolon: bool = True) -> list[str]`
Read a `.sql` file and return list of statements. Raises `FileError` if file missing or unreadable.

### `is_fetch_statement(sql: str) -> bool`
### `is_execute_statement(sql: str) -> bool`
Convenience wrappers around `detect_statement_type`.

## Errors and Exceptions

All exceptions live in `splurge_sql_generator.exceptions` and inherit from `SplurgeSqlGeneratorError`.

- `SplurgeSqlGeneratorError(message: str, details: str | None = None)` — base
- `FileError` — I/O and file path related issues
- `SqlValidationError` — invalid input / SQL format errors
- `ParsingError`, `SqlParsingError`, `TokenizationError` — parsing and token-level
- `SchemaError`, `ColumnDefinitionError`, `TypeInferenceError` — schema-level
- `ConfigurationError` — configuration / YAML errors

Examples:

```py
try:
    code = generate_class('examples/User.sql', schema_file_path='nonexistent.schema')
except FileError as e:
    print(e.message)
    print(e.details)
```

## Migration notes: 2025.4.x → 2025.5.0

This release introduced several API and internal improvements. Important migration notes:

- Safe I/O adapter
  - File I/O now uses a centralized `SafeTextFileIoAdapter` (in `splurge_sql_generator.file_utils`).
  - Direct usage of `splurge_safe_io.safe_text_file_reader.SafeTextFileReader` and `splurge_safe_io.safe_text_file_writer.SafeTextFileWriter` has been removed from public modules. If you previously used these classes directly in your code via imports from `splurge_sql_generator`, update to use the new adapter:

```py
from splurge_sql_generator.file_utils import SafeTextFileIoAdapter
file_io = SafeTextFileIoAdapter()
content = file_io.read_text('file.sql')
file_io.write_text('out.sql', '...')
```

- Types module renamed
  - `splurge_sql_generator.types` was renamed to `splurge_sql_generator.type_definitions` to avoid stdlib shadowing. If you imported `splurge_sql_generator.types`, update to:

```py
from splurge_sql_generator import type_definitions
```

- Error messages
  - Some internal error messages were standardized to `FileError` messages originating from the adapter. Tests were updated accordingly.

- Improved explicit validation
  - Functions now validate `None` more explicitly and raise `TypeError` or `SqlValidationError` with clearer messages.

## Examples

1. Generate single class to stdout

```py
from splurge_sql_generator import PythonCodeGenerator

gen = PythonCodeGenerator()
print(gen.generate_class('examples/User.sql', schema_file_path='examples/User.schema'))
```

2. Generate multiple classes and write to directory

```py
from splurge_sql_generator import PythonCodeGenerator

gen = PythonCodeGenerator()
classes = gen.generate_multiple_classes(['examples/User.sql', 'examples/ProductRepository.sql'], output_dir='generated', schema_file_path='examples/database.schema')
```

3. Programmatically parse SQL and inspect statements

```py
from splurge_sql_generator import split_sql_file, parse_sql_statements
stmts = split_sql_file('examples/complex.sql')
print(len(stmts))
```

---

For additional details, check docstrings in each module and unit tests in `tests/` for concrete behavior examples.