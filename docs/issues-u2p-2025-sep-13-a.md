---
title: "u2p conversion evidence & issues — 2025-09-13 (run A)"
date: 2025-09-13
tags: [u2p, unittest-to-pytest, evidence, migration]
---

Summary
-------

This report documents a clean run performed on 2025-09-13: tests were restored to HEAD, the `splurge-unittest-to-pytest` converter was run with `--no-compat` and backups were written, and the converted tests were executed with pytest. The report includes converter output, pytest results (including the single error), diffs for converted files, backup listing, and recommended fixes.

Commands executed
-----------------

- Restore tests to HEAD:

  git restore --source=HEAD --staged --worktree -- tests/

- Run converter with --no-compat and backups:

  source .venv/Scripts/activate && splurge-unittest-to-pytest -r --no-compat -b backups/u2p-2025-09-13-a tests/

- Run pytest:

  source .venv/Scripts/activate && pytest -q


Converter output (summary)
--------------------------

- Processed: 14 files
- Converted: 13 files
- Unchanged: 1 file
- Backups saved in: `backups/u2p-2025-09-13-a/`


Pytest result (this run)
------------------------

- Summary: 71 passed, 1 error
- Error: fixture 'sql_file' not found (raised at tests/unit/test_init_api.py:40)

Exact pytest error message (excerpt):

  E   fixture 'sql_file' not found
  File: tests/unit/test_init_api.py:40

Pytest terminated early due to this fixture error (xdist stopped after the first failing worker). Many tests passed before the error (71).


Concrete diffs / examples
-------------------------

Selected conversion patterns visible in diffs:

- The converter replaced many unittest.TestCase classes with plain pytest-style functions and module-level fixtures. In `tests/unit/test_init_api.py` it added fixtures like `temp_dir` and `sql_file` in some runs; in this run pytest reported `sql_file` is missing as a fixture dependency for `test_generate_class`.

- Example diff excerpt (converted to pytest-style):

  - Original: class TestInitAPI(unittest.TestCase): ... def test_generate_class(self): ...
  - Converted: def test_generate_class(temp_dir, sql_content, sql_file, schema_file): ...

The converted test now requires module-level fixtures named `sql_file` and `schema_file`. In this run `sql_file` was not provided (fixture not found), which causes pytest to error.


Backups created (top-level listing)
----------------------------------

- backups/u2p-2025-09-13-a:
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


Recommendations and minimal fixes
----------------------------------

The failure is caused by converted tests depending on fixtures that either were not generated or were generated incorrectly. Recommended minimal actions:

1) Implement missing `sql_file` and/or `schema_file` fixtures in `tests/unit/test_init_api.py` (or remove them from function args and rely on the class `setUp()` which remains in many converted classes). Example fixtures:

    @pytest.fixture
    def sql_file(tmp_path, sql_content):
        p = tmp_path / 'test.sql'
        p.write_text(sql_content)
        return str(p)

    @pytest.fixture
    def schema_file(tmp_path):
        p = tmp_path / 'test.schema'
        p.write_text('CREATE TABLE t (id INTEGER PRIMARY KEY);')
        return str(p)

2) Audit other converted tests for similar missing or self-referential fixtures (earlier runs showed `cm.exception` vs `cm.value` issues and self-referential fixtures returning placeholder strings). Fix these as needed.

3) Re-run pytest after implementing fixes to ensure the suite completes.


If you want, I can apply the minimal fixture implementations and re-run pytest to confirm a green run. Say the word and I will patch the tests and re-run.
