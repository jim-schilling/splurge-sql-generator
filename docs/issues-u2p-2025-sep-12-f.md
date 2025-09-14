---
title: "u2p conversion evidence & issues — 2025-09-13 (run F)"
date: 2025-09-13
tags: [u2p, unittest-to-pytest, evidence, migration]
---

Summary
-------

This document records run F: tests were restored to HEAD, `splurge-unittest-to-pytest` was run with `--no-compat` and backups were written, then the converted tests were executed with pytest. The report contains concrete evidence (converter output, pytest error, diffs, backups) and recommendations.

What I ran
----------

- Restore tests to HEAD:

  git restore --source=HEAD --staged --worktree -- tests/

- Run converter with `--no-compat` and backups for run F:

  source .venv/Scripts/activate && splurge-unittest-to-pytest -r --no-compat -b backups/u2p-2025-09-12-f tests/

- Run pytest:

  source .venv/Scripts/activate && pytest -q


Converter output (run F)
------------------------

- Processed 14 files
- 13 files converted, 1 file unchanged
- Converted files (modified in working tree):
  - tests/integration/test_cli.py
  - tests/integration/test_cli_sql_type_option.py
  - tests/unit/test_code_generator.py
  - tests/unit/test_detect_statement_type.py
  - tests/unit/test_generate_types.py
  - tests/unit/test_init_api.py
  - tests/unit/test_parameter_validation.py
  - tests/unit/test_parse_sql_statements.py
  - tests/unit/test_remove_sql_comments.py
  - tests/unit/test_schema_parser.py
  - tests/unit/test_schema_parser_edge_cases.py
  - tests/unit/test_sql_parser.py
  - tests/unit/test_statement_detection.py

Backups
-------

- Backups stored in: `backups/u2p-2025-09-12-f/`
- Top-level listing (files preserved with .bak):
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


Pytest run (evidence)
---------------------

- Summary: 71 passed, 1 error
- The single error occurs during test setup for `test_generate_class`.

Error excerpt (exact runtime message):

  E   RuntimeError: Converted fixture 'schema_file' is ambiguous: converter produced a self-referential placeholder. Please implement this fixture to create the required artifact (e.g., using tmp_path and helper factories).
  File: tests/unit/test_init_api.py:28

This error is raised by the converted `schema_file` fixture (converter detected a self-referential fixture and injected a runtime error to make the problem explicit). The error stops pytest early (xdist interrupted after the first failure).


Concrete diffs / conversion patterns (selected)
---------------------------------------------

1) Module-level fixtures were introduced. Example (from `tests/unit/test_init_api.py`):

  @pytest.fixture()
  def sql_file(tmp_path, sql_content):
      p = tmp_path.joinpath('test.sql')
      p.write_text(sql_content)
      return str(p)

  @pytest.fixture
  def schema_file():
      _schema_file_value = str(schema_file)
      return _schema_file_value

  - `sql_file` fixture above is reasonable (creates a temp file). But `schema_file` is self-referential and therefore broken; converter left a placeholder implementation that returns `str(schema_file)`.

2) The converter moved many TestCase methods into plain pytest test functions and replaced unittest assertions with bare `assert` statements. Most of these changes are syntactic and worked for many tests.


Why this fails (short analysis)
------------------------------

- The converter sometimes cannot infer how to create per-test artifacts that were originally created in TestCase `setUp` or via helper methods. It emits module-level fixtures, but if the fixture logic is ambiguous the conversion can produce self-referential placeholders.
- To make these failures visible, the converter (or our test harness) raises a RuntimeError at fixture setup rather than silently passing a broken value into tests. That's the error you see.


Recommended minimal fixes
------------------------

1) Implement `schema_file` fixture to create an actual schema file and return its path. Example pattern:

    @pytest.fixture
    def schema_file(tmp_path):
        p = tmp_path.joinpath('test.schema')
        p.write_text('CREATE TABLE t (id INTEGER PRIMARY KEY);')
        return str(p)

2) Review other converted fixtures for self-referential placeholders and implement them or rely on the class-based `setUp()`/`tearDown()` (which remain present in many converted test classes).

3) After applying these small changes re-run `pytest -q` to confirm the suite completes. Many tests already passed in this run (71) so the remaining fixes are likely minimal.


Files created for record
------------------------

- `backups/u2p-2025-09-12-f/*` (lots of .bak files preserving originals)


If you want me to proceed
-------------------------

I can:
- Apply the `schema_file` fixture fix and any other small fixture fixes detected, then re-run pytest.
- Or, prepare a patch/PR with the recommended fixture implementations so you can review before applying.

Tell me which option you prefer and I'll continue.
