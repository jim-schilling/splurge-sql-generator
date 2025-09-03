"""
Unit tests for SQL statement type detection.

Tests the detect_statement_type function from the sql_helper module.
"""


from splurge_sql_generator.sql_helper import (
    detect_statement_type,
    EXECUTE_STATEMENT,
    FETCH_STATEMENT,
)


class TestDetectStatementType:
    """Test SQL statement type detection."""

    def test_empty_string(self):
        """Test detecting type of empty string."""
        result = detect_statement_type("")
        assert result == EXECUTE_STATEMENT

    def test_whitespace_only(self):
        """Test detecting type of whitespace-only string."""
        result = detect_statement_type("   \n\t  ")
        assert result == EXECUTE_STATEMENT

    def test_simple_select(self):
        """Test detecting SELECT statement type."""
        result = detect_statement_type("SELECT * FROM users")
        assert result == FETCH_STATEMENT

    def test_select_with_comments(self):
        """Test detecting SELECT statement with comments."""
        sql = """
        -- Get all users
        SELECT * FROM users
        WHERE active = 1 -- Only active users
        """
        result = detect_statement_type(sql)
        assert result == FETCH_STATEMENT

    def test_values_statement(self):
        """Test detecting VALUES statement type."""
        result = detect_statement_type("VALUES (1, 'Alice'), (2, 'Bob')")
        assert result == FETCH_STATEMENT

    def test_show_statement(self):
        """Test detecting SHOW statement type."""
        result = detect_statement_type("SHOW TABLES")
        assert result == FETCH_STATEMENT

    def test_explain_statement(self):
        """Test detecting EXPLAIN statement type."""
        result = detect_statement_type("EXPLAIN SELECT * FROM users")
        assert result == FETCH_STATEMENT

    def test_pragma_statement(self):
        """Test detecting PRAGMA statement type."""
        result = detect_statement_type("PRAGMA table_info(users)")
        assert result == FETCH_STATEMENT

    def test_describe_statement(self):
        """Test detecting DESCRIBE statement type."""
        result = detect_statement_type("DESCRIBE users")
        assert result == FETCH_STATEMENT

    def test_desc_statement(self):
        """Test detecting DESC statement type."""
        result = detect_statement_type("DESC users")
        assert result == FETCH_STATEMENT

    def test_insert_statement(self):
        """Test detecting INSERT statement type."""
        result = detect_statement_type("INSERT INTO users (name) VALUES ('John')")
        assert result == EXECUTE_STATEMENT

    def test_update_statement(self):
        """Test detecting UPDATE statement type."""
        result = detect_statement_type("UPDATE users SET active = 1 WHERE id = 1")
        assert result == EXECUTE_STATEMENT

    def test_delete_statement(self):
        """Test detecting DELETE statement type."""
        result = detect_statement_type("DELETE FROM users WHERE id = 1")
        assert result == EXECUTE_STATEMENT

    def test_create_table_statement(self):
        """Test detecting CREATE TABLE statement type."""
        result = detect_statement_type("CREATE TABLE users (id INT, name TEXT)")
        assert result == EXECUTE_STATEMENT

    def test_alter_table_statement(self):
        """Test detecting ALTER TABLE statement type."""
        result = detect_statement_type("ALTER TABLE users ADD COLUMN email TEXT")
        assert result == EXECUTE_STATEMENT

    def test_drop_table_statement(self):
        """Test detecting DROP TABLE statement type."""
        result = detect_statement_type("DROP TABLE users")
        assert result == EXECUTE_STATEMENT

    def test_cte_with_select(self):
        """Test detecting CTE with SELECT statement type."""
        sql = """
        WITH active_users AS (
            SELECT id, name FROM users WHERE active = 1
        )
        SELECT * FROM active_users
        """
        result = detect_statement_type(sql)
        assert result == FETCH_STATEMENT

    def test_cte_with_insert(self):
        """Test detecting CTE with INSERT statement type."""
        sql = """
        WITH new_data AS (
            SELECT 'John' as name, 25 as age
        )
        INSERT INTO users (name, age) SELECT * FROM new_data
        """
        result = detect_statement_type(sql)
        assert result == EXECUTE_STATEMENT

    def test_cte_with_update(self):
        """Test detecting CTE with UPDATE statement type."""
        sql = """
        WITH user_updates AS (
            SELECT id, 'new_name' as name FROM users WHERE id = 1
        )
        UPDATE users SET name = u.name FROM user_updates u WHERE users.id = u.id
        """
        result = detect_statement_type(sql)
        assert result == EXECUTE_STATEMENT

    def test_complex_cte(self):
        """Test detecting complex CTE statement type."""
        sql = """
        WITH 
        active_users AS (
            SELECT id, name FROM users WHERE active = 1
        ),
        user_stats AS (
            SELECT user_id, COUNT(*) as post_count 
            FROM posts 
            GROUP BY user_id
        )
        SELECT u.name, s.post_count 
        FROM active_users u 
        JOIN user_stats s ON u.id = s.user_id
        """
        result = detect_statement_type(sql)
        assert result == FETCH_STATEMENT

    def test_case_insensitive_keywords(self):
        """Test that keywords are detected case-insensitively."""
        result1 = detect_statement_type("select * from users")
        result2 = detect_statement_type("SELECT * FROM users")
        assert result1 == result2 == FETCH_STATEMENT

        result3 = detect_statement_type("insert into users values (1)")
        result4 = detect_statement_type("INSERT INTO users VALUES (1)")
        assert result3 == result4 == EXECUTE_STATEMENT
