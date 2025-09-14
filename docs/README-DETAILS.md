# splurge-sql-generator

A Python library for generating SQLAlchemy classes from SQL template files with sophisticated SQL parsing and statement type detection.

## Features

- **SQL Template Parsing**: Parse SQL files with method name comments to extract queries
- **Intelligent Type Inference**: Advanced parameter type detection using schema analysis, naming patterns, and SQL context
- **Schema-Based Type Mapping**: Automatically infer Python types from SQL schema files (`.schema`) for accurate type annotations
- **Custom SQL Type Mapping**: Support for custom SQL-to-Python type mappings via configurable YAML files
- **Type File Generation**: Generate default SQL type mapping files with `--generate-types` option
- **Parameter Validation**: Optional validation of SQL parameters against schema definitions
- **Statement Type Detection**: Automatically detect if SQL statements return rows (fetch) or perform operations (execute)
- **Code Generation**: Generate Python classes with SQLAlchemy methods and precise type hints
- **Parameter Extraction**: Extract and map SQL parameters to Python method signatures with inferred types
- **Multi-Database Support**: Built-in support for SQLite, PostgreSQL, MySQL, MSSQL, and Oracle SQL types
- **CLI Interface**: Command-line tool for batch processing with flexible configuration options
- **Comprehensive Error Handling**: Robust error handling for file operations and SQL parsing with fail-fast validation

## SQL File Format Requirement

> **Important:** The first line of every SQL file must be a class comment specifying the class name, e.g.:
>
>     # UserRepository
>
> This class name will be used for the generated Python class. The filename is no longer used for class naming.

## Installation

```bash
pip install splurge-sql-generator
```

Or install from source:

```bash
git clone https://github.com/yourusername/splurge-sql-generator.git
cd splurge-sql-generator
pip install -e .
```

## Quick Start

### 1. Create a SQL Template File



**Generated method signatures** (with intelligent type inference):
```python
@classmethod
def get_user_by_id(
    cls,
    *,
    connection: Connection,
    id: int,  # Inferred from INTEGER in schema
) -> List[Row]:

@classmethod
def create_user(
    cls,
    *,
    connection: Connection,
    username: str,     # Inferred from VARCHAR in schema
    email: str,        # Inferred from VARCHAR in schema
    age: int,          # Inferred from INTEGER in schema
    salary: float,     # Inferred from DECIMAL in schema
    is_active: bool,   # Inferred from BOOLEAN in schema
) -> Result:
```

### Advanced Type Inference Examples

The type inference system uses multiple strategies to determine parameter types:

**Schema-based inference** (highest priority):
```python
# Parameter matches schema column exactly
def get_user_by_id(self, user_id: int) -> dict[str, Any] | None:
    # user_id matches 'id INTEGER' in schema → int
```

**Pattern-based inference** (fallback):
```python
# Common naming patterns
def search_products(self, search_term: str) -> list[dict[str, Any]]:
    # '_term' suffix → str
    
def update_stock(self, product_id: int, new_quantity: int) -> None:
    # '_id' suffix → int, '_quantity' suffix → int
    
def set_price(self, item_price: float) -> None:
    # '_price' suffix → float
```

**Context-based inference** (SQL analysis):
```python
# SQL context analysis
def find_active_users(self, is_active: bool) -> list[dict[str, Any]]:
    # WHERE is_active = :is_active → boolean comparison
```

### Custom SQL Type Mappings

You can customize the SQL-to-Python type mappings using a custom YAML file:

**custom_types.yaml**:
```yaml
# Custom SQL Type to Python Type Mapping
CUSTOM_ID: int
CUSTOM_NAME: str
CUSTOM_AMOUNT: float
CUSTOM_FLAG: bool
CUSTOM_DATA: dict
DEFAULT: Any
```

Use it with the CLI:
```bash
python -m splurge_sql_generator.cli UserRepository.sql --types custom_types.yaml
```

### Generating Type Mapping Files

You can generate the default SQL type mapping file to use as a starting point:

```bash
# Generate default types.yaml in current directory
python -m splurge_sql_generator.cli --generate-types

# Generate custom types file
python -m splurge_sql_generator.cli --generate-types my_custom_types.yaml
```

Or programmatically:
```python
from splurge_sql_generator import generate_types_file

# Generate default types.yaml
generate_types_file()

# Generate custom types file
generate_types_file(output_path='my_custom_types.yaml')
```

> **Note:** The `generate_types_file()` function uses keyword-only parameters. Always use `output_path='filename'` syntax.

The generated file includes comprehensive mappings for SQLite, PostgreSQL, MySQL, MSSQL, and Oracle types, organized by database with helpful comments.

## Usage Examples

### Statement Type Detection

```python
from splurge_sql_generator import detect_statement_type, is_fetch_statement

# Detect statement types
sql1 = "SELECT * FROM users WHERE id = :user_id"
print(detect_statement_type(sql1))  # 'fetch'

sql2 = "INSERT INTO users (name) VALUES (:name)"
print(detect_statement_type(sql2))  # 'execute'

# Convenience functions
print(is_fetch_statement(sql1))     # True
print(is_fetch_statement(sql2))     # False
```

### Complex SQL with CTEs

```sql
# UserStats
#get_user_stats
WITH user_orders AS (
    SELECT user_id, COUNT(*) as order_count
    FROM orders
    GROUP BY user_id
)
SELECT u.name, uo.order_count
FROM users u
LEFT JOIN user_orders uo ON u.id = uo.user_id
WHERE u.id = :user_id AND u.status = :status;
```

The generator will correctly detect this as a fetch statement and generate appropriate Python code.

### CLI Usage

```bash
# Generate single class (module)
python -m splurge_sql_generator.cli UserRepository.sql --output generated/

# Generate single class (console script)
splurge-sql-gen UserRepository.sql --output generated/

# Generate multiple classes (globs expanded by shell)
splurge-sql-gen *.sql --output generated/

# Generate from a directory recursively
splurge-sql-gen path/to/sqls/ --output generated/

# Preview generated code without saving
splurge-sql-gen UserRepository.sql --dry-run

# Strict mode: treat warnings (e.g., non-.sql inputs, empty dir) as errors
splurge-sql-gen path/to/sqls/ --output generated/ --strict

# Generate to specific output directory
splurge-sql-gen UserRepository.sql -o src/repositories/

# Use custom SQL type mapping file
splurge-sql-gen UserRepository.sql --output generated/ --types custom_types.yaml

# Use custom SQL type mapping file (short form)
splurge-sql-gen UserRepository.sql --output generated/ -t custom_types.yaml

# Use shared schema file for multiple SQL files
splurge-sql-gen *.sql --output generated/ --schema User.schema

# Use shared schema file with custom type mapping
splurge-sql-gen *.sql --output generated/ --schema User.schema --types custom_types.yaml

# Automatic schema discovery (no --schema needed)
splurge-sql-gen *.sql --output generated/  # Automatically finds *.schema files

# Generate default SQL type mapping file
splurge-sql-gen --generate-types

# Generate custom SQL type mapping file
splurge-sql-gen --generate-types my_types.yaml
```

## API Reference

### Core Classes

#### `PythonCodeGenerator`
Main class for generating Python code from SQL templates.

```python
# Use default types.yaml
generator = PythonCodeGenerator()

# Use custom SQL type mapping file
generator = PythonCodeGenerator(sql_type_mapping_file="custom_types.yaml")

# Use with parameter validation enabled
generator = PythonCodeGenerator(validate_parameters=True)

# Generate code
code = generator.generate_class(sql_file_path, output_file_path=None, schema_file_path=None)
classes = generator.generate_multiple_classes(sql_files, output_dir=None, schema_file_path=None)
```

**Parameters:**
- `sql_type_mapping_file` (optional): Path to custom SQL type mapping YAML file. Defaults to `types.yaml`.
- `validate_parameters` (optional): Whether to validate SQL parameters against schema. Defaults to `False`.

**Methods:**
- `generate_class(sql_file_path, *, output_file_path=None, schema_file_path=None)`: Generate a single Python class
- `generate_multiple_classes(sql_files, *, output_dir=None, schema_file_path=None)`: Generate multiple Python classes

#### `SqlParser`
Parser for SQL template files.

```python
parser = SqlParser()
class_name, method_queries = parser.parse_file(sql_file_path)
class_name, method_queries = parser.parse_string(sql_content, file_path=None)
method_info = parser.get_method_info(sql_query)
```

#### `SchemaParser`
Parser for SQL schema files and type mapping.

```python
schema_parser = SchemaParser()
schema_parser.load_schema(schema_file_path)
schema_parser.generate_types_file(output_path=None)
```

### SQL Helper Functions

#### `detect_statement_type(sql: str) -> str`
Detect if a SQL statement returns rows ('fetch') or performs operations ('execute').

#### `is_fetch_statement(sql: str) -> bool`
Convenience function to check if a statement returns rows.

#### `is_execute_statement(sql: str) -> bool`
Convenience function to check if a statement performs operations.

#### `remove_sql_comments(sql_text: str) -> str`
Remove SQL comments from a SQL string.

#### `parse_sql_statements(sql_text: str, strip_semicolon: bool = False) -> List[str]`
Parse a SQL string containing multiple statements into individual statements.

#### `split_sql_file(file_path: str, strip_semicolon: bool = False) -> List[str]`
Read a SQL file and split it into individual statements.

#### `parse_table_columns(table_body: str) -> dict[str, str]`
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

The test suite now uses pytest. Run all tests with:

```bash
pytest -q
```

Run a single test file or directory:

```bash
pytest tests/unit/test_some_module.py -q
pytest tests/integration -q
```

Notes:
- The test suite was migrated from unittest to pytest to simplify test fixtures and parametrization.
- Coverage reports are available via the `coverage` plugin or CI integration (see repo badges).

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
