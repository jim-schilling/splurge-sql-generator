---
title: "u2p conversion evidence & issues — 2025-09-12 (run E)"
date: 2025-09-12
tags: [u2p, unittest-to-pytest, evidence, migration]
---

Summary
-------

This document records a clean-run (run E) where I restored the test tree to `HEAD`, ran the newest `splurge-unittest-to-pytest` with `--no-compat`, executed the converted tests with `pytest`, and captured concrete evidence of any issues.

Commands executed
-----------------

- Restore tests to HEAD (worktree + index):

  git restore --source=HEAD --staged --worktree -- tests/

- Run converter with `--no-compat` and backups for run E:

  source .venv/Scripts/activate && \
  splurge-unittest-to-pytest -r --no-compat -b backups/u2p-2025-09-12-e tests/

- Run pytest:

  source .venv/Scripts/activate && pytest -q


Converter output (summary)
--------------------------

- Processed 14 files
- 9 files converted, 5 files unchanged
- Converted files (modified in working tree):
  - tests/integration/test_cli.py
  - tests/integration/test_cli_sql_type_option.py
  - tests/unit/test_code_generator.py
  - tests/unit/test_generate_types.py
  - tests/unit/test_init_api.py
  - tests/unit/test_parameter_validation.py
  - tests/unit/test_schema_parser.py
  - tests/unit/test_schema_parser_edge_cases.py
  - tests/unit/test_sql_parser.py

- Backups directory for this run: `backups/u2p-2025-09-12-e/` (original files saved with `.bak` extension)


Pytest run result
-----------------

- Outcome: 147 passed, 2 failed
- Failures (same two persistent issues across runs):
  - tests/unit/test_parameter_validation.py::TestParameterValidation::test_validation_with_nonexistent_table
  - tests/unit/test_init_api.py::TestInitAPI::test_generate_class


Concrete evidence (diff snippets and failing lines)
-----------------------------------------------

1) `pytest.raises` vs `ExceptionInfo` attribute

- Converted test excerpt (from `tests/unit/test_parameter_validation.py`):

    with pytest.raises(SqlValidationError) as cm:
        self.generator.generate_class(sql_fname, schema_file_path=schema_fname)

    error_msg = str(cm.exception)    # <-- AttributeError at runtime; pytest's ExceptionInfo has `.value`

Evidence: pytest raised AttributeError: 'ExceptionInfo' object has no attribute 'exception' at this line.


2) Broken fixtures producing placeholder strings

- Converted fixture excerpt (from `tests/unit/test_init_api.py`):

@pytest.fixture()
def sql_file(tmp_path, sql_content):
    p = tmp_path.joinpath('test.sql')
    p.write_text(sql_content)
    return str(p)

@pytest.fixture
def schema_file():
    _schema_file_value = str(schema_file)
    return _schema_file_value

The `schema_file` fixture was converted into a self-referential function that returns a placeholder string like '<pytest_fixture(...)>', which later causes FileNotFoundError when the code expects a real path.

Evidence: pytest error shows FileNotFoundError: Schema file required but not found: <pytest_fixture(<function schema_file at 0x...>)>


Backups (run E)
---------------

Contents of `backups/u2p-2025-09-12-e` (top-level):

- test_cli.py.bak
- test_cli_end_to_end.py.bak
- test_cli_sql_type_option.py.bak
- test_code_generator.py.bak
- test_detect_statement_type.py.bak
- test_generate_types.py.bak
- test_init_api.py.bak
- test_parameter_validation.py.bak
- test_parse_sql_statements.py.bak
- test_remove_sql_comments.py.bak
- test_schema_parser.py.bak
- test_schema_parser_edge_cases.py.bak
- test_sql_parser.py.bak
- test_statement_detection.py.bak


Conclusion & recommended fixes
------------------------------

Both issues are semantic translation problems introduced by the converter and are small and localized:

1) After `with pytest.raises(...) as cm:` use `cm.value` to access the raised exception object instead of `cm.exception`.

2) Fix `schema_file` and similar fixtures so they create and return real file paths. For example:

    @pytest.fixture()
    def schema_file(tmp_path, sql_content):
        p = tmp_path.joinpath('test.schema')
        p.write_text('CREATE TABLE ...')
        return str(p)

Alternatively, remove the module-level fixtures and rely on class `setUp()` which already creates `self.sql_file`/`self.schema_file` in some tests.


If you want, I can apply these fixes (very small edits) and re-run pytest to confirm the suite becomes green. Say the word and I'll implement the patches and report back.
