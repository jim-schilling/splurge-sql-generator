## Splurge SQL Generator — Simplification and Optimization Plan (2025-08-24)

### Goals
- Reduce complexity across modules while preserving behavior and test stability.
- Clarify responsibilities and public APIs; minimize hidden state and cross-module coupling.
- Improve performance of hot paths (statement detection, parsing, rendering) without premature optimization.
- Keep CLI UX simple: single schema per run with automatic discovery by default.

### Principles
- Single-responsibility per module; no cross-module internal state mutation.
- Favor explicit parameters over implicit discovery inside low-level modules.
- Strong typing and clear error handling via package exceptions.
- Tests validate behavior and patterns, not exact text formatting.

### Current Architecture (summary)
- `sql_helper.py`: comment removal, statement detection, file splitting.
- `sql_parser.py`: extract class name, methods, parameters; classify statements.
- `schema_parser.py`: load SQL→Python type map (YAML), parse `.schema` files.
- `code_generator.py`: orchestrate parse → type/schema → render; Jinja template.
- `cli.py`: arg parsing, input discovery/validation, schema discovery, output.
- `templates/python_class.j2`: class-method-only SQLAlchemy wrapper code.
- `__init__.py`: public exports and convenience functions.

---

### Module-by-Module Plan

#### 1) sql_helper.py
- Cleanup
  - Keep only used constants public: `FETCH_STATEMENT`, `EXECUTE_STATEMENT`.
  - Keep helpers private; remove unused constants and trivial wrappers.
- Performance
  - Fast-path: classify by first significant token (SELECT/INSERT/UPDATE/DELETE/CREATE/ALTER/DROP/VALUES/SHOW/DESC/DESCRIBE/EXPLAIN/PRAGMA).
  - Run CTE walk only when the first token is `WITH`.
- API (stable)
  - Keep: `remove_sql_comments`, `detect_statement_type`, `parse_sql_statements`, `split_sql_file`.
  - Use `SqlFileError`/`SqlValidationError` for I/O and validation.
- Acceptance
  - All existing tests for detection/splitting pass with identical classifications.

#### 2) sql_parser.py
- Scope
  - Parse templates only: class name, methods, parameters; leave typing to schema.
  - Add clearer error messages with file context for invalid identifiers.
- API
  - Keep: `parse_file(path) -> (class_name, method_queries)`.
  - Keep: `get_method_info(sql_query) -> dict` (uses `detect_statement_type`).
  - Add: `parse_string(content) -> (class_name, method_queries)` for programmatic use.
- Acceptance
  - Parser tests pass; new `parse_string` gains unit coverage.

#### 3) schema_parser.py
- Scope and state
  - Add `load_schema(schema_file_path) -> None` to populate internal table map.
  - Stop external mutation of `_table_schemas`; no private attribute pokes.
- Robustness
  - Column line parsing tolerates trailing commas/constraints; ignore non-column lines.
  - Ensure YAML mapping includes `DEFAULT`, else fallback `'Any'`.
- API (final)
  - `load_schema`, `parse_schema_file` (internal use), `get_column_type`, `get_python_type`.
- Acceptance
  - Existing schema tests pass; private-state usage removed from generator tests.

#### 4) code_generator.py
- Responsibility
  - Orchestrate parse → `schema_parser.load_schema(schema_file)` → render; no discovery.
- Simplification
  - Remove `_load_all_schemas` and any direct writes to `_schema_parser._table_schemas`.
  - Centralize parameter preparation in one place.
- Parameter validation (new)
  - Validate that all SQL parameters map to existing table/column combinations in the loaded schema.
  - Raise clear error messages when parameters don't match schema definitions.
  - Keep all parameter types as `Any` (no type inference).
- API (stable)
  - `generate_class(sql_file_path, *, output_file_path | None, schema_file_path) -> str`.
  - `generate_multiple_classes(sql_files, *, output_dir | None, schema_file_path) -> dict[str, str]`.
- Acceptance
  - All parameters must exist in schema; clear error messages for missing table/column combinations.

#### 5) cli.py
- UX/validation
  - Maintain single shared schema per run; keep automatic discovery when `--schema` omitted.
  - Keep `--types/-t` mapping option (defaults to `types.yaml`).
- Structure
  - Extract small helpers for: expanding inputs, discovering schema, and reporting output.
- Acceptance
  - All CLI tests pass; help text and error messages remain pattern-stable.

#### 6) __init__.py
- Public surface
  - Re-export: `PythonCodeGenerator`, `SqlParser`, helpers (`detect_statement_type`, `remove_sql_comments`, `parse_sql_statements`, `split_sql_file`), and conveniences (`generate_class`, `generate_multiple_classes`), plus `is_fetch_statement`/`is_execute_statement`.
- Acceptance
  - Importability tests pass; version and exports unchanged.

#### 7) Parameter validation (new step)
- Scope
  - Add parameter validation to ensure all SQL parameters exist in the loaded schema.
  - Parse SQL to identify table references and parameter usage patterns.
- Implementation
  - Extract table names from FROM, UPDATE, INSERT INTO clauses.
  - Validate that parameters match column names in referenced tables.
  - Raise `SqlValidationError` with clear messages for missing table/column combinations.
- API
  - Add validation method to `code_generator.py` that can be called during generation.
  - Integrate validation into existing generation workflow.
- Acceptance
  - Clear error messages when parameters don't match schema; all valid parameters pass through unchanged.

#### 8) templates/python_class.j2
- Stability
  - Keep class-method-only design and logging.
  - Optionally trim imports if no fetch methods exist (non-breaking; low priority).
- Acceptance
  - Template rendering tests pass; whitespace deltas minimized.

---

### Execution Plan (increments)
1. ✅ Schema ownership
   - Add `SchemaParser.load_schema` and refactor `code_generator` to use it; remove private state mutation.
2. ✅ Generator cleanup
   - Remove `_load_all_schemas`; consolidate parameter preparation; keep outputs stable.
3. ✅ Helper fast-paths
   - Optimize `detect_statement_type` with early classification; retain CTE logic.
4. ✅ Parser ergonomics
   - Added `parse_string`; polished error messages (keep patterns compatible with tests).
5. ✅ CLI refactor (internal)
   - Extracted helpers; no behavior change.
6. ✅ Parameter validation
   - Validated all SQL parameters against loaded schema; ensure table/column combinations exist.

### Testing Strategy
- Run `pytest -x -v --cov` locally; ensure coverage ≥ 85% on public interfaces.
- Add/adjust tests:
  - New: `SchemaParser.load_schema` behavior.
  - New: `SqlParser.parse_string`.
  - New: Parameter validation cases with valid/invalid table/column combinations.
  - Update: Remove any test reliance on private `_table_schemas`.

### Risks and Mitigations
- Risk: Private attribute removal breaks tests.
  - Mitigation: Replace usages with `load_schema`; update tests accordingly.
- Risk: Parameter validation is too strict.
  - Mitigation: Focus on clear error messages; allow override for edge cases.
- Risk: CLI message drift.
  - Mitigation: Maintain pattern-compatible messages; keep examples stable.

### Non-Goals (now)
- Parameter type inference (all parameters remain `Any` type).
- Full SQL AST for complex validation.
- ORM model generation beyond current class-method template.
- Multi-schema merging and resolution.

### Rollback Plan
- All changes are incremental per module; revert by module if tests regress.
- Guard parameter validation behind small functions; disable by skipping validation.

---

## Implementation Status (2025-08-24)

### Completed Steps

#### ✅ Step 1: Schema ownership
- **Added**: `SchemaParser.load_schema(schema_file_path)` method with proper error handling
- **Refactored**: `PythonCodeGenerator` to use `load_schema()` instead of direct private state manipulation
- **Removed**: `_load_all_schemas()` method from code generator
- **Tests**: Added comprehensive tests for new `load_schema` method including error cases
- **Result**: Cleaner separation of concerns; schema loading is now explicit and testable

#### ✅ Step 2: Generator cleanup  
- **Simplified**: Schema handling in `generate_class()` and `generate_multiple_classes()`
- **Removed**: Direct writes to `_schema_parser._table_schemas` 
- **Maintained**: All existing functionality and API compatibility
- **Tests**: All code generator tests pass (12/12); end-to-end workflow tests pass
- **Result**: More maintainable code with clearer responsibility boundaries

#### ✅ Step 3: Helper fast-paths
- **Enhanced**: `detect_statement_type()` with early classification for common SQL keywords
- **Added**: Fast-paths for SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER, DROP, VALUES, SHOW, EXPLAIN, PRAGMA
- **Preserved**: Complex CTE analysis logic for WITH statements
- **Tests**: All 21 statement detection tests pass with identical classifications
- **Result**: Improved performance for common cases while maintaining accuracy for complex queries

#### ✅ Step 4: Parser ergonomics
- **Added**: `SqlParser.parse_string(content, file_path=None)` method for programmatic parsing
- **Enhanced**: Error messages with file context for better debugging
- **Improved**: Class comment validation to accept both `#Class` and `# Class` formats
- **Maintained**: All existing validation rules (valid Python identifiers, no reserved keywords)
- **Tests**: All 25 SQL parser tests pass; added comprehensive tests for new functionality
- **Result**: More flexible parser API with better error reporting and improved usability

#### ✅ Step 5: CLI refactor (internal)
- **Extracted**: `_expand_and_validate_inputs()` helper for input file processing and validation
- **Extracted**: `_discover_schema_file()` helper for schema file discovery logic
- **Extracted**: `_report_generated_classes()` helper for output reporting and dry-run handling
- **Added**: `_to_snake_case()` utility function for filename conversion
- **Maintained**: All existing CLI behavior and error handling patterns
- **Tests**: All 23 CLI tests pass; maintained 93% code coverage
- **Result**: More maintainable CLI code with clearer separation of concerns

#### ✅ Step 6: Parameter validation
- **Added**: `validate_parameters` flag to `PythonCodeGenerator` constructor (default: False)
- **Implemented**: `_extract_table_names()` method to parse SQL queries for table references
- **Implemented**: `_validate_parameters_against_schema()` method for parameter validation
- **Implemented**: `_get_available_columns()` method for helpful error messages
- **Enhanced**: Error messages include file context, referenced tables, and available columns
- **Maintained**: Backward compatibility - validation is opt-in, not enabled by default
- **Tests**: Added comprehensive parameter validation test suite (8/8 tests pass)
- **Result**: Optional strict parameter validation with clear error reporting

### Test Results
- **Code Generator**: 12/12 tests pass ✅
- **Schema Parser**: 20/20 tests pass ✅ (including 2 new tests)
- **Statement Detection**: 21/21 tests pass ✅
- **SQL Parser**: 25/25 tests pass ✅ (including new parse_string tests)
- **CLI**: 23/23 tests pass ✅ (including all refactored functionality)
- **Parameter Validation**: 8/8 tests pass ✅ (new test suite)
- **End-to-End**: 1/1 tests pass ✅
- **Coverage**: Maintained >90% on public interfaces

### Next Steps
All planned simplification and optimization steps have been completed! The codebase has been successfully refactored with:

- ✅ **Schema ownership**: Clean separation of concerns with explicit schema loading
- ✅ **Generator cleanup**: Simplified parameter handling and removed private state mutation
- ✅ **Helper fast-paths**: Optimized statement detection for common SQL keywords
- ✅ **Parser ergonomics**: Added programmatic parsing with improved error messages
- ✅ **CLI refactor**: Extracted helper functions for better maintainability
- ✅ **Parameter validation**: Optional strict validation with clear error reporting

The codebase is now more maintainable, performant, and user-friendly while preserving all existing functionality.


