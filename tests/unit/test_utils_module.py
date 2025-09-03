import os
from pathlib import Path

import pytest

from splurge_sql_generator.utils import (
    to_snake_case,
    clean_sql_type,
    validate_file_path,
    safe_read_file,
    safe_write_file,
    find_files_by_extension,
    validate_python_identifier,
    format_error_context,
    normalize_string,
    is_empty_or_whitespace,
)


def test_to_snake_case_basic_and_acronyms():
    assert to_snake_case("UserRepository") == "user_repository"
    assert to_snake_case("API") == "api"
    assert to_snake_case("") == ""


def test_clean_sql_type_removes_sizes():
    assert clean_sql_type("VARCHAR(255)") == "VARCHAR"
    assert clean_sql_type("DECIMAL(10,2)") == "DECIMAL"
    assert clean_sql_type("INTEGER") == "INTEGER"


def test_validate_file_path_success_and_extension(tmp_path: Path):
    file_path = tmp_path / "file.sql"
    file_path.write_text("SELECT 1;")

    # must_exist default True
    path = validate_file_path(str(file_path))
    assert path == file_path

    # extension check
    with pytest.raises(ValueError):
        validate_file_path(str(file_path), extension=".txt")


def test_validate_file_path_must_exist_false(tmp_path: Path):
    missing = tmp_path / "missing.schema"
    path = validate_file_path(str(missing), must_exist=False, extension=".schema")
    assert path == missing


def test_safe_write_and_read_roundtrip(tmp_path: Path):
    file_path = tmp_path / "data.txt"
    content = "hello world"
    safe_write_file(file_path, content)
    assert safe_read_file(file_path) == content

    with pytest.raises(FileNotFoundError):
        safe_read_file(tmp_path / "does_not_exist.txt")


def test_find_files_by_extension(tmp_path: Path):
    a = tmp_path / "a.sql"
    b = tmp_path / "b.sql"
    c = tmp_path / "c.txt"
    a.write_text("-- a")
    b.write_text("-- b")
    c.write_text("-- c")

    found = find_files_by_extension(tmp_path, ".sql")
    names = {p.name for p in found}
    assert names == {"a.sql", "b.sql"}


def test_validate_python_identifier():
    # valid
    validate_python_identifier("foo_bar", context="name")

    # invalid empty
    with pytest.raises(ValueError):
        validate_python_identifier("", context="name")

    # invalid non-identifier
    with pytest.raises(ValueError):
        validate_python_identifier("1abc", context="name")

    # reserved keyword
    with pytest.raises(ValueError):
        validate_python_identifier("class", context="name")


def test_format_error_context():
    assert format_error_context(None) == ""
    # OS-agnostic path check
    test_path = Path("/tmp/file.sql") if os.name != "nt" else Path("\\tmp\\file.sql")
    result = format_error_context(test_path)
    assert result.startswith(" in ")
    # Normalize separators for assertion
    assert result[4:].replace("\\", "/").endswith("/tmp/file.sql")


def test_normalize_string_and_is_empty_or_whitespace():
    assert normalize_string(None) == ""
    assert normalize_string(123) == "123"
    assert normalize_string("  a  ") == "a"

    assert is_empty_or_whitespace(None) is True
    assert is_empty_or_whitespace("") is True
    assert is_empty_or_whitespace("   ") is True
    assert is_empty_or_whitespace("x") is False


