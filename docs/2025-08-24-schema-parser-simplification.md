## Schema Parser Simplification and Optimization Plan (schema_parser.py)

### Goals
- Reduce complexity and duplication in `schema_parser.py`.
- Leverage `sqlparse` via `splurge_sql_generator.sql_helper` for robust SQL handling.
- Improve correctness across dialects (SQLite, PostgreSQL, MySQL, MSSQL, Oracle).
- Enhance maintainability, testability, and performance.

### Non-Goals
- Implement a full ANSI SQL DDL parser.
- Support every vendor-specific edge case; provide sane fallbacks instead.

### Constraints and Principles
- Prefer `sqlparse`-first approach with a minimal regex fallback.
- Centralize cross-cutting SQL utilities in `sql_helper` (e.g., comment removal).
- Normalize names consistently (lowercase for table and column keys in internal maps).
- Preserve a small public API with clear contracts and type annotations.

### Current Issues (to address)
- Duplicate comment removal (“local” regex and helper) and inconsistent normalization.
- Column parsing relies on simple regex and newline splits; fragile with inline constraints.
- Case-sensitivity mismatch between extracted table names and schema store.
- Scattered error handling; messages not always actionable.

### Target Public API (unchanged where possible)
- `parse_schema_file(schema_file_path: str) -> dict[str, dict[str, str]]`
- `load_schema(schema_file_path: str) -> None`
- `load_schema_for_sql_file(sql_file_path: str, *, schema_file_path: str | None = None) -> None`
- `get_column_type(table_name: str, column_name: str) -> str`
- `get_python_type(sql_type: str) -> str`
- `table_schemas` property (read-only mapping)

### High-Level Design
1. Comment handling: delegate to `sql_helper.remove_sql_comments()`.
2. Statement detection: use `sqlparse.parse()` to isolate `CREATE TABLE` statements; fallback to bounded regex if parsing fails.
3. Column list extraction:
   - Tokenize statement body; consume balanced parentheses to isolate the column list.
   - Split columns by top-level commas only (paren depth = 0).
   - Skip non-column definitions (PRIMARY KEY, FOREIGN KEY, UNIQUE, CHECK, CONSTRAINT, INDEX).
4. Column type capture:
   - Extract raw SQL type token sequence for each column; normalize by removing size/precision `(… )`.
   - Convert to uppercase for mapping; store columns under lowercase names.
5. Type mapping:
   - Load YAML types (`types.yaml`) with safe defaults; validate mapping structure.
   - `get_python_type()` performs normalized lookup with fallback to `DEFAULT: Any`.
6. Case normalization:
   - Store tables and columns in lowercase; callers can pass either case.
7. Error handling:
   - Clear `FileNotFoundError` for missing schema; YAML errors downgraded to warnings with defaults.
8. Performance (optional):
   - Add lightweight cache keyed by file path + mtime to avoid re-parsing unchanged schemas.

### Step-by-Step Implementation Plan
1. ✅ Replace any local comment removal logic with `sql_helper.remove_sql_comments()`.
2. ✅ Implement `CREATE TABLE` detection using `sqlparse.parse()`:
    - Walk tokens to find `CREATE` → `TABLE` sequences and capture the identifier and parenthesized body.
    - If `sqlparse` fails, raise SqlValidationError instead of regex fallback.
3. ✅ Rework column extraction logic to top-level comma splitter:
   - Replace character-by-character iteration with sqlparse token-based parsing.
   - Implement `_split_by_top_level_commas()` to handle nested parentheses correctly.
   - Extract column names and types using `_extract_column_name_and_type()`.
   - Skip constraint definitions (PRIMARY KEY, FOREIGN KEY, etc.).
4. ✅ Improve type extraction:
   - For each column `part`, take first identifier as column name; next contiguous identifiers form type.
   - Normalize to uppercase; strip `(N[,M])` suffix.
   - Store as `tables[table_name_lower][column_name_lower] = normalized_sql_type`.
   - Ensure `get_column_type()` accepts any case and resolves to lowercase keys.
5. ✅ Validate YAML mapping loading with clear warnings; ensure `DEFAULT` exists (fallback to `Any`).
6. ✅ Tighten exceptions and messages (user-actionable, include file path).
7. ✅ Keep function signatures and typings consistent with user rules (PEP8, docstrings).

### Testing Strategy
- Unit tests per dialect: verify type mapping of representative column types.
- Edge cases:
  - Inline constraints; composite keys; multiple UNIQUE/FOREIGN KEY lines.
  - Mixed case and quoted identifiers (`"Users"`, `\`users\``).
  - Inline and block comments; comments within strings unaffected.
- Property-like fuzz: random whitespace, ordering of constraints, extra commas.
- Performance: large schema file with 100+ tables parses under time budget.

### Integration Plan
- Confirm `code_generator` uses `SchemaParser` API only; no internal access.
- Ensure table name extraction (helper) returns lowercase to match schema store.
- Update README with notes on casing and supported DDL shapes; add changelog entry.

### Rollout and Risk Mitigation
- Phase behind a feature flag if necessary (env var) for quick rollback.
- Preserve regex fallback path if `sqlparse` token walk fails on exotic DDL.
- Add telemetry-level debug logging behind logger debug level (off by default).

### Timeline (suggested)
- Day 1: Refactor comment handling, casing normalization, unit tests.
- Day 2: Implement token-based column extraction, update tests, fix edge cases.
- Day 3: Add cache option, performance test, docs, and changelog.

### Acceptance Criteria
- All tests pass; coverage ≥ 85% for public methods.
- Correct types inferred for sample schemas in `examples/` and tests.
- Robust to common dialect variations; graceful fallback to `Any` where unknown.


