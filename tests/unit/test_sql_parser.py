import os
import tempfile

import pytest

from splurge_sql_generator.exceptions import SqlValidationError
from splurge_sql_generator.sql_parser import SqlParser
from tests.unit.test_utils import temp_sql_files


@pytest.fixture
def parser():
    return SqlParser()


def test_parse_file_and_extract_methods(parser):
    sql = """# TestClass
#get_user
SELECT * FROM users WHERE id = :user_id;

#create_user
INSERT INTO users (name, email) VALUES (:name, :email);
        """
    with temp_sql_files(sql) as (sql_file, _):
        class_name, methods = parser.parse_file(sql_file)
        assert class_name == "TestClass"
        assert "get_user" in methods
        assert "create_user" in methods
        assert methods["get_user"].startswith("SELECT")


def test_extract_methods_and_queries(parser):
    sql = """
#get_one
SELECT 1;
#get_two
SELECT 2;
        """
    methods = parser._extract_methods_and_queries(sql)
    assert len(methods) == 2
    assert "get_one" in methods
    assert "get_two" in methods


def test_extract_methods_edge_cases(parser):
    # Empty content
    methods = parser._extract_methods_and_queries("")
    assert methods == {}

    # Content with no methods
    methods = parser._extract_methods_and_queries("SELECT * FROM users;")
    assert methods == {}

    # Method with no SQL
    methods = parser._extract_methods_and_queries("#get_user\n\n#get_two\nSELECT 2;")
    assert "get_two" in methods
    assert "get_user" not in methods


def test_sql_cleaning_with_sql_helper(parser):
    """Test that SQL cleaning using sql_helper works correctly."""
    # Test that semicolons are stripped
    methods = parser._extract_methods_and_queries("#test_method\nSELECT 1;")
    assert methods["test_method"] == "SELECT 1"

    # Test that whitespace is trimmed
    methods = parser._extract_methods_and_queries("#test_method\n  SELECT 2  ")
    assert methods["test_method"] == "SELECT 2"

    # Test that multiple semicolons are handled
    methods = parser._extract_methods_and_queries("#test_method\nSELECT 3;;")
    assert methods["test_method"] == "SELECT 3;"

    # Test empty SQL is handled
    methods = parser._extract_methods_and_queries("#test_method\n   ")
    assert "test_method" not in methods


def test_get_method_info_basic_types(parser):
    # SELECT statements
    info = parser.get_method_info("SELECT * FROM users WHERE id = :user_id")
    assert info["type"] == "select"
    assert info["is_fetch"]
    assert "user_id" in info["parameters"]
    assert not info["has_returning"]

    # INSERT statements
    info = parser.get_method_info("INSERT INTO users (name) VALUES (:name) RETURNING id")
    assert info["type"] == "insert"
    assert not info["is_fetch"]
    assert "name" in info["parameters"]
    assert info["has_returning"]

    # UPDATE statements
    info = parser.get_method_info("UPDATE users SET x=1 WHERE id=:id")
    assert info["type"] == "update"
    assert not info["is_fetch"]
    assert "id" in info["parameters"]

    # DELETE statements
    info = parser.get_method_info("DELETE FROM users WHERE id=:id")
    assert info["type"] == "delete"
    assert not info["is_fetch"]
    assert "id" in info["parameters"]

    # CTE statements
    info = parser.get_method_info("WITH cte AS (SELECT 1) SELECT * FROM cte")
    assert info["type"] == "cte"
    assert info["is_fetch"]

    # Other statement types
    info = parser.get_method_info("SHOW TABLES")
    assert info["type"] == "show"
    assert info["is_fetch"]

    info = parser.get_method_info("EXPLAIN SELECT 1")
    assert info["type"] == "explain"
    assert info["is_fetch"]

    info = parser.get_method_info("DESCRIBE users")
    assert info["type"] == "describe"
    assert info["is_fetch"]

    info = parser.get_method_info("VALUES (1, 2), (3, 4)")
    assert info["type"] == "values"
    assert info["is_fetch"]

    # PRAGMA is a fetch statement but not mapped to a named type, so 'other'
    info = parser.get_method_info("PRAGMA table_info(users)")
    assert info["type"] == "other"
    assert info["is_fetch"]


def test_get_method_info_complex_sql(parser):
    # Complex CTE with multiple CTEs
    sql = """
        WITH cte1 AS (SELECT 1 as id),
             cte2 AS (SELECT 2 as id)
        SELECT * FROM cte1 UNION SELECT * FROM cte2
        """
    info = parser.get_method_info(sql)
    assert info["type"] == "cte"
    assert info["is_fetch"]

    # CTE with INSERT
    sql = """
        WITH temp_data AS (SELECT id, name FROM source_table)
        INSERT INTO target_table (id, name)
        SELECT id, name FROM temp_data
        """
    info = parser.get_method_info(sql)
    assert info["type"] == "cte"
    assert not info["is_fetch"]

    # Subquery in FROM clause
    sql = "SELECT * FROM (SELECT id, name FROM users) AS u WHERE u.id = :user_id"
    info = parser.get_method_info(sql)
    assert info["type"] == "select"
    assert info["is_fetch"]
    assert "user_id" in info["parameters"]

    # Complex parameter extraction
    sql = """
        SELECT u.name, p.title 
        FROM users u 
        JOIN posts p ON u.id = p.user_id 
        WHERE u.id = :user_id AND p.status = :status
        """
    info = parser.get_method_info(sql)
    assert "user_id" in info["parameters"]
    assert "status" in info["parameters"]
    assert len(info["parameters"]) == 2

    # VALUES-only query
    sql = "VALUES (1,'a'), (2,'b')"
    info = parser.get_method_info(sql)
    assert info["type"] == "values"
    assert info["is_fetch"]

    # SHOW with parameters in string literal should not be extracted
    sql = "SHOW TABLES -- :not_a_param"
    info = parser.get_method_info(sql)
    assert info["type"] == "show"
    assert info["parameters"] == []

    # WITH RECURSIVE select
    sql = """
        WITH RECURSIVE cte(n) AS (
            SELECT 1
            UNION ALL
            SELECT n+1 FROM cte WHERE n < 3
        )
        SELECT * FROM cte
        """
    info = parser.get_method_info(sql)
    assert info["type"] == "cte"
    assert info["is_fetch"]


def test_get_method_info_parameter_extraction(parser):
    # Multiple parameters
    sql = "SELECT * FROM users WHERE id = :user_id AND status = :status"
    info = parser.get_method_info(sql)
    assert "user_id" in info["parameters"]
    assert "status" in info["parameters"]
    assert len(info["parameters"]) == 2

    # Duplicate parameters (should be deduplicated)
    sql = "SELECT * FROM users WHERE id = :user_id OR parent_id = :user_id"
    info = parser.get_method_info(sql)
    assert "user_id" in info["parameters"]
    assert len(info["parameters"]) == 1

    # Parameters with underscores and numbers
    sql = "SELECT * FROM users WHERE user_id_123 = :user_id_123"
    info = parser.get_method_info(sql)
    assert "user_id_123" in info["parameters"]

    # No parameters
    sql = "SELECT COUNT(*) FROM users"
    info = parser.get_method_info(sql)
    assert info["parameters"] == []

    # Parameters in different contexts
    sql = """
        INSERT INTO users (name, email, status) 
        VALUES (:name, :email, :status) 
        RETURNING id
        """
    info = parser.get_method_info(sql)
    assert "name" in info["parameters"]
    assert "email" in info["parameters"]
    assert "status" in info["parameters"]
    assert info["has_returning"]

    # Parameter-like sequence in string should be ignored
    sql = "SELECT ':not_a_param' as s, col as c FROM t WHERE x = :x"
    info = parser.get_method_info(sql)
    assert "x" in info["parameters"]
    assert len(info["parameters"]) == 1


def test_parameter_extraction_colon_then_comment_then_name(parser):
    """Detect parameter when ':' is followed by a comment then identifier."""
    sql = "SELECT * FROM users WHERE id = : /* inline */ user_id"
    info = parser.get_method_info(sql)
    assert "user_id" in info["parameters"]


def test_get_method_info_edge_cases(parser):
    # Empty SQL
    info = parser.get_method_info("")
    assert info["type"] == "other"
    assert not info["is_fetch"]
    assert info["parameters"] == []

    # Whitespace only
    info = parser.get_method_info("   ")
    assert info["type"] == "other"
    assert not info["is_fetch"]

    # SQL with comments
    sql = "SELECT * FROM users -- comment\nWHERE id = :user_id"
    info = parser.get_method_info(sql)
    assert info["type"] == "select"
    assert "user_id" in info["parameters"]

    # Case insensitive matching
    sql = "select * from users where id = :user_id"
    info = parser.get_method_info(sql)
    assert info["type"] == "select"

    sql = "Select * from users where id = :user_id"
    info = parser.get_method_info(sql)
    assert info["type"] == "select"

    # CREATE TABLE classified as execute and maps to 'other'
    info = parser.get_method_info("CREATE TABLE t (id INT)")
    assert info["type"] == "other"
    assert not info["is_fetch"]

    # Update with FROM and RETURNING
    sql = "UPDATE t1 SET x=:x FROM t2 WHERE t1.id=t2.id RETURNING t1.id"
    info = parser.get_method_info(sql)
    assert info["type"] == "update"
    assert not info["is_fetch"]  # execute
    assert info["has_returning"]  # flag still true


def test_parse_file_not_found(parser):
    from splurge_sql_generator.exceptions import FileError

    with pytest.raises(FileError):
        parser.parse_file("nonexistent_file.sql")


def test_parse_file_encoding(parser):
    # Test with UTF-8 content
    sql = """# TestClass
#get_user_with_unicode
SELECT * FROM users WHERE name = :name;
        """
    with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".sql", encoding="utf-8") as f:
        f.write(sql)
        fname = f.name
    try:
        class_name, methods = parser.parse_file(fname)
        assert class_name == "TestClass"
        assert "get_user_with_unicode" in methods
    finally:
        os.remove(fname)


def test_parse_file_missing_class_comment(parser):
    """Test that parse_file raises SqlValidationError when first line is not a class comment."""
    sql = """get_user
SELECT * FROM users WHERE id = :user_id;
        """
    with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".sql") as f:
        f.write(sql)
        fname = f.name
    try:
        with pytest.raises(SqlValidationError) as cm:
            parser.parse_file(fname)
        assert "First line must be a class comment" in str(cm.value)
    finally:
        os.remove(fname)


def test_parse_file_empty_class_comment(parser):
    """Test that parse_file raises SqlValidationError when class comment is empty."""
    sql = """#
#get_user
SELECT * FROM users WHERE id = :user_id;
        """
    with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".sql") as f:
        f.write(sql)
        fname = f.name
    try:
        with pytest.raises(SqlValidationError) as cm:
            parser.parse_file(fname)
        assert "Class name cannot be empty" in str(cm.value)
    finally:
        os.remove(fname)


def test_parse_file_invalid_class_comment_format(parser):
    """Test that parse_file raises SqlValidationError when class comment doesn't start with '#'."""
    sql = """TestClass
#get_user
SELECT * FROM users WHERE id = :user_id;
        """
    with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".sql") as f:
        f.write(sql)
        fname = f.name
    try:
        with pytest.raises(SqlValidationError) as cm:
            parser.parse_file(fname)
        assert "First line must be a class comment" in str(cm.value)
    finally:
        os.remove(fname)


def test_parse_file_empty_file(parser):
    """Test that parse_file raises ValueError when file is empty."""
    with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".sql") as f:
        f.write("")
        fname = f.name
    try:
        from splurge_sql_generator.exceptions import SqlValidationError

        with pytest.raises(SqlValidationError) as cm:
            parser.parse_file(fname)
        assert "First line must be a class comment" in str(cm.value)
    finally:
        os.remove(fname)


def test_parse_string_basic(parser):
    """Test parse_string with valid SQL content."""
    sql = """# TestClass
#get_user
SELECT * FROM users WHERE id = :user_id;

#create_user
INSERT INTO users (name, email) VALUES (:name, :email);
        """
    class_name, methods = parser.parse_string(sql)
    assert class_name == "TestClass"
    assert "get_user" in methods
    assert "create_user" in methods
    assert methods["get_user"].startswith("SELECT")


def test_parse_string_with_file_path(parser):
    """Test parse_string with file path for error context."""
    sql = """# TestClass
#get_user
SELECT * FROM users WHERE id = :user_id;
        """
    class_name, methods = parser.parse_string(sql, "test.sql")
    assert class_name == "TestClass"
    assert "get_user" in methods


def test_parse_string_missing_class_comment(parser):
    """Test parse_string raises error when first line is not a class comment."""
    sql = """get_user
SELECT * FROM users WHERE id = :user_id;
        """
    with pytest.raises(SqlValidationError) as cm:
        parser.parse_string(sql)
    assert "First line must be a class comment" in str(cm.value)


def test_parse_string_missing_class_comment_with_file_path(parser):
    """Test parse_string error includes file path when provided."""
    sql = """get_user
SELECT * FROM users WHERE id = :user_id;
        """
    with pytest.raises(SqlValidationError) as cm:
        parser.parse_string(sql, "test.sql")
    assert "First line must be a class comment starting with # in test.sql" in str(cm.value)


def test_parse_string_empty_class_comment(parser):
    """Test parse_string raises error when class comment is empty."""
    sql = """# 
#get_user
SELECT * FROM users WHERE id = :user_id;
        """
    with pytest.raises(SqlValidationError) as cm:
        parser.parse_string(sql)
    assert "Class name cannot be empty" in str(cm.value)


def test_parse_string_invalid_class_comment_format(parser):
    """Test parse_string raises error when class comment doesn't start with '#'."""
    sql = """TestClass
#get_user
SELECT * FROM users WHERE id = :user_id;
        """
    with pytest.raises(SqlValidationError) as cm:
        parser.parse_string(sql)
    assert "First line must be a class comment" in str(cm.value)


def test_parse_string_leading_whitespace_before_hash_raises(parser):
    """Leading spaces before '#' on first line should raise due to strict startswith check."""
    sql = """   # TestClass
#get_user
SELECT * FROM users WHERE id = :user_id;
        """
    with pytest.raises(SqlValidationError) as cm:
        parser.parse_string(sql)
    assert "First line must be a class comment" in str(cm.value)


def test_parse_string_empty_content(parser):
    """Test parse_string raises error when content is empty."""
    with pytest.raises(SqlValidationError) as cm:
        parser.parse_string("")
    assert "First line must be a class comment" in str(cm.value)


def test_parse_string_invalid_class_name(parser):
    """Test parse_string raises error when class name is invalid."""
    sql = """# 123InvalidClass
#get_user
SELECT * FROM users WHERE id = :user_id;
        """
    with pytest.raises(SqlValidationError) as cm:
        parser.parse_string(sql)
    assert "Class name must be a valid Python identifier" in str(cm.value)


def test_parse_string_reserved_keyword_class_name(parser):
    """Test parse_string raises error when class name is a reserved keyword."""
    sql = """# class
#get_user
SELECT * FROM users WHERE id = :user_id;
        """
    with pytest.raises(SqlValidationError) as cm:
        parser.parse_string(sql)
    assert "Class name cannot be a reserved keyword" in str(cm.value)


def test_parse_string_class_comment_formats(parser):
    """Test parse_string accepts both '#Class' and '# Class' formats."""
    # Test without space
    sql1 = """#TestClass
#get_user
SELECT * FROM users WHERE id = :user_id;
        """
    class_name1, methods1 = parser.parse_string(sql1)
    assert class_name1 == "TestClass"
    assert "get_user" in methods1

    # Test with space
    sql2 = """# TestClass
#get_user
SELECT * FROM users WHERE id = :user_id;
        """
    class_name2, methods2 = parser.parse_string(sql2)
    assert class_name2 == "TestClass"
    assert "get_user" in methods2


def test_get_method_info_with_file_path(parser):
    """Test get_method_info with file path for error context."""
    sql = "SELECT * FROM users WHERE id = :class"  # 'class' is a reserved keyword
    with pytest.raises(SqlValidationError) as cm:
        parser.get_method_info(sql, "test.sql")
    assert "Parameter name cannot be a reserved keyword in test.sql" in str(cm.value)


def test_get_method_info_parameter_fallback_on_sqlparse_error(parser):
    """Fallback regex path is used when sqlparse.parse raises; parameters are still captured."""
    from unittest.mock import patch

    import splurge_sql_generator.sql_parser as sql_parser_module

    def raise_err(_):
        raise RuntimeError("boom")

    with (
        patch.object(sql_parser_module.sqlparse, "parse", side_effect=raise_err),
        patch.object(
            sql_parser_module,
            "detect_statement_type",
            return_value=sql_parser_module.FETCH_STATEMENT,
        ),
    ):
        parser = sql_parser_module.SqlParser()
        sql = "SELECT * FROM users WHERE id = :id AND status = :status"
        info = parser.get_method_info(sql)
        assert info["parameters"] == ["id", "status"]
