from pathlib import Path

import pytest

from splurge_sql_generator.exceptions import SplurgeSqlGeneratorValueError
from splurge_sql_generator.utils import (
    clean_sql_type,
    find_files_by_extension,
    is_empty_or_whitespace,
    normalize_string,
    to_snake_case,
    validate_python_identifier,
)


def test_to_snake_case_basic_and_acronyms():
    assert to_snake_case("UserRepository") == "user_repository"
    assert to_snake_case("API") == "api"
    assert to_snake_case("") == ""


def test_clean_sql_type_removes_sizes():
    assert clean_sql_type("VARCHAR(255)") == "VARCHAR"
    assert clean_sql_type("DECIMAL(10,2)") == "DECIMAL"
    assert clean_sql_type("INTEGER") == "INTEGER"


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
    with pytest.raises(SplurgeSqlGeneratorValueError):
        validate_python_identifier("", context="name")

    # invalid non-identifier
    with pytest.raises(SplurgeSqlGeneratorValueError):
        validate_python_identifier("1abc", context="name")

    # reserved keyword
    with pytest.raises(SplurgeSqlGeneratorValueError):
        validate_python_identifier("class", context="name")


def test_normalize_string_and_is_empty_or_whitespace():
    assert normalize_string(None) == ""
    assert normalize_string(123) == "123"
    assert normalize_string("  a  ") == "a"

    assert is_empty_or_whitespace(None) is True
    assert is_empty_or_whitespace("") is True
    assert is_empty_or_whitespace("   ") is True
    assert is_empty_or_whitespace("x") is False
