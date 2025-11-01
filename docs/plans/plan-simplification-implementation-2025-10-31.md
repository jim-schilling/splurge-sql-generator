# Implementation Plan: Simplification Improvements

**Date:** October 31, 2025  
**Version:** 2025.6.0+  
**Branch:** `feature/simplification-improvements`  
**Status:** Ready for Implementation  
**Source:** Based on `docs/research/research-design-review.md`

---

## Overview

This plan implements the five simplification recommendations identified in the design review to improve maintainability and reduce duplication in the `splurge-sql-generator` package.

**Total Estimated Effort:** ~9-10 hours  
**Risk Level:** LOW (internal refactoring, type-only changes)  
**Impact:** Medium (improved maintainability, reduced duplication)

---

## Requirements

### Functional Requirements
1. All existing functionality must be preserved
2. All existing tests must continue to pass
3. Type safety must be maintained or improved
4. Public API must remain unchanged

### Non-Functional Requirements
1. Code must pass mypy with 0 errors
2. Code must pass ruff linting
3. Test coverage must not decrease
4. Performance must not regress

### Acceptance Criteria
- [ ] All 235+ existing tests pass
- [ ] mypy reports 0 errors
- [ ] ruff reports 0 issues
- [ ] Test coverage maintains or improves
- [ ] No breaking changes to public API
- [ ] Code duplication reduced
- [ ] Type safety improved

---

## Testing Strategy

### Unit Tests
- Each new function/module must have unit tests
- Test both happy paths and error conditions
- Maintain or improve existing test coverage

### Integration Tests
- Verify end-to-end workflows still work
- Test with real SQL files and schemas
- Verify generated code is unchanged

### Validation Steps
1. Run `pytest -v` - all tests must pass
2. Run `mypy splurge_sql_generator` - must return 0 errors
3. Run `ruff check .` - must return 0 errors
4. Run `pytest --cov=splurge_sql_generator --cov-report=term-missing` - check coverage
5. Run integration tests with examples

---

## Implementation Stages

---

## Stage 1: Extract Token Navigation Helpers

**Priority:** MEDIUM  
**Estimated Effort:** 2-3 hours  
**Risk:** LOW

### Objective
Reduce duplication in token navigation patterns by extracting helper functions that handle `None` checks automatically.

### Stage 1.1: Create Token Navigation Helper Functions

**Location:** `splurge_sql_generator/sql_helper.py`

**Tasks:**
- [x] **Task-1.1.1:** Add `require_next_token()` helper function
  - [x] Function signature: `require_next_token(tokens: list[Token], start: int, description: str = "token") -> tuple[int, Token]`
  - [x] Calls `_next_significant_token()` internally
  - [x] Raises `SplurgeSqlGeneratorTokenizationError` if token not found
  - [x] Include clear error message with description
  - [x] Add docstring explaining purpose and usage
  - [x] Add type hints

- [x] **Task-1.1.2:** Add `require_token_at()` helper function (alternative pattern)
  - [x] Function signature: `require_token_at(tokens: list[Token], index: int, description: str = "token") -> Token`
  - [x] Similar to `require_next_token()` but returns Token directly (not tuple)
  - [x] Useful for cases where index tracking isn't needed
  - [x] Add docstring and type hints

- [x] **Task-1.1.3:** Add unit tests for new helper functions
  - [x] Test `require_next_token()` with valid tokens
  - [x] Test `require_next_token()` with no tokens found (should raise)
  - [x] Test `require_next_token()` with only whitespace/comments (should raise)
  - [x] Test `require_token_at()` with valid tokens
  - [x] Test `require_token_at()` with no tokens found (should raise)
  - [x] Verify error messages are descriptive

**Files to Modify:**
- `splurge_sql_generator/sql_helper.py`

**Files to Create:**
- `tests/unit/test_sql_helper_token_navigation.py` (new test file)

### Stage 1.2: Refactor Functions to Use New Helpers

**Location:** `splurge_sql_generator/sql_helper.py`

**Tasks:**
- [x] **Task-1.2.1:** Refactor `find_main_statement_after_with()`
  - [x] Identify all `_next_significant_token()` calls
  - [x] Replace with `require_next_token()` or `require_token_at()` where appropriate
  - [x] Remove `None` checks that are no longer needed
  - [x] Update error handling if needed
  - [x] Verify logic unchanged (test-driven)

- [x] **Task-1.2.2:** Refactor `_extract_create_table_components()`
  - [x] Identify all `_next_significant_token()` calls (~8-10 occurrences)
  - [x] Replace with new helpers (where appropriate - some kept for None return pattern)
  - [x] Simplify nested conditionals where possible
  - [x] Remove redundant `None` checks
  - [x] Verify functionality unchanged

- [x] **Task-1.2.3:** Refactor `parse_table_columns()` if applicable
  - [x] Check for token navigation patterns
  - [x] Apply new helpers if appropriate (not applicable)
  - [x] Maintain existing behavior

- [x] **Task-1.2.4:** Update any other functions using `_next_significant_token()`
  - [x] Search codebase for all usages
  - [x] Apply helpers consistently (applied in detect_statement_type)
  - [x] Document any cases where original pattern is kept (with rationale)

**Files to Modify:**
- `splurge_sql_generator/sql_helper.py`

### Stage 1.3: Validation and Testing

**Tasks:**
- [ ] **Task-1.3.1:** Run existing tests
  - [ ] `pytest tests/unit/test_sql_helper.py -v`
  - [ ] `pytest tests/integration/test_*.py -v`
  - [ ] All tests must pass

- [ ] **Task-1.3.2:** Run type checking
  - [ ] `mypy splurge_sql_generator/sql_helper.py`
  - [ ] Must return 0 errors

- [ ] **Task-1.3.3:** Run linting
  - [ ] `ruff check splurge_sql_generator/sql_helper.py`
  - [ ] Must return 0 errors

- [ ] **Task-1.3.4:** Verify test coverage
  - [ ] `pytest --cov=splurge_sql_generator/sql_helper --cov-report=term-missing`
  - [ ] Coverage should maintain or improve

- [ ] **Task-1.3.5:** Integration test
  - [ ] Generate code from example SQL files
  - [ ] Verify generated code is identical to before refactoring
  - [ ] Test with complex SQL (CTEs, nested queries)

**Acceptance Criteria:**
- [ ] All existing tests pass
- [ ] New helper functions have unit tests
- [ ] Code duplication reduced (fewer `None` checks)
- [ ] Error messages are clearer
- [ ] No functionality changes
- [ ] mypy and ruff pass

---

## Stage 2: Consolidate Identifier Extraction

**Priority:** LOW  
**Estimated Effort:** 30 minutes  
**Risk:** NONE

### Objective
Remove duplication between `extract_identifier_name()` and `_extract_identifier_name()` by using a single implementation.

### Stage 2.1: Analyze Duplication

**Tasks:**
- [x] **Task-2.1.1:** Compare `extract_identifier_name()` and `_extract_identifier_name()`
  - [x] Document differences (if any)
  - [x] Identify which implementation is more complete
  - [x] Note all call sites for each function

**Files to Review:**
- `splurge_sql_generator/sql_helper.py`

### Stage 2.2: Consolidate to Single Function

**Tasks:**
- [x] **Task-2.2.1:** Choose primary implementation
  - [x] Select most complete version (likely `extract_identifier_name()`)
  - [x] Enhance if needed to handle all cases from both versions

- [x] **Task-2.2.2:** Remove duplicate function
  - [x] Delete `_extract_identifier_name()` (private version)
  - [x] Keep `extract_identifier_name()` as public function
  - [x] Update all call sites to use `extract_identifier_name()`

- [x] **Task-2.2.3:** Update call sites
  - [x] Find all calls to `_extract_identifier_name()`
  - [x] Replace with `extract_identifier_name()`
  - [x] Verify no functionality changes

- [x] **Task-2.2.4:** Enhance function if needed
  - [x] Ensure all quote styles are handled: `[identifier]`, `` `identifier` ``, `"identifier"`
  - [x] Add unit test for each quote style (existing tests cover this)
  - [x] Test with unquoted identifiers

**Files to Modify:**
- `splurge_sql_generator/sql_helper.py`

**Files to Update:**
- `tests/unit/test_sql_helper.py` (ensure coverage)

### Stage 2.3: Validation and Testing

**Tasks:**
- [ ] **Task-2.3.1:** Run existing tests
  - [ ] `pytest tests/unit/test_sql_helper.py -v`
  - [ ] All tests must pass

- [ ] **Task-2.3.2:** Run type checking
  - [ ] `mypy splurge_sql_generator/sql_helper.py`
  - [ ] Must return 0 errors

- [ ] **Task-2.3.3:** Verify no duplicate implementations remain
  - [ ] Search codebase for similar identifier extraction logic
  - [ ] Consolidate if found

**Acceptance Criteria:**
- [ ] Single identifier extraction function exists
- [ ] All call sites updated
- [ ] All existing tests pass
- [ ] Duplication eliminated
- [ ] Function handles all quote styles

---

## Stage 3: Extract Type Inference Logic

**Priority:** MEDIUM  
**Estimated Effort:** 3-4 hours  
**Risk:** LOW

### Objective
Extract type inference logic from `code_generator.py` into a separate module/class for better separation of concerns and testability.

### Stage 3.1: Create Type Inference Module

**Tasks:**
- [x] **Task-3.1.1:** Create new file `splurge_sql_generator/type_inference.py`
  - [x] Add module docstring
  - [x] Add `DOMAINS = ["type", "inference"]`
  - [x] Import necessary dependencies

- [x] **Task-3.1.2:** Create `ParameterTypeInferrer` class
  - [x] Class docstring explaining purpose
  - [x] `__init__` method accepting schema_parser (or table_schemas dict)
  - [x] Store schema reference as instance variable

- [x] **Task-3.1.3:** Extract `infer()` method (main entry point)
  - [x] Signature: `infer(self, sql_query: str, parameter: str) -> str`
  - [x] Implement fallback chain:
    1. Call `_exact_match()`
    2. If None, call `_sql_context_match()`
    3. If None, call `_name_heuristics()`
  - [x] Return default "Any" if all fail
  - [x] Add docstring with examples

- [x] **Task-3.1.4:** Extract `_exact_match()` method
  - [x] Copy logic from `code_generator._infer_parameter_type()` (exact match section)
  - [x] Signature: `_exact_match(self, parameter: str, table_names: list[str]) -> str | None`
  - [x] Extract table names from schema
  - [x] Match parameter to column name
  - [x] Return Python type or None
  - [x] Add docstring

- [x] **Task-3.1.5:** Extract `_sql_context_match()` method
  - [x] Copy logic from `code_generator._infer_type_from_sql_context()`
  - [x] Signature: `_sql_context_match(self, sql_query: str, parameter: str, table_names: list[str]) -> str | None`
  - [x] Keep regex patterns for WHERE/SET clauses
  - [x] Match parameter usage in SQL context
  - [x] Return Python type or None
  - [x] Add docstring

- [x] **Task-3.1.6:** Extract `_name_heuristics()` method
  - [x] Copy logic from `code_generator._infer_type_from_parameter_name()`
  - [x] Signature: `_name_heuristics(self, parameter: str) -> str`
  - [x] Keep parameter naming pattern matching
  - [x] Return inferred type (default "Any")
  - [x] Add docstring

- [x] **Task-3.1.7:** Add helper method `_get_table_names_from_sql()`
  - [x] Extract table names from SQL query
  - [x] Reuse `code_generator._extract_table_names()` logic or import from sql_helper
  - [x] Returns list of table names

- [x] **Task-3.1.8:** Add helper method `_get_python_type_from_schema()`
  - [x] Lookup SQL type in schema (done via schema_parser method calls)
  - [x] Convert to Python type using schema_parser method
  - [x] Returns Python type string

**Files to Create:**
- `splurge_sql_generator/type_inference.py`

### Stage 3.2: Create Unit Tests for Type Inference

**Tasks:**
- [x] **Task-3.2.1:** Create test file `tests/unit/test_type_inference.py`
  - [x] Import `ParameterTypeInferrer`
  - [x] Set up test fixtures (mock schema, test data)

- [x] **Task-3.2.2:** Test `infer()` method
  - [x] Test exact match (parameter matches column name)
  - [x] Test SQL context match (parameter in WHERE clause)
  - [x] Test name heuristics (parameter name patterns)
  - [x] Test fallback to "Any"
  - [x] Test with empty schema
  - [x] Test with multiple tables

- [x] **Task-3.2.3:** Test `_exact_match()` method
  - [x] Test successful match
  - [x] Test no match found
  - [x] Test with multiple tables

- [x] **Task-3.2.4:** Test `_sql_context_match()` method
  - [x] Test WHERE clause matching
  - [x] Test SET clause matching
  - [x] Test various operators (=, <, >, LIKE, IN)
  - [x] Test no match found

- [x] **Task-3.2.5:** Test `_name_heuristics()` method
  - [x] Test ID patterns (`_id`, `id`)
  - [x] Test quantity patterns
  - [x] Test price/cost patterns
  - [x] Test name/title patterns
  - [x] Test boolean patterns
  - [x] Test unknown patterns (returns "Any")

**Files to Create:**
- `tests/unit/test_type_inference.py`

### Stage 3.3: Refactor code_generator.py to Use New Module

**Tasks:**
- [x] **Task-3.3.1:** Update imports in `code_generator.py`
  - [x] Import `ParameterTypeInferrer` from `type_inference`
  - [x] Remove unused imports if any (removed `import re`)

- [x] **Task-3.3.2:** Update `__init__` method
  - [x] Create `ParameterTypeInferrer` instance
  - [x] Store as `self._type_inferrer`
  - [x] Pass schema_parser reference to inferrer

- [x] **Task-3.3.3:** Replace `_infer_parameter_type()` calls
  - [x] Find all call sites
  - [x] Replace with `self._type_inferrer.infer(sql_query, parameter)`
  - [x] Verify behavior unchanged

- [x] **Task-3.3.4:** Remove old methods
  - [x] Delete `_infer_parameter_type()`
  - [x] Delete `_infer_type_from_sql_context()`
  - [x] Delete `_infer_type_from_parameter_name()`
  - [x] Delete `_extract_table_names()` (no longer needed)
  - [x] Keep `_get_available_columns()` (still needed)

- [x] **Task-3.3.5:** Update method calls in `_prepare_method_data()`
  - [x] Replace type inference logic
  - [x] Verify parameter types still work correctly

**Files to Modify:**
- `splurge_sql_generator/code_generator.py`

### Stage 3.4: Validation and Testing

**Tasks:**
- [ ] **Task-3.4.1:** Run existing tests
  - [ ] `pytest tests/unit/test_code_generator.py -v`
  - [ ] `pytest tests/integration/test_*.py -v`
  - [ ] All tests must pass

- [ ] **Task-3.4.2:** Run new type inference tests
  - [ ] `pytest tests/unit/test_type_inference.py -v`
  - [ ] All new tests must pass

- [ ] **Task-3.4.3:** Run type checking
  - [ ] `mypy splurge_sql_generator/type_inference.py`
  - [ ] `mypy splurge_sql_generator/code_generator.py`
  - [ ] Must return 0 errors

- [ ] **Task-3.4.4:** Run linting
  - [ ] `ruff check splurge_sql_generator/type_inference.py`
  - [ ] `ruff check splurge_sql_generator/code_generator.py`
  - [ ] Must return 0 errors

- [ ] **Task-3.4.5:** Integration test
  - [ ] Generate code from example SQL files
  - [ ] Verify generated code has same type annotations
  - [ ] Test with various SQL queries (SELECT, INSERT, UPDATE)
  - [ ] Test with parameters that require different inference strategies

- [ ] **Task-3.4.6:** Verify test coverage
  - [ ] `pytest --cov=splurge_sql_generator/type_inference --cov-report=term-missing`
  - [ ] Coverage should be >80% for new module

**Acceptance Criteria:**
- [ ] Type inference logic extracted to separate module
- [ ] New module has comprehensive unit tests
- [ ] `code_generator.py` uses new module
- [ ] All existing tests pass
- [ ] Generated code types are unchanged
- [ ] mypy and ruff pass
- [ ] Code is more maintainable and testable

---

## Stage 4: Remove Unused Configuration Options

**Priority:** LOW  
**Estimated Effort:** 1 hour  
**Risk:** VERY LOW

### Objective
Remove or simplify unused configuration options following YAGNI principle.

### Stage 4.1: Analyze Configuration Usage

**Tasks:**
- [x] **Task-4.1.1:** Search for `max_file_size_mb` usage
  - [x] Find all references in codebase
  - [x] Check if chunked processing is implemented
  - [x] Document current behavior (unused - sql_helper uses its own MAX_MEMORY_MB)

- [x] **Task-4.1.2:** Search for `validate_parameters` usage
  - [x] Find all references in codebase
  - [x] Check if feature is actually used (used in code_generator)
  - [x] Document current behavior

- [x] **Task-4.1.3:** Review `config.py`
  - [x] Read `GeneratorConfig` class
  - [x] Check `from_env()` method
  - [x] Check `to_dict()` method
  - [x] Identify which options are unused (max_file_size_mb is unused)

**Files to Review:**
- `splurge_sql_generator/config.py`
- `splurge_sql_generator/sql_helper.py` (check MAX_MEMORY_MB usage)
- `splurge_sql_generator/code_generator.py` (check validate_parameters usage)

### Stage 4.2: Remove or Document Unused Options

**Tasks:**
- [x] **Task-4.2.1:** Remove `max_file_size_mb` if unused
  - [x] Remove from `GeneratorConfig` dataclass
  - [x] Remove from `from_env()` method
  - [x] Remove from `to_dict()` method
  - [x] Remove from `_ENV_PREFIX` constant usage
  - [x] Update docstrings
  - [x] Keep `MAX_MEMORY_MB` in `sql_helper.py` if needed for logging

- [x] **Task-4.2.2:** Keep or enhance `validate_parameters`
  - [x] If used: Keep and document its limited scope
  - [x] If unused: Remove following same steps as above
  - [x] Update docstrings to clarify purpose

- [x] **Task-4.2.3:** Update configuration documentation
  - [x] Update `config.py` module docstring
  - [x] Document remaining configuration options
  - [x] Add examples if helpful

**Files to Modify:**
- `splurge_sql_generator/config.py`

**Files to Check:**
- `splurge_sql_generator/code_generator.py` (if validate_parameters removed - kept it)
- `splurge_sql_generator/sql_helper.py` (if max_file_size_mb removed - kept MAX_MEMORY_MB)

### Stage 4.3: Update Tests and Validation

**Tasks:**
- [ ] **Task-4.3.1:** Update config tests
  - [ ] `pytest tests/unit/test_config.py -v`
  - [ ] Remove or update tests for removed options
  - [ ] All tests must pass

- [ ] **Task-4.3.2:** Run type checking
  - [ ] `mypy splurge_sql_generator/config.py`
  - [ ] Must return 0 errors

- [ ] **Task-4.3.3:** Run linting
  - [ ] `ruff check splurge_sql_generator/config.py`
  - [ ] Must return 0 errors

- [ ] **Task-4.3.4:** Verify no broken imports
  - [ ] Search for imports of removed config options
  - [ ] Update or remove as needed

**Acceptance Criteria:**
- [ ] Unused configuration options removed
- [ ] Remaining options are documented
- [ ] All tests pass
- [ ] No broken references
- [ ] Configuration is simpler and clearer

---

## Stage 5: Consistent TypedDict Usage

**Priority:** MEDIUM  
**Estimated Effort:** 2 hours  
**Risk:** NONE (type-only changes)

### Objective
Update function return types to use TypedDict definitions consistently throughout the codebase.

### Stage 5.1: Audit TypedDict Usage

**Tasks:**
- [x] **Task-5.1.1:** Review `type_definitions.py`
  - [x] List all TypedDict definitions:
    - `ColumnInfo`
    - `MethodInfo`
    - `TableDefinition`
  - [x] Understand structure of each

- [x] **Task-5.1.2:** Search for functions returning `dict[str, Any]`
  - [x] Find in `code_generator.py`
  - [x] Find in `schema_parser.py`
  - [x] Find in other modules
  - [x] Document which match TypedDict structures

- [x] **Task-5.1.3:** Map functions to TypedDict types
  - [x] `_prepare_method_data()` → `MethodInfo`
  - [x] Schema parser methods → `TableDefinition` or `ColumnInfo` (kept as dict for internal use)
  - [x] Document mappings

**Files to Review:**
- `splurge_sql_generator/type_definitions.py`
- `splurge_sql_generator/code_generator.py`
- `splurge_sql_generator/schema_parser.py`

### Stage 5.2: Update Return Types in code_generator.py

**Tasks:**
- [x] **Task-5.2.1:** Update `_prepare_method_data()` return type
  - [x] Change from `dict[str, Any]` to `MethodInfo`
  - [x] Import `MethodInfo` from `type_definitions`
  - [x] Verify returned dict matches `MethodInfo` structure
  - [x] Update function to explicitly construct `MethodInfo` if needed (dict matches structure)

- [x] **Task-5.2.2:** Update `generate_multiple_classes()` return type
  - [x] Check if return type `dict[str, str]` is appropriate (class names → code)
  - [x] Keep as-is if correct, or create new TypedDict if needed (kept as-is - appropriate)
  - [x] Document decision

- [x] **Task-5.2.3:** Review other dict returns
  - [x] Check `_generate_python_code()` return type (returns str - correct)
  - [x] Update if applicable
  - [x] Document any kept as `dict` with rationale

**Files to Modify:**
- `splurge_sql_generator/code_generator.py`

### Stage 5.3: Update Return Types in schema_parser.py

**Tasks:**
- [ ] **Task-5.3.1:** Review schema parser methods
  - [ ] Check `_parse_schema_file()` return type
  - [ ] Check `_parse_schema_content()` return type
  - [ ] Check `_parse_table_columns()` return type
  - [ ] Map to appropriate TypedDict structures

- [ ] **Task-5.3.2:** Update table schema returns
  - [ ] Consider if `dict[str, dict[str, str]]` should be `dict[str, TableDefinition]`
  - [ ] Update if appropriate (may require refactoring return structure)
  - [ ] Or keep as-is if structure doesn't match exactly
  - [ ] Document decision

- [ ] **Task-5.3.3:** Update column-related returns
  - [ ] Check if `dict[str, str]` (column name → SQL type) matches `ColumnInfo`
  - [ ] May need to enhance TypedDict or keep simple dict
  - [ ] Document decision

**Files to Modify:**
- `splurge_sql_generator/schema_parser.py`
- `splurge_sql_generator/type_definitions.py` (if enhancements needed)

### Stage 5.4: Enhance TypedDict Definitions if Needed

**Tasks:**
- [ ] **Task-5.4.1:** Review `MethodInfo` structure
  - [ ] Compare with actual data in `_prepare_method_data()`
  - [ ] Add missing fields if needed (use `total=False` for optional)
  - [ ] Ensure all fields match

- [ ] **Task-5.4.2:** Review `TableDefinition` structure
  - [ ] Compare with schema parser returns
  - [ ] Enhance if needed
  - [ ] Document any limitations

- [ ] **Task-5.4.3:** Review `ColumnInfo` structure
  - [ ] Compare with column parsing returns
  - [ ] Enhance if needed
  - [ ] Document any limitations

**Files to Modify:**
- `splurge_sql_generator/type_definitions.py`

### Stage 5.5: Validation and Testing

**Tasks:**
- [ ] **Task-5.5.1:** Run type checking
  - [ ] `mypy splurge_sql_generator/code_generator.py`
  - [ ] `mypy splurge_sql_generator/schema_parser.py`
  - [ ] `mypy splurge_sql_generator/type_definitions.py`
  - [ ] Must return 0 errors
  - [ ] Fix any type errors

- [ ] **Task-5.5.2:** Run existing tests
  - [ ] `pytest tests/unit/test_code_generator.py -v`
  - [ ] `pytest tests/unit/test_schema_parser.py -v`
  - [ ] All tests must pass

- [ ] **Task-5.5.3:** Run linting
  - [ ] `ruff check splurge_sql_generator/code_generator.py`
  - [ ] `ruff check splurge_sql_generator/schema_parser.py`
  - [ ] Must return 0 errors

- [ ] **Task-5.5.4:** Verify IDE support
  - [ ] Check autocomplete works with TypedDict returns
  - [ ] Verify type hints are helpful
  - [ ] Document any limitations

- [ ] **Task-5.5.5:** Integration test
  - [ ] Generate code from examples
  - [ ] Verify functionality unchanged
  - [ ] Only type annotations changed, not behavior

**Acceptance Criteria:**
- [ ] Return types use TypedDict where appropriate
- [ ] mypy reports 0 errors
- [ ] All existing tests pass
- [ ] Type safety improved
- [ ] IDE autocomplete works better
- [ ] No functionality changes

---

## Final Validation

After completing all stages:

### Comprehensive Testing

**Tasks:**
- [ ] **Task-Final.1:** Run full test suite
  - [ ] `pytest -v`
  - [ ] All 235+ tests must pass
  - [ ] No new test failures

- [ ] **Task-Final.2:** Run type checking
  - [ ] `mypy splurge_sql_generator`
  - [ ] Must return 0 errors
  - [ ] No type regressions

- [ ] **Task-Final.3:** Run linting
  - [ ] `ruff check .`
  - [ ] Must return 0 errors
  - [ ] Code style consistent

- [ ] **Task-Final.4:** Check test coverage
  - [ ] `pytest --cov=splurge_sql_generator --cov-report=term-missing`
  - [ ] Coverage should maintain or improve
  - [ ] Document any coverage changes

- [ ] **Task-Final.5:** Integration testing
  - [ ] Test with all example SQL files
  - [ ] Verify generated code is identical (or type annotations improved)
  - [ ] Test CLI workflow end-to-end
  - [ ] Test API usage

- [ ] **Task-Final.6:** Performance check
  - [ ] Run timing tests if available
  - [ ] Verify no performance regression
  - [ ] Document any improvements

### Documentation Updates

**Tasks:**
- [ ] **Task-Final.7:** Update CHANGELOG.md
  - [ ] Document all changes
  - [ ] List improvements made
  - [ ] Note any deprecations (none expected)

- [ ] **Task-Final.8:** Update code comments
  - [ ] Ensure new functions have docstrings
  - [ ] Update existing docstrings if behavior changed
  - [ ] Document any design decisions

- [ ] **Task-Final.9:** Review and merge
  - [ ] Create pull request
  - [ ] Review all changes
  - [ ] Get approval
  - [ ] Merge to main branch

---

## Risk Mitigation

### Potential Issues and Solutions

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Breaking changes during refactoring | Low | High | Run tests after each task, fix immediately |
| Type errors after TypedDict changes | Medium | Low | Use mypy strictly, fix incrementally |
| Performance regression | Low | Medium | Profile before/after, benchmark key paths |
| Test coverage decrease | Low | Medium | Monitor coverage continuously |
| Merge conflicts | Low | Low | Work on feature branch, merge frequently |

### Rollback Plan

If issues are discovered:
1. Revert to previous commit
2. Document issues found
3. Create issue ticket for follow-up
4. Plan incremental approach

---

## Success Metrics

### Quantitative Metrics

- [ ] Code duplication reduced (token navigation patterns)
- [ ] Type coverage improved (TypedDict usage)
- [ ] Test coverage maintained or improved
- [ ] Zero mypy errors
- [ ] Zero ruff errors
- [ ] All tests passing (235+)

### Qualitative Metrics

- [ ] Code is more maintainable
- [ ] Type inference logic is easier to test
- [ ] Configuration is simpler
- [ ] Developer experience improved (better IDE support)

---

## Timeline

| Stage | Estimated Time | Dependencies |
|-------|---------------|--------------|
| Stage 1: Token Navigation Helpers | 2-3 hours | None |
| Stage 2: Consolidate Identifier Extraction | 30 minutes | Stage 1 (can be parallel) |
| Stage 3: Extract Type Inference | 3-4 hours | None |
| Stage 4: Remove Unused Config | 1 hour | None (can be parallel) |
| Stage 5: Consistent TypedDict Usage | 2 hours | Stage 3 (uses type_inference) |
| Final Validation | 1 hour | All stages |

**Total Estimated Time:** 9-11 hours

**Suggested Approach:**
- Complete stages sequentially for safety
- Stages 2 and 4 can be done in parallel with others
- Stage 5 should follow Stage 3

---

## Notes

- All changes are internal refactoring - no public API changes
- Focus on maintainability improvements, not new features
- Keep changes incremental and testable
- Document any design decisions made during implementation

---

**Document Status:** Ready for Implementation  
**Last Updated:** October 31, 2025  
**Next Review:** After implementation completion

