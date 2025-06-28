# jpy-sql-generator

A Python library for generating SQLAlchemy classes from SQL template files with sophisticated SQL parsing and statement type detection.

## Features

- **SQL Template Parsing**: Parse SQL files with method name comments to extract queries
- **Statement Type Detection**: Automatically detect if SQL statements return rows (fetch) or perform operations (execute)
- **Code Generation**: Generate Python classes with SQLAlchemy methods
- **Parameter Extraction**: Extract and map SQL parameters to Python method signatures
- **CLI Interface**: Command-line tool for batch processing
- **Comprehensive Error Handling**: Robust error handling for file operations and SQL parsing

## Installation

```bash
pip install jpy-sql-generator
```

Or install from source:

```bash
git clone https://github.com/yourusername/jpy-sql-generator.git
cd jpy-sql-generator
pip install -e .
```

## Quick Start

### 1. Create a SQL Template File

Create a file named `UserRepository.sql`:

```sql
#get_user_by_id
SELECT id, username, email, created_at 
FROM users 
WHERE id = :user_id;

#create_user
INSERT INTO users (username, email, password_hash, status) 
VALUES (:username, :email, :password_hash, :status) 
RETURNING id;

#update_user_status
UPDATE users 
SET status = :new_status, updated_at = CURRENT_TIMESTAMP 
WHERE id = :user_id;
```

### 2. Generate Python Class

Using the CLI:

```bash
python -m jpy_sql_generator.cli UserRepository.sql --output generated/
```

Or using Python:

```python
from jpy_sql_generator import PythonCodeGenerator

generator = PythonCodeGenerator()
code = generator.generate_class('UserRepository.sql', 'generated/UserRepository.py')
```

### 3. Use the Generated Class

```python
from sqlalchemy import create_engine
from generated.UserRepository import UserRepository

# Create database connection
engine = create_engine('sqlite:///example.db')
connection = engine.connect()

# Use the generated repository
user_repo = UserRepository(connection)

# Get user by ID
users = user_repo.get_user_by_id(user_id=1)

# Create new user
result = user_repo.create_user(
    username='john_doe',
    email='john@example.com',
    password_hash='hashed_password',
    status='active'
)
```

## Usage Examples

### Statement Type Detection

```python
from jpy_sql_generator import detect_statement_type, is_fetch_statement

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
# Generate single class
python -m jpy_sql_generator.cli UserRepository.sql --output generated/

# Generate multiple classes
python -m jpy_sql_generator.cli *.sql --output generated/

# Preview generated code without saving
python -m jpy_sql_generator.cli UserRepository.sql --dry-run

# Generate to specific output directory
python -m jpy_sql_generator.cli UserRepository.sql -o src/repositories/
```

## API Reference

### Core Classes

#### `PythonCodeGenerator`
Main class for generating Python code from SQL templates.

```python
generator = PythonCodeGenerator()
code = generator.generate_class(sql_file_path, output_file_path=None)
classes = generator.generate_multiple_classes(sql_files, output_dir=None)
```

#### `SqlParser`
Parser for SQL template files.

```python
parser = SqlParser()
class_name, method_queries = parser.parse_file(sql_file_path)
method_info = parser.get_method_info(sql_query)
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

## Supported SQL Features

- **Basic DML**: SELECT, INSERT, UPDATE, DELETE
- **CTEs**: Common Table Expressions (WITH clauses)
- **Complex Queries**: Subqueries, JOINs, aggregations
- **Database-Specific**: SHOW, EXPLAIN, DESCRIBE, VALUES
- **Parameters**: Named parameters with `:param_name` syntax
- **Comments**: Single-line (`--`) and multi-line (`/* */`) comments

## Generated Code Features

- **Type Hints**: Full type annotations for parameters and return values
- **Docstrings**: Comprehensive documentation for each method
- **Error Handling**: Proper SQLAlchemy result handling
- **Parameter Mapping**: Automatic mapping of SQL parameters to Python arguments
- **Statement Type Detection**: Correct return types based on SQL statement type
- **Auto-Generated Headers**: Clear identification of generated files

## Development

### Running Tests

```bash
python -m unittest discover -s tests -v
```

### Project Structure

```
jpy_sql_generator/
├── jpy_sql_generator/
│   ├── __init__.py          # Main package exports
│   ├── sql_helper.py        # SQL parsing utilities
│   ├── sql_parser.py        # SQL template parser
│   ├── code_generator.py    # Python code generator
│   └── cli.py              # Command-line interface
├── tests/                   # Test suite
├── examples/               # Example SQL templates
└── output/                 # Generated code examples
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

## Changelog

### [0.1.0] - 2025-06-28

#### Added
- Initial release of jpy-sql-generator
- SQL template parsing with method name extraction
- Sophisticated SQL statement type detection (fetch vs execute)
- Support for Common Table Expressions (CTEs)
- Python code generation with SQLAlchemy integration
- Command-line interface for batch processing
- Comprehensive parameter extraction and mapping
- Support for complex SQL features (subqueries, JOINs, aggregations)
- Auto-generated file headers with tool attribution
- Robust error handling for file operations
- Comprehensive test suite with edge case coverage

#### Features
- **SQL Helper Utilities**: `detect_statement_type()`, `remove_sql_comments()`, `parse_sql_statements()`
- **Template Parser**: Extract method names and SQL queries from template files
- **Code Generator**: Generate Python classes with proper type hints and docstrings
- **CLI Tool**: Command-line interface with dry-run and batch processing options
- **Statement Detection**: Automatic detection of fetch vs execute statements
- **Parameter Handling**: Deduplication and proper mapping of SQL parameters

#### Technical Details
- Uses `sqlparse` for robust SQL parsing
- Supports all major SQL statement types
- Generates Python code with SQLAlchemy best practices
- Comprehensive error handling and validation
- MIT licensed with clear copyright attribution
