## Changelog

### [2025.5.0] - 2025-10-19

#### Added
- Centralized Safe I/O adapter: introduced `SafeTextFileIoAdapter` in `splurge_sql_generator.file_utils` and migrated internal modules to use the adapter for consistent error translation and simplified file I/O.
- Comprehensive API and CLI reference docs:
  - `docs/api/API-REFERENCE.md`
  - `docs/cli/CLI-REFERENCE.md`

#### Changed
- Replaced direct usage of `splurge_safe_io.safe_text_file_reader.SafeTextFileReader` and `splurge_safe_io.safe_text_file_writer.SafeTextFileWriter` with the `SafeTextFileIoAdapter` across the codebase (modules updated: `sql_helper.py`, `sql_parser.py`, `schema_parser.py`, `code_generator.py`).
- Renamed module `splurge_sql_generator.types` → `splurge_sql_generator.type_definitions` to avoid shadowing the Python standard library `types` module.

#### Fixed
- Improved cross-version compatibility (Python 3.11/3.12) by normalizing error messages and adding explicit validation for `None` schema file paths.

#### Technical Improvements
- Simplified exception mapping by centralizing file I/O errors in the adapter; reduced duplication and improved maintainability.
- Added comprehensive docs and examples for API and CLI usage, and updated tests to match standardized error messages.

### [2025.4.6] - 2025-09-03

#### Added
- More comprehensive test coverage:
  - Unit tests for `splurge_sql_generator.utils` (file operations, identifier validation, normalization utilities)
  - End-to-end CLI tests covering multi-file generation with a single shared `--schema`, `--dry-run` output, and `--generate-types`
  - Schema parser edge-case tests to harden behavior and raise coverage:
    - YAML mapping validation (filters non-string values, ensures `DEFAULT` exists)
    - Fallback to default mapping on invalid YAML or non-dict content
    - Error propagation tests for `parse_schema_file` (UnicodeDecodeError, OSError, malformed SQL)
    - Case-insensitive lookups for `get_column_type`
    - Explicit `schema_file_path` override in `load_schema_for_sql_file`

#### Changed
- CLI internals modernized to Python 3.10+ typing:
  - Replaced `Optional[...]` with `| None`
  - Reformatted multi-parameter function signatures to multiline per method standards
- Documentation clarified for schema loading:
  - Explicit `schema_file_path` in APIs takes precedence over derived `.schema` files
  - YAML mapping behavior documented: non-string entries ignored; `DEFAULT` ensured

#### Fixed
- Snake case conversion for all-uppercase acronyms (e.g., `API` → `api`) in `to_snake_case`
- Test portability improvements (OS-agnostic path assertions in utils tests)
- Correct UnicodeDecodeError re-raise in `utils.safe_read_file` to use proper constructor signature, with clearer context message

#### Technical Improvements
- Consistency with project standards (absolute imports, method formatting)
- Strengthened end-to-end validation of CLI workflows and reporting
- Increased module coverage (approximate): `schema_parser.py` ~96%, overall ~94%

### [2025.4.5] - 2025-08-25

#### Added
- **Enhanced Table Name Extraction**: Comprehensive support for various table name formats in CREATE TABLE statements
- **Schema Prefix Support**: Full support for schema-qualified table names (e.g., `my_schema.mytable`)
- **IF NOT EXISTS Support**: Proper handling of `CREATE TABLE IF NOT EXISTS` statements
- **Quoted Identifier Support**: Support for all major SQL identifier quoting styles:
  - Bracketed identifiers: `[mytable]`, `[myschema].[mytable]`
  - Backtick identifiers: `` `mytable` ``, `` `myschema`.`mytable` ``
  - Double-quoted identifiers: `"mytable"`, `"myschema"."mytable"`
- **Comprehensive Test Coverage**: Added 9 new test cases covering all table name extraction variants

#### Enhanced
- **SQL Parser Robustness**: Improved `_extract_create_table_components()` function to handle complex table name patterns
- **Identifier Normalization**: New `_extract_identifier_name()` helper function for consistent handling of quoted identifiers
- **Schema Parser Accuracy**: More reliable table name extraction from diverse SQL dialects and conventions

#### Technical Improvements
- **Token-Based Parsing**: Enhanced sqlparse token analysis for accurate table name extraction
- **Schema Prefix Handling**: Proper parsing of dot-separated schema.table combinations
- **Quote Style Detection**: Automatic detection and handling of different identifier quoting conventions
- **Error Handling**: Robust error handling for malformed CREATE TABLE statements

#### Supported Table Name Formats
```sql
-- Basic table names
CREATE TABLE mytable (id TEXT PRIMARY KEY);

-- IF NOT EXISTS variants
CREATE TABLE IF NOT EXISTS mytable (id TEXT PRIMARY KEY);

-- Schema prefixes
CREATE TABLE my_schema.mytable (id TEXT PRIMARY KEY);

-- Bracketed identifiers (SQL Server style)
CREATE TABLE [mytable] (id TEXT PRIMARY KEY);
CREATE TABLE [myschema].[mytable] (id TEXT PRIMARY KEY);

-- Backtick identifiers (MySQL style)
CREATE TABLE `mytable` (id TEXT PRIMARY KEY);
CREATE TABLE `myschema`.`mytable` (id TEXT PRIMARY KEY);

-- Double-quoted identifiers (PostgreSQL style)
CREATE TABLE "mytable" (id TEXT PRIMARY KEY);
CREATE TABLE "myschema"."mytable" (id TEXT PRIMARY KEY);

-- Mixed quoting styles
CREATE TABLE [myschema].`mytable` (id TEXT PRIMARY KEY);
```

### [2025.4.4] - 2025-08-24

#### Changed
- **Enhanced Error Handling**: Removed fallback mechanisms in `sql_helper.py` functions to ensure robust error handling
- **Stricter SQL Parsing**: `parse_table_columns()` and `extract_table_names()` now raise `SqlValidationError` when sqlparse fails instead of falling back to regex-based parsing
- **Improved Code Quality**: Eliminated unreliable fallback parsing in favor of clear error reporting
- **Better Test Coverage**: Added comprehensive test coverage for `sql_helper.py` with 55 tests achieving 90% code coverage

#### Technical Improvements
- **Removed Fallback Functions**: Eliminated `_parse_table_columns_fallback()` and `_extract_tables_with_regex()` functions
- **Enhanced Error Messages**: Functions now provide clear error messages when SQL parsing fails
- **Robust Validation**: Added validation to ensure valid column definitions and table names are found
- **Comprehensive Testing**: Added extensive test suite covering edge cases, error conditions, and integration scenarios

#### Behavior Changes
- **`parse_table_columns()`**: Now raises `SqlValidationError` when:
  - sqlparse fails to parse the table body
  - No valid column definitions are found (e.g., only constraint definitions)
- **`extract_table_names()`**: Now raises `SqlValidationError` when:
  - sqlparse fails to parse the SQL query
  - No table names are found in the query (e.g., `SELECT 1 as value`)

#### Development Experience
- **Fail-Fast Approach**: Functions now fail fast with clear error messages rather than attempting unreliable fallback parsing
- **Better Debugging**: Clear error messages help developers identify and fix SQL parsing issues
- **Improved Reliability**: Eliminates potential for incorrect parsing results from fallback mechanisms
- **Enhanced Maintainability**: Simplified codebase with fewer edge cases and fallback paths

### [2025.4.3] - 2025-08-24

#### Added
- **Intelligent Type Inference**: Automatic parameter type detection based on SQL schema, parameter naming patterns, and SQL context
- **Enhanced SQL Parsing**: Consolidated SQL parsing logic using `sqlparse` library for more accurate table name extraction
- **Advanced Table Name Extraction**: Sophisticated table name extraction from complex SQL constructs including CTEs, subqueries, and aliases
- **Pattern-Based Type Inference**: Smart type detection based on parameter naming conventions (e.g., `_id` → `int`, `_price` → `float`, `_term` → `str`)

#### Changed
- **Parameter Types**: Generated parameters now use specific Python types instead of `Any` based on intelligent inference
- **SQL Parser Architecture**: Refactored to leverage `sql_helper` functionality for better code organization
- **Type Inference Logic**: Replaced hardcoded `Any` types with sophisticated type inference system
- **Code Generator**: Enhanced to use schema information and SQL context for accurate type determination

#### Enhanced
- **Code Quality**: Generated code now has proper type annotations for better IDE support and static analysis
- **SQL Parsing Accuracy**: More reliable table name extraction from complex SQL queries
- **Developer Experience**: Better type hints in generated code improve development workflow
- **Schema Integration**: Deeper integration between SQL queries and schema definitions for type inference

#### Technical Improvements
- **Type Inference Algorithm**: Multi-layered approach combining schema lookup, pattern matching, and SQL context analysis
- **Table Name Extraction**: Uses `sqlparse` for parsing FROM, JOIN, UPDATE, INSERT INTO clauses with fallback to regex
- **Schema-Based Inference**: Matches parameter names against schema column names for exact type mapping
- **Pattern-Based Fallback**: Intelligent fallback using common parameter naming conventions
- **SQL Context Analysis**: Analyzes SQL query structure to infer types from WHERE clauses and comparisons

#### Usage Examples
```python
# Generated code now has proper type annotations
class ProductRepository:
    def get_product_by_id(self, product_id: int) -> dict[str, Any] | None:
        """Retrieves a product by its ID."""
        query = "SELECT * FROM products WHERE id = :product_id"
        return self.connection.fetch_one(query, {"product_id": product_id})
    
    def search_products(self, search_term: str) -> list[dict[str, Any]]:
        """Searches for products by name or description."""
        query = "SELECT * FROM products WHERE name LIKE :search_term"
        return self.connection.fetch_all(query, {"search_term": f"%{search_term}%"})
```

#### Type Inference Features
- **Schema-Based**: Uses schema column types (INTEGER → `int`, TEXT → `str`, DECIMAL → `float`)
- **Pattern-Based**: Recognizes common patterns (`_id` → `int`, `_price` → `float`, `_term` → `str`)
- **Context-Based**: Analyzes SQL WHERE clauses and comparisons for type hints
- **Fallback Strategy**: Gracefully falls back to `Any` when type cannot be determined

### [2025.4.2] - 2025-08-24

#### Added
- **Type File Generation**: New `--generate-types` CLI option to generate default SQL type mapping files
- **Parameter Validation**: Optional validation of SQL parameters against schema definitions with `validate_parameters=True`
- **Programmatic Type Generation**: `generate_types_file()` function for generating type mapping files programmatically
- **Enhanced Error Messages**: Clear error reporting when parameters don't match schema definitions
- **Comprehensive Type Coverage**: Generated type files include SQLite, PostgreSQL, MySQL, MSSQL, and Oracle types

#### Changed
- **CLI Enhancement**: Added `--generate-types [TYPES_FILE]` option for generating default type mapping files
- **Code Generator**: Added `validate_parameters` parameter to `PythonCodeGenerator` constructor
- **Schema Parser**: Added `generate_types_file()` method for creating type mapping files
- **API Exports**: Added `SchemaParser` and `generate_types_file` to public API exports

#### Enhanced
- **User Experience**: Users can now generate starter type mapping files for customization
- **Parameter Safety**: Optional validation ensures SQL parameters exist in referenced tables
- **Type Organization**: Generated type files are organized by database with helpful comments
- **Backward Compatibility**: All existing functionality continues to work unchanged

#### Technical Improvements
- **Parameter Validation Logic**: Added `_extract_table_names()` and `_validate_parameters_against_schema()` methods
- **Error Context**: Enhanced error messages include file paths, referenced tables, and available columns
- **Type File Structure**: Generated files include comprehensive type mappings organized by database
- **Test Coverage**: Added comprehensive tests for type generation and parameter validation functionality

#### Usage Examples
```bash
# Generate default types.yaml in current directory
python -m splurge_sql_generator.cli --generate-types

# Generate custom types file
python -m splurge_sql_generator.cli --generate-types my_types.yaml

# Use parameter validation
python -c "
from splurge_sql_generator import PythonCodeGenerator
generator = PythonCodeGenerator(validate_parameters=True)
# ... generate code with validation
"
```

#### Parameter Validation Features
- **Table Extraction**: Automatically extracts table names from FROM, UPDATE, INSERT INTO, and JOIN clauses
- **Schema Validation**: Validates that SQL parameters exist as columns in referenced tables
- **Clear Error Messages**: Reports invalid parameters with context about available columns
- **Optional Feature**: Validation is disabled by default to maintain backward compatibility

### [2025.4.1] - 2025-08-24

#### Added
- **Automatic Schema Discovery**: CLI now automatically searches for `*.schema` files when no `--schema` option is specified
- **Smart Schema Location Detection**: Searches for schema files in the current directory and directories containing SQL files being processed
- **Improved User Experience**: Users no longer need to explicitly specify schema files when they follow common naming conventions

#### Changed
- **CLI Schema Handling**: Updated CLI to automatically find schema files using `_find_schema_files()` function
- **Schema File Requirements**: Schema files are still mandatory, but the CLI now helps users locate them automatically
- **Error Messages**: Enhanced error messages to guide users when no schema files are found

#### Enhanced
- **CLI Flexibility**: Users can still explicitly specify schema files with `--schema` for full control
- **Backward Compatibility**: All existing CLI usage patterns continue to work unchanged
- **Test Coverage**: Added comprehensive tests for automatic schema discovery functionality

#### Technical Improvements
- **CLI Logic**: Added `_find_schema_files()` helper function for intelligent schema file discovery
- **Code Generator**: Simplified schema handling by making `schema_file_path` a required parameter
- **API Consistency**: Updated convenience functions in `__init__.py` to include schema file parameters
- **Error Handling**: Clear error messages when no schema files are found in expected locations

#### Usage Examples
```bash
# Automatic schema discovery (finds *.schema files automatically)
python -m splurge_sql_generator.cli examples/User.sql --dry-run

# Multiple files with automatic schema discovery
python -m splurge_sql_generator.cli examples/*.sql --output generated/

# Still works with explicit schema specification
python -m splurge_sql_generator.cli examples/User.sql --schema custom.schema --dry-run
```

#### Schema Discovery Behavior
- **Search Locations**: Current directory and directories containing SQL files
- **File Pattern**: Looks for `*.schema` files (e.g., `User.schema`, `OrderService.schema`)
- **Selection**: Uses the first schema file found in the search order
- **Fallback**: Clear error message if no schema files are found
- **Override**: `--schema` option always takes precedence over automatic discovery

### [2025.4.0] - 2025-08-23

#### Added
- **Custom SQL Type Mapping**: New CLI option `--types` / `-t` to specify custom SQL type mapping YAML files
- **Schema-Based Type Inference**: Enhanced type inference system using dedicated schema files (`.schema`) for accurate Python type annotations
- **Comprehensive Database Support**: Added support for MSSQL and Oracle-specific SQL types in addition to existing SQLite, PostgreSQL, and MySQL support
- **Case-Insensitive Type Lookups**: SQL type matching now works regardless of case (e.g., `INTEGER`, `integer`, `Integer` all work)
- **Schema File Requirements**: Schema files are now mandatory for code generation, ensuring consistent type inference

#### Changed
- **CLI Option Names**: Updated `-st | --sql-types` to `-t | --types` for better consistency
- **Default Type Mapping File**: Changed default from `sql-types.yaml` to `types.yaml` for cleaner naming
- **Schema File Extension**: Updated schema file lookup from `*.sql.schema` to `*.schema` for simpler naming
- **Schema File Requirements**: Made schema files mandatory - code generation now requires at least one schema file to be present

#### Enhanced
- **CLI Flexibility**: Users can now specify custom type mappings per project using `--types custom_types.yaml`
- **Type Mapping Configuration**: Sortable and maintainable `types.yaml` file with alphabetical ordering and `DEFAULT` fallback
- **Schema Parser Improvements**: Enhanced schema parsing with better error handling and fallback mechanisms
- **Test Coverage**: Added comprehensive tests for custom type mapping functionality and schema file requirements
- **Test Organization**: Refactored test modules to follow "one test class per module" principle for better maintainability

#### Technical Improvements
- **PythonCodeGenerator**: Updated to accept `sql_type_mapping_file` parameter for custom type mappings
- **SchemaParser**: Enhanced with Oracle types in default mapping for better fallback support
- **CLI Integration**: Seamless integration of custom type mapping files with existing CLI workflow
- **Schema Validation**: Enhanced schema file validation with clear error messages for missing schema files
- **Test Utilities**: Fixed schema file naming in test utilities to match expected patterns

#### Usage Examples
```bash
# Use default types.yaml
python -m splurge_sql_generator.cli examples/User.sql --dry-run

# Use custom type mapping file (long form)
python -m splurge_sql_generator.cli examples/User.sql --dry-run --types custom_types.yaml

# Use custom type mapping file (short form)
python -m splurge_sql_generator.cli examples/User.sql --dry-run -t custom_types.yaml

# Use shared schema file for multiple SQL files
python -m splurge_sql_generator.cli *.sql --output generated/ --schema User.schema
```

#### Database Type Support
- **SQLite**: INTEGER, TEXT, REAL, BLOB, etc.
- **PostgreSQL**: JSON, JSONB, UUID, SERIAL, BIGSERIAL, etc.
- **MySQL**: TINYINT, MEDIUMINT, LONGTEXT, ENUM, etc.
- **MSSQL**: BIT, MONEY, NVARCHAR, UNIQUEIDENTIFIER, XML, SQL_VARIANT, etc.
- **Oracle**: NUMBER, VARCHAR2, CLOB, RAW, ROWID, INTERVAL, etc.

#### Development Experience
- **Custom Type Definitions**: Projects can define application-specific SQL types and their Python mappings
- **Type Consistency**: Ensures consistent type inference across different database dialects
- **Project Flexibility**: Different projects can use different type mapping strategies
- **Maintainable Configuration**: YAML-based configuration for easy type mapping management
- **Schema File Management**: Support for both individual schema files and shared schema files across multiple SQL files

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
