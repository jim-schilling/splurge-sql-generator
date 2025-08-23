# splurge-sql-generator

A Python library for generating SQLAlchemy classes from SQL template files with sophisticated SQL parsing and statement type detection.

## Features

- **SQL Template Parsing**: Parse SQL files with method name comments to extract queries
- **Statement Type Detection**: Automatically detect if SQL statements return rows (fetch) or perform operations (execute)
- **Code Generation**: Generate Python classes with SQLAlchemy methods
- **Parameter Extraction**: Extract and map SQL parameters to Python method signatures
- **CLI Interface**: Command-line tool for batch processing
- **Comprehensive Error Handling**: Robust error handling for file operations and SQL parsing

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

Create a file named `UserRepository.sql`:

```sql
# UserRepository
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
# Module invocation
python -m splurge_sql_generator.cli UserRepository.sql --output generated/

# Or via the installed console script
splurge-sql-gen UserRepository.sql --output generated/
```

Or using Python:

```python
from splurge_sql_generator import PythonCodeGenerator, generate_class

generator = PythonCodeGenerator()
code = generator.generate_class(
    'UserRepository.sql',
    output_file_path='generated/UserRepository.py',
)

# Or use the convenience function
code2 = generate_class(
    'UserRepository.sql',
    output_file_path='generated/UserRepository.py',
)
```

### 3. Use the Generated Class

```python
from sqlalchemy import create_engine
from generated.user_repository import UserRepository

# Create database connection
engine = create_engine('sqlite:///example.db')
connection = engine.connect()

# Use the generated class methods (class methods only)
users = UserRepository.get_user_by_id(
    connection=connection,
    user_id=1,
)

# For data modification operations, use transaction blocks
with connection.begin():
    result = UserRepository.create_user(
        connection=connection,
        username='john_doe',
        email='john@example.com',
        password_hash='hashed_password',
        status='active',
    )
    # Transaction commits automatically when context exits

# For multiple operations in a single transaction:
with connection.begin():
    UserRepository.create_user(
        connection=connection,
        username='jane',
        email='jane@example.com',
        password_hash='pw',
        status='active',
    )
    UserRepository.update_user_status(
        connection=connection,
        user_id=1,
        new_status='active',
    )
    # All operations commit together, or all rollback on error

# Note: All generated methods now use a class-level logger automatically. There is no optional logger parameter. To customize logging, configure the class logger as needed:
# import logging
# UserRepository.logger.setLevel(logging.INFO)
```

> **Note:** All generated methods are class methods. You must always pass the connection and parameters as named arguments. **For data modification operations (INSERT, UPDATE, DELETE), use `with connection.begin():` blocks to manage transactions explicitly.** This gives you full control over transaction boundaries and ensures data consistency.

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
splurge-sql-generator/
├── splurge_sql_generator/
│   ├── __init__.py          # Main package exports
│   ├── sql_helper.py        # SQL parsing utilities
│   ├── sql_parser.py        # SQL template parser
│   ├── code_generator.py    # Python code generator
│   ├── cli.py               # Command-line interface
│   └── templates/           # Jinja2 templates (python_class.j2)
├── tests/                   # Test suite
├── examples/                # Example SQL templates
└── output/                  # Generated code examples
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

### [2025.4.0] - 2025-08-23

### [2025.3.1] - 2025-08-19

#### Changed
- **Enhanced test robustness**: Updated all test assertions to use pattern matching instead of exact string matching
- **Improved test maintainability**: Tests now validate behavior and patterns rather than exact textual strings
- **Better error message flexibility**: CLI and parser tests are more tolerant of minor text changes and formatting variations
- **Cross-platform test compatibility**: Enhanced tests to handle different line endings and platform-specific formatting

#### Technical Improvements
- **CLI test enhancements**: 
  - Replaced exact error message matching with flexible pattern matching
  - Used regex patterns for generated class count validation (`r'Generated \d+ Python classes?'`)
  - Simplified error message assertions to focus on key phrases rather than exact text
  - Added regex import for advanced pattern matching capabilities
- **SQL helper test improvements**:
  - Changed from exact SQL statement equality to pattern matching with `in` operator
  - Enhanced whitespace tolerance for SQL statement validation
  - Improved semicolon handling flexibility in statement parsing tests
- **SQL parser test updates**:
  - Simplified error message validation to focus on core content
  - Removed exact punctuation and spacing requirements from error assertions
  - Made tests more resilient to UI/UX improvements and message refinements

#### Test Quality Enhancements
- **Reduced test brittleness**: Tests are less likely to break due to minor text changes or formatting updates
- **Better maintainability**: Error message improvements and UI changes won't require test updates
- **Clearer test intent**: Tests now focus on validating behavior rather than implementation details
- **Future-proof validation**: Accommodates improvements to error messages and user interface without breaking tests

#### Development Experience
- **Maintained coverage**: All 108 tests pass with 91% overall coverage (97% CLI coverage)
- **No functionality loss**: All test scenarios still validated with improved robustness
- **Enhanced reliability**: Tests handle minor text variations gracefully while maintaining validation rigor

### [2025.3.0] - 2025-08-13

#### Changed
- Package renamed and unified under `splurge-sql-generator` / `splurge_sql_generator`
- Keyword-only, fully typed public APIs (Python 3.10+ unions, precise return types)
- CLI improvements: directory input recursion and `--strict` mode
- Narrowed public exports to user-facing helpers and classes
- Consistent exceptions: `SqlValidationError` for validation; now inherits from `ValueError`
- Generated classes add a `NullHandler` to the class logger to avoid warnings
- Faster generation: preloaded Jinja template and single-parse batch generation
- Documentation updates and examples migrated to new package/module names

> Note: Backwards-compatibility with positional arguments was intentionally removed. Use keyword-only parameters (`output_file_path=...`, `output_dir=...`).

### [0.2.4] - 2025-06-30

#### Changed
- **Strict Python identifier enforcement**: Method names, class names, and parameter names extracted from SQL templates must now be valid Python identifiers. Invalid names will raise errors during code generation.
- **Improved error messages**: Clearer error reporting when invalid names are detected in SQL templates.
- **Documentation update**: The requirement for valid Python names is now explicitly documented in the README and enforced in the code generator.

> **Note:** All method names, class names, and parameter names in your SQL templates must be valid Python identifiers (letters, numbers, and underscores, not starting with a number, and not a Python keyword). This ensures the generated code is always valid and importable.

### [0.2.3] - 2025-06-29

#### Changed
- **Updated pyproject.toml**: Modernized build configuration with current best practices and comprehensive metadata
- **Enhanced development setup**: Added optional dependency groups for dev, test, and docs tools
- **Improved package metadata**: Added keywords, comprehensive classifiers, and better project description
- **Type safety improvements**: Fixed all mypy type checking issues throughout the codebase
- **Enhanced test coverage**: Added comprehensive test cases to achieve 81% overall coverage

#### Technical Improvements
- **Modern build system**: Upgraded to setuptools 68.0+ for better compatibility
- **Development dependencies**: Added pytest, black, isort, flake8, mypy, and sphinx for development workflow
- **Type annotations**: Added missing return type annotations and fixed type compatibility issues
- **Code quality tools**: Integrated Black (formatter), isort (import sorter), flake8 (linter), and mypy (type checker)
- **Comprehensive testing**: Added tests for CLI error handling, edge cases, and public API coverage
- **Cross-platform compatibility**: Ensured all tests work reliably on Windows and Unix systems

#### Development Experience
- **One-command setup**: `pip install -e ".[dev]"` installs all development tools
- **Automated code formatting**: Black and isort ensure consistent code style
- **Static analysis**: flake8 and mypy provide comprehensive code quality checks
- **Test automation**: pytest with coverage reporting for quality assurance
- **Documentation support**: Sphinx integration for generating project documentation

### [0.2.2] - 2025-06-29

#### Changed
- **Simplified logger handling**: Removed optional `logger` parameter from all generated methods to always use class-level logger
- **Cleaner API**: Reduced parameter clutter by eliminating the optional logger parameter
- **Consistent logging**: All methods now use the same class-level logger for uniform logging behavior
- **Updated test suite**: Modified tests to reflect the simplified logger approach

#### Technical Improvements
- **Simplified method signatures**: Generated methods now have fewer parameters and cleaner interfaces
- **Consistent logging pattern**: Class-level logger approach follows common Python utility class patterns
- **Reduced complexity**: Eliminated conditional logger assignment logic in generated code
- **Better maintainability**: Generated code is simpler and easier to understand

### [0.2.1] - 2025-06-29

#### Changed
- **Refactored `sql_helper.py`**: Improved error handling and input validation for file operations.
- **Stricter type checks**: Functions now validate input types and raise clear exceptions for invalid arguments.
- **Robust SQL parsing utilities**: Enhanced parsing and comment removal logic for more accurate statement detection and splitting.
- **Improved documentation**: Expanded and clarified docstrings for all helper functions.

### [0.2.0] - 2025-06-28

#### Changed
- **Switched to class-methods-only approach**: Removed instance methods and constructors for better transaction control
- **Removed automatic commit/rollback**: Data modification operations no longer automatically commit or rollback, allowing explicit transaction management
- **Added comprehensive logging**: All operations now include debug and error logging with customizable logger support
- **Improved parameter formatting**: All method parameters are now on separate lines with proper PEP8 formatting
- **Enhanced error handling**: Simplified exception handling without automatic rollback interference

#### Technical Improvements
- **Explicit transaction control**: Users must use `with connection.begin():` blocks for data modifications
- **Better encapsulation**: No shared state between method calls, improving thread safety
- **Named parameters required**: All methods use `*` to force named parameter usage for clarity
- **Class-level logger**: Default logger with optional override per method call
- **Production-ready**: Generated code is now suitable for production use with proper transaction management

#### Generated Code Enhancements
- **Transaction safety**: No automatic commits that could interfere with user-managed transactions
- **Cleaner API**: Class methods only, no instance state to manage
- **Better error propagation**: Exceptions are logged but not automatically rolled back
- **Maintained API compatibility**: Public API remains consistent while improving safety

### [0.1.1] - 2025-06-28

#### Changed
- **Refactored code generator to use Jinja2 templates**: Replaced string concatenation with template-based code generation for better maintainability and flexibility
- **Added Jinja2 dependency**: Added `jinja2>=3.1.0` to requirements.txt
- **Created templates directory**: Added `splurge_sql_generator/templates/` with `python_class.j2` template
- **Simplified code generation logic**: Removed individual method generation functions in favor of template rendering
- **Updated test suite**: Modified tests to work with new template-based approach while maintaining full functionality

#### Technical Improvements
- **Template-based generation**: All Python code is now generated using Jinja2 templates, making it easier to modify output format
- **Better separation of concerns**: Template logic is separated from Python generation logic
- **Maintained API compatibility**: Public API remains unchanged, ensuring backward compatibility
- **Enhanced maintainability**: Code generation format can now be modified by editing templates without touching Python logic

### [0.1.0] - 2025-06-28

#### Added
- Initial release of splurge-sql-generator
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
