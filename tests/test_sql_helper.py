import unittest
from jpy_sql_generator import sql_helper
import tempfile
import os

class TestSqlHelper(unittest.TestCase):
    def test_remove_sql_comments(self):
        sql = """
        SELECT * FROM users -- comment
        /* block comment */
        WHERE id = 1; -- another
        """
        result = sql_helper.remove_sql_comments(sql)
        self.assertNotIn('--', result)
        self.assertNotIn('/*', result)
        self.assertIn('SELECT * FROM users', result)

    def test_remove_sql_comments_empty(self):
        self.assertEqual(sql_helper.remove_sql_comments(''), '')
        self.assertEqual(sql_helper.remove_sql_comments(None), None)

    def test_detect_statement_type(self):
        self.assertEqual(sql_helper.detect_statement_type('SELECT * FROM users'), sql_helper.FETCH_STATEMENT)
        self.assertEqual(sql_helper.detect_statement_type('INSERT INTO users VALUES (1)'), sql_helper.EXECUTE_STATEMENT)
        self.assertEqual(sql_helper.detect_statement_type('UPDATE users SET x=1'), sql_helper.EXECUTE_STATEMENT)
        self.assertEqual(sql_helper.detect_statement_type('DELETE FROM users'), sql_helper.EXECUTE_STATEMENT)
        self.assertEqual(sql_helper.detect_statement_type('SHOW TABLES'), sql_helper.FETCH_STATEMENT)
        self.assertEqual(sql_helper.detect_statement_type('DESCRIBE users'), sql_helper.FETCH_STATEMENT)
        self.assertEqual(sql_helper.detect_statement_type('WITH cte AS (SELECT 1) SELECT * FROM cte'), sql_helper.FETCH_STATEMENT)
        self.assertEqual(sql_helper.detect_statement_type('WITH cte AS (SELECT 1) INSERT INTO t SELECT * FROM cte'), sql_helper.EXECUTE_STATEMENT)
        self.assertEqual(sql_helper.detect_statement_type(''), sql_helper.EXECUTE_STATEMENT)
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
        self.assertTrue(all(stmt.strip().endswith(';') for stmt in stmts))

    def test_parse_sql_statements_strip_semicolon(self):
        sql = "SELECT 1; INSERT INTO t VALUES (2);"
        stmts = sql_helper.parse_sql_statements(sql, strip_semicolon=True)
        self.assertTrue(all(not stmt.strip().endswith(';') for stmt in stmts))

    def test_parse_sql_statements_empty(self):
        self.assertEqual(sql_helper.parse_sql_statements(''), [])
        self.assertEqual(sql_helper.parse_sql_statements(None), [])

    def test_split_sql_file(self):
        sql = "SELECT 1; INSERT INTO t VALUES (2);"
        with tempfile.NamedTemporaryFile('w+', delete=False, suffix='.sql') as f:
            f.write(sql)
            fname = f.name
        try:
            stmts = sql_helper.split_sql_file(fname)
            self.assertEqual(len(stmts), 2)
        finally:
            os.remove(fname)

    def test_split_sql_file_errors(self):
        with self.assertRaises(ValueError):
            sql_helper.split_sql_file('')
        with self.assertRaises(ValueError):
            sql_helper.split_sql_file(None)
        with self.assertRaises(FileNotFoundError):
            sql_helper.split_sql_file('nonexistent_file.sql')

if __name__ == '__main__':
    unittest.main() 