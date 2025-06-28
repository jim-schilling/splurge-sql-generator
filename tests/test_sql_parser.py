import unittest
import tempfile
import os
from jpy_sql_generator.sql_parser import SqlParser

class TestSqlParser(unittest.TestCase):
    def setUp(self):
        self.parser = SqlParser()

    def test_parse_file_and_extract_methods(self):
        sql = """# TestClass
#get_user
SELECT * FROM users WHERE id = :user_id;

#create_user
INSERT INTO users (name, email) VALUES (:name, :email);
        """
        with tempfile.NamedTemporaryFile('w+', delete=False, suffix='.sql') as f:
            f.write(sql)
            fname = f.name
        try:
            class_name, methods = self.parser.parse_file(fname)
            self.assertEqual(class_name, 'TestClass')
            self.assertIn('get_user', methods)
            self.assertIn('create_user', methods)
            self.assertTrue(methods['get_user'].startswith('SELECT'))
        finally:
            os.remove(fname)

    def test_extract_methods_and_queries(self):
        sql = """
#get_one
SELECT 1;
#get_two
SELECT 2;
        """
        methods = self.parser._extract_methods_and_queries(sql)
        self.assertEqual(len(methods), 2)
        self.assertIn('get_one', methods)
        self.assertIn('get_two', methods)

    def test_extract_methods_edge_cases(self):
        # Empty content
        methods = self.parser._extract_methods_and_queries("")
        self.assertEqual(methods, {})
        
        # Content with no methods
        methods = self.parser._extract_methods_and_queries("SELECT * FROM users;")
        self.assertEqual(methods, {})
        
        # Method with no SQL
        methods = self.parser._extract_methods_and_queries("#get_user\n\n#get_two\nSELECT 2;")
        self.assertIn('get_two', methods)
        self.assertNotIn('get_user', methods)

    def test_sql_cleaning_with_sql_helper(self):
        """Test that SQL cleaning using sql_helper works correctly."""
        # Test that semicolons are stripped
        methods = self.parser._extract_methods_and_queries("#test_method\nSELECT 1;")
        self.assertEqual(methods['test_method'], 'SELECT 1')
        
        # Test that whitespace is trimmed
        methods = self.parser._extract_methods_and_queries("#test_method\n  SELECT 2  ")
        self.assertEqual(methods['test_method'], 'SELECT 2')
        
        # Test that multiple semicolons are handled
        methods = self.parser._extract_methods_and_queries("#test_method\nSELECT 3;;")
        self.assertEqual(methods['test_method'], 'SELECT 3;')
        
        # Test empty SQL is handled
        methods = self.parser._extract_methods_and_queries("#test_method\n   ")
        self.assertNotIn('test_method', methods)

    def test_get_method_info_basic_types(self):
        # SELECT statements
        info = self.parser.get_method_info('SELECT * FROM users WHERE id = :user_id')
        self.assertEqual(info['type'], 'select')
        self.assertTrue(info['is_fetch'])
        self.assertIn('user_id', info['parameters'])
        self.assertFalse(info['has_returning'])

        # INSERT statements
        info = self.parser.get_method_info('INSERT INTO users (name) VALUES (:name) RETURNING id')
        self.assertEqual(info['type'], 'insert')
        self.assertFalse(info['is_fetch'])
        self.assertIn('name', info['parameters'])
        self.assertTrue(info['has_returning'])

        # UPDATE statements
        info = self.parser.get_method_info('UPDATE users SET x=1 WHERE id=:id')
        self.assertEqual(info['type'], 'update')
        self.assertFalse(info['is_fetch'])
        self.assertIn('id', info['parameters'])

        # DELETE statements
        info = self.parser.get_method_info('DELETE FROM users WHERE id=:id')
        self.assertEqual(info['type'], 'delete')
        self.assertFalse(info['is_fetch'])
        self.assertIn('id', info['parameters'])

        # CTE statements
        info = self.parser.get_method_info('WITH cte AS (SELECT 1) SELECT * FROM cte')
        self.assertEqual(info['type'], 'cte')
        self.assertTrue(info['is_fetch'])

        # Other statement types
        info = self.parser.get_method_info('SHOW TABLES')
        self.assertEqual(info['type'], 'show')
        self.assertTrue(info['is_fetch'])

        info = self.parser.get_method_info('EXPLAIN SELECT 1')
        self.assertEqual(info['type'], 'explain')
        self.assertTrue(info['is_fetch'])

        info = self.parser.get_method_info('DESCRIBE users')
        self.assertEqual(info['type'], 'describe')
        self.assertTrue(info['is_fetch'])

        info = self.parser.get_method_info('VALUES (1, 2), (3, 4)')
        self.assertEqual(info['type'], 'values')
        self.assertTrue(info['is_fetch'])

    def test_get_method_info_complex_sql(self):
        # Complex CTE with multiple CTEs
        sql = """
        WITH cte1 AS (SELECT 1 as id),
             cte2 AS (SELECT 2 as id)
        SELECT * FROM cte1 UNION SELECT * FROM cte2
        """
        info = self.parser.get_method_info(sql)
        self.assertEqual(info['type'], 'cte')
        self.assertTrue(info['is_fetch'])

        # CTE with INSERT
        sql = """
        WITH temp_data AS (SELECT id, name FROM source_table)
        INSERT INTO target_table (id, name)
        SELECT id, name FROM temp_data
        """
        info = self.parser.get_method_info(sql)
        self.assertEqual(info['type'], 'cte')
        self.assertFalse(info['is_fetch'])

        # Subquery in FROM clause
        sql = "SELECT * FROM (SELECT id, name FROM users) AS u WHERE u.id = :user_id"
        info = self.parser.get_method_info(sql)
        self.assertEqual(info['type'], 'select')
        self.assertTrue(info['is_fetch'])
        self.assertIn('user_id', info['parameters'])

        # Complex parameter extraction
        sql = """
        SELECT u.name, p.title 
        FROM users u 
        JOIN posts p ON u.id = p.user_id 
        WHERE u.id = :user_id AND p.status = :status
        """
        info = self.parser.get_method_info(sql)
        self.assertIn('user_id', info['parameters'])
        self.assertIn('status', info['parameters'])
        self.assertEqual(len(info['parameters']), 2)

    def test_get_method_info_parameter_extraction(self):
        # Multiple parameters
        sql = "SELECT * FROM users WHERE id = :user_id AND status = :status"
        info = self.parser.get_method_info(sql)
        self.assertIn('user_id', info['parameters'])
        self.assertIn('status', info['parameters'])
        self.assertEqual(len(info['parameters']), 2)

        # Duplicate parameters (should be deduplicated)
        sql = "SELECT * FROM users WHERE id = :user_id OR parent_id = :user_id"
        info = self.parser.get_method_info(sql)
        self.assertIn('user_id', info['parameters'])
        self.assertEqual(len(info['parameters']), 1)

        # Parameters with underscores and numbers
        sql = "SELECT * FROM users WHERE user_id_123 = :user_id_123"
        info = self.parser.get_method_info(sql)
        self.assertIn('user_id_123', info['parameters'])

        # No parameters
        sql = "SELECT COUNT(*) FROM users"
        info = self.parser.get_method_info(sql)
        self.assertEqual(info['parameters'], [])

        # Parameters in different contexts
        sql = """
        INSERT INTO users (name, email, status) 
        VALUES (:name, :email, :status) 
        RETURNING id
        """
        info = self.parser.get_method_info(sql)
        self.assertIn('name', info['parameters'])
        self.assertIn('email', info['parameters'])
        self.assertIn('status', info['parameters'])
        self.assertTrue(info['has_returning'])

    def test_get_method_info_edge_cases(self):
        # Empty SQL
        info = self.parser.get_method_info('')
        self.assertEqual(info['type'], 'other')
        self.assertFalse(info['is_fetch'])
        self.assertEqual(info['parameters'], [])

        # Whitespace only
        info = self.parser.get_method_info('   ')
        self.assertEqual(info['type'], 'other')
        self.assertFalse(info['is_fetch'])

        # SQL with comments
        sql = "SELECT * FROM users -- comment\nWHERE id = :user_id"
        info = self.parser.get_method_info(sql)
        self.assertEqual(info['type'], 'select')
        self.assertIn('user_id', info['parameters'])

        # Case insensitive matching
        sql = "select * from users where id = :user_id"
        info = self.parser.get_method_info(sql)
        self.assertEqual(info['type'], 'select')

        sql = "Select * from users where id = :user_id"
        info = self.parser.get_method_info(sql)
        self.assertEqual(info['type'], 'select')

    def test_parse_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            self.parser.parse_file('nonexistent_file.sql')

    def test_parse_file_encoding(self):
        # Test with UTF-8 content
        sql = """# TestClass
#get_user_with_unicode
SELECT * FROM users WHERE name = :name;
        """
        with tempfile.NamedTemporaryFile('w+', delete=False, suffix='.sql', encoding='utf-8') as f:
            f.write(sql)
            fname = f.name
        try:
            class_name, methods = self.parser.parse_file(fname)
            self.assertEqual(class_name, 'TestClass')
            self.assertIn('get_user_with_unicode', methods)
        finally:
            os.remove(fname)

    def test_parse_file_missing_class_comment(self):
        """Test that parse_file raises ValueError when first line is not a class comment."""
        sql = """#get_user
SELECT * FROM users WHERE id = :user_id;
        """
        with tempfile.NamedTemporaryFile('w+', delete=False, suffix='.sql') as f:
            f.write(sql)
            fname = f.name
        try:
            with self.assertRaises(ValueError) as cm:
                self.parser.parse_file(fname)
            self.assertIn("Class comment must start with '# '", str(cm.exception))
        finally:
            os.remove(fname)

    def test_parse_file_empty_class_comment(self):
        """Test that parse_file raises ValueError when class comment is empty."""
        sql = """# 
#get_user
SELECT * FROM users WHERE id = :user_id;
        """
        with tempfile.NamedTemporaryFile('w+', delete=False, suffix='.sql') as f:
            f.write(sql)
            fname = f.name
        try:
            with self.assertRaises(ValueError) as cm:
                self.parser.parse_file(fname)
            self.assertIn("Class comment must start with '# '", str(cm.exception))
        finally:
            os.remove(fname)

    def test_parse_file_invalid_class_comment_format(self):
        """Test that parse_file raises ValueError when class comment doesn't start with '# '."""
        sql = """#TestClass
#get_user
SELECT * FROM users WHERE id = :user_id;
        """
        with tempfile.NamedTemporaryFile('w+', delete=False, suffix='.sql') as f:
            f.write(sql)
            fname = f.name
        try:
            with self.assertRaises(ValueError) as cm:
                self.parser.parse_file(fname)
            self.assertIn("Class comment must start with '# '", str(cm.exception))
        finally:
            os.remove(fname)

    def test_parse_file_empty_file(self):
        """Test that parse_file raises ValueError when file is empty."""
        with tempfile.NamedTemporaryFile('w+', delete=False, suffix='.sql') as f:
            f.write("")
            fname = f.name
        try:
            with self.assertRaises(ValueError) as cm:
                self.parser.parse_file(fname)
            self.assertIn("First line must be a class comment starting with #", str(cm.exception))
        finally:
            os.remove(fname)

if __name__ == '__main__':
    unittest.main() 