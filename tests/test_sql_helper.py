import os
import tempfile
import unittest

from jpy_sql_generator import sql_helper


class TestSqlHelper(unittest.TestCase):
    def test_remove_sql_comments(self):
        sql = """
        SELECT * FROM users -- comment
        /* block comment */
        WHERE id = 1; -- another
        """
        result = sql_helper.remove_sql_comments(sql)
        self.assertNotIn("--", result)
        self.assertNotIn("/*", result)
        self.assertIn("SELECT * FROM users", result)

    def test_remove_sql_comments_empty(self):
        self.assertEqual(sql_helper.remove_sql_comments(""), "")
        self.assertEqual(sql_helper.remove_sql_comments(None), "")

    def test_detect_statement_type(self):
        self.assertEqual(
            sql_helper.detect_statement_type("SELECT * FROM users"),
            sql_helper.FETCH_STATEMENT,
        )
        self.assertEqual(
            sql_helper.detect_statement_type("INSERT INTO users VALUES (1)"),
            sql_helper.EXECUTE_STATEMENT,
        )
        self.assertEqual(
            sql_helper.detect_statement_type("UPDATE users SET x=1"),
            sql_helper.EXECUTE_STATEMENT,
        )
        self.assertEqual(
            sql_helper.detect_statement_type("DELETE FROM users"),
            sql_helper.EXECUTE_STATEMENT,
        )
        self.assertEqual(
            sql_helper.detect_statement_type("SHOW TABLES"), sql_helper.FETCH_STATEMENT
        )
        self.assertEqual(
            sql_helper.detect_statement_type("DESCRIBE users"),
            sql_helper.FETCH_STATEMENT,
        )
        self.assertEqual(
            sql_helper.detect_statement_type(
                "WITH cte AS (SELECT 1) SELECT * FROM cte"
            ),
            sql_helper.FETCH_STATEMENT,
        )
        self.assertEqual(
            sql_helper.detect_statement_type(
                "WITH cte AS (SELECT 1) INSERT INTO t SELECT * FROM cte"
            ),
            sql_helper.EXECUTE_STATEMENT,
        )
        self.assertEqual(
            sql_helper.detect_statement_type(""), sql_helper.EXECUTE_STATEMENT
        )
        self.assertEqual(
            sql_helper.detect_statement_type(None), sql_helper.EXECUTE_STATEMENT
        )

    def test_detect_statement_type_cte_multiple(self):
        sql = """
        WITH a AS (SELECT 1), b AS (SELECT 2) SELECT * FROM a JOIN b ON a.x = b.x;
        """
        self.assertEqual(sql_helper.detect_statement_type(sql), sql_helper.FETCH_STATEMENT)

    def test_detect_statement_type_cte_insert(self):
        sql = """
        WITH a AS (SELECT 1) INSERT INTO t SELECT * FROM a;
        """
        self.assertEqual(sql_helper.detect_statement_type(sql), sql_helper.EXECUTE_STATEMENT)

    def test_detect_statement_type_empty_or_whitespace(self):
        self.assertEqual(sql_helper.detect_statement_type("   "), sql_helper.EXECUTE_STATEMENT)
        self.assertEqual(sql_helper.detect_statement_type(None), sql_helper.EXECUTE_STATEMENT)

    def test_parse_sql_statements(self):
        sql = """
        SELECT 1;
        INSERT INTO t VALUES (2);
        -- comment only
        SELECT 3;
        """
        stmts = sql_helper.parse_sql_statements(sql)
        self.assertEqual(len(stmts), 3)
        self.assertTrue(all(stmt.strip().endswith(";") for stmt in stmts))

    def test_parse_sql_statements_strip_semicolon(self):
        sql = "SELECT 1; INSERT INTO t VALUES (2);"
        stmts = sql_helper.parse_sql_statements(sql, strip_semicolon=True)
        self.assertTrue(all(not stmt.strip().endswith(";") for stmt in stmts))

    def test_parse_sql_statements_empty(self):
        self.assertEqual(sql_helper.parse_sql_statements(""), [])
        self.assertEqual(sql_helper.parse_sql_statements(None), [])

    def test_parse_sql_statements_all_comments(self):
        sql = """
        -- comment only
        /* block comment */
        """
        self.assertEqual(sql_helper.parse_sql_statements(sql), [])

    def test_parse_sql_statements_semicolon_only(self):
        sql = "; ; ;"
        self.assertEqual(sql_helper.parse_sql_statements(sql), [])

    def test_split_sql_file(self):
        sql = "SELECT 1; INSERT INTO t VALUES (2);"
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".sql") as f:
            f.write(sql)
            fname = f.name
        try:
            stmts = sql_helper.split_sql_file(fname)
            self.assertEqual(len(stmts), 2)
        finally:
            os.remove(fname)

    def test_split_sql_file_errors(self):
        with self.assertRaises(ValueError):
            sql_helper.split_sql_file("")
        with self.assertRaises(ValueError):
            sql_helper.split_sql_file(None)
        with self.assertRaises(FileNotFoundError):
            sql_helper.split_sql_file("nonexistent_file.sql")

    def test_split_sql_file_invalid_type(self):
        with self.assertRaises(ValueError):
            sql_helper.split_sql_file(123)

    def test_split_sql_file_empty(self):
        with self.assertRaises(ValueError):
            sql_helper.split_sql_file("")

    def test_split_sql_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            sql_helper.split_sql_file("not_a_real_file.sql")
    
    def test_detect_statement_type_nested_cte(self):
        sql = '''
        WITH a AS (SELECT 1), b AS (WITH c AS (SELECT 2) SELECT * FROM c) SELECT * FROM a JOIN b ON 1=1;
        '''
        self.assertEqual(sql_helper.detect_statement_type(sql), sql_helper.FETCH_STATEMENT)

    def test_detect_statement_type_cte_with_as_keyword(self):
        sql = '''
        WITH a AS (SELECT 1) SELECT * FROM a AS alias;
        '''
        self.assertEqual(sql_helper.detect_statement_type(sql), sql_helper.FETCH_STATEMENT)

    def test_detect_statement_type_pragma(self):
        sql = 'PRAGMA table_info(users);'
        self.assertEqual(sql_helper.detect_statement_type(sql), sql_helper.FETCH_STATEMENT)

    def test_detect_statement_type_explain(self):
        sql = 'EXPLAIN SELECT * FROM users;'
        self.assertEqual(sql_helper.detect_statement_type(sql), sql_helper.FETCH_STATEMENT)

    def test_detect_statement_type_show(self):
        sql = 'SHOW TABLES;'
        self.assertEqual(sql_helper.detect_statement_type(sql), sql_helper.FETCH_STATEMENT)

    def test_detect_statement_type_values(self):
        sql = 'VALUES (1), (2);'
        self.assertEqual(sql_helper.detect_statement_type(sql), sql_helper.FETCH_STATEMENT)

    def test_parse_sql_statements_whitespace_and_comments(self):
        sql = '\n   -- comment\n   /* block */\n   SELECT 1;\n\n'
        stmts = sql_helper.parse_sql_statements(sql)
        self.assertEqual(len(stmts), 1)
        self.assertTrue(stmts[0].strip().startswith('SELECT'))

    def test_parse_sql_statements_multiple_semicolons(self):
        sql = 'SELECT 1;;;;;SELECT 2;'
        stmts = sql_helper.parse_sql_statements(sql)
        self.assertEqual(len(stmts), 2)

    def test_parse_sql_statements_only_semicolons_and_comments(self):
        sql = '; -- comment\n; /* block */ ;'
        stmts = sql_helper.parse_sql_statements(sql)
        self.assertEqual(stmts, [])

    
if __name__ == "__main__":
    unittest.main()
