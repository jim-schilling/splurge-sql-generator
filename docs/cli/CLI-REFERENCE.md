# CLI Reference — splurge_sql_generator

Version: 2025.5.0 (release/2025.5.0-prep)

This document describes the command-line interface for `splurge_sql_generator`, including available flags and options, expected behavior, error modes, exit codes, environment variables, and usage examples.

## Command

Invoke via module or script:

```bash
python -m splurge_sql_generator.cli [options] sql_files...
# or
python -m splurge_sql_generator [options] sql_files...
```

The CLI produces Python classes generated from SQL template files. It supports generating type mapping files and printing generated code to stdout for review.

## Synopsis

- `sql_files`: One or more SQL template files (or directories) to process
- `-o, --output OUTPUT`: Output directory for generated Python files
- `--dry-run`: Print generated code to stdout without saving files
- `--strict`: Treat warnings (non-.sql inputs, empty dir) as errors
- `-t, --types TYPES`: Path to custom SQL type mapping YAML file (default: `types.yaml`)
- `--schema SCHEMA`: Path to schema file to use for all SQL files (default: discover `*.schema` files)
- `--generate-types [TYPES_FILE]`: Generate default SQL type mapping file (defaults to `types.yaml` when used without a value)

The CLI also supports passing a directory; directories will be scanned recursively for `.sql` files.

## Full Options

- `-h, --help` — Show help message and exit.

- `sql_files` — Positional arguments. One or more SQL template files or directories containing `.sql` files. Required unless `--generate-types` is used.

- `-o, --output OUTPUT` — Optional output directory. When provided and not used with `--dry-run`, the generator will write generated classes into the directory using snake_case file names derived from class names (e.g., `MyClass` → `my_class.py`). The directory is created if it doesn't exist.

- `--dry-run` — Print generated code to stdout. When used with a single SQL file, the code for that file is printed. When used with multiple files, prints nothing; use without `--dry-run` to write files.

- `--strict` — Treat warnings as errors (exit non-zero) for conditions like non-`.sql` files or empty directories.

- `-t, --types TYPES` — Path to a YAML types mapping file, mapping SQL types to Python types (default: `types.yaml`). The file is loaded by `SchemaParser.load_sql_type_mapping()`.

- `--schema SCHEMA` — Path to schema file to use for all SQL files. If omitted, the CLI will search for `*.schema` files in the current directory and in directories that contain the provided SQL files.

- `--generate-types [TYPES_FILE]` — Generate a default types YAML file. If the optional `TYPES_FILE` argument is not provided, the CLI creates `types.yaml` in the current directory. Example: `--generate-types my_types.yaml`.

## Environment variables

The CLI does not require environment variables. Project-wide policy recommends prefixing env vars with `SPLURGE_` if added in the future.

## Exit codes

- `0` — Success
- `1` — Generic error
- `2` — Invalid arguments (argparse usage)
- `130` — Interrupted (Ctrl+C)

## Errors and messages

The CLI prints informative messages to stderr and will exit with non-zero codes for fatal errors. Examples:

- "Error: SQL file not found: <path>" — printed when a provided SQL file path does not exist
- "Warning: File <path> doesn't have .sql extension" — printed for non-.sql files (treated as a warning unless `--strict`)
- "Error: No schema file specified and no *.schema files found..." — fatal if schema file required but not found
- When unexpected exceptions occur during generation, the CLI prints: "Unexpected error generating classes: <error>" and exits 1.

## Examples

Generate a single class to `generated/` directory:

```bash
python -m splurge_sql_generator.cli examples/User.sql -o generated/
```

Generate classes for all SQL files in a directory (recursively):

```bash
python -m splurge_sql_generator.cli examples/ -o generated/
```

Print a single class to stdout (dry run):

```bash
python -m splurge_sql_generator.cli examples/User.sql --dry-run
```

Generate a default types mapping file in the current directory:

```bash
python -m splurge_sql_generator.cli --generate-types
# or
python -m splurge_sql_generator.cli --generate-types my_types.yaml
```

Strict mode — abort on warnings:

```bash
python -m splurge_sql_generator.cli examples/ --strict
```

Reporting generated classes (sample output):

```
Generated 2 Python classes:
    - User: generated/user.py
    - ProductRepository: generated/product_repository.py
```

## Migration notes (CLI)

- The CLI continues to accept the same flags as 2025.4.x. The notable change is that file I/O is routed through the `SafeTextFileIoAdapter`, which standardizes `FileError` messages. Tests and error handling were updated to expect adapter-provided messages rather than `splurge_safe_io`-specific exception types.

## Troubleshooting

- If you see errors related to importing `types`, ensure you are importing `type_definitions` instead of `types` (module renamed to avoid stdlib shadowing).
- If the CLI fails to find a schema file, either pass `--schema path/to/schema.schema` or place a `*.schema` file in the current directory or in the SQL file directory.

---

For more concrete examples, refer to unit and integration tests under `tests/` which show the CLI usage in automated scenarios.