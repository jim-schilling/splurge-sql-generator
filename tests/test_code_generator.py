import unittest
import tempfile
import os
import ast
from jpy_sql_generator.code_generator import PythonCodeGenerator
from jpy_sql_generator.sql_parser import SqlParser

class TestPythonCodeGenerator(unittest.TestCase):
    def setUp(self):
        self.generator = PythonCodeGenerator()
        self.parser = SqlParser()

    def test_generate_class_and_methods(self):
        sql = """
#get_user
SELECT * FROM users WHERE id = :user_id;
#create_user
INSERT INTO users (name, email) VALUES (:name, :email);
        """
        with tempfile.NamedTemporaryFile('w+', delete=False, suffix='.sql') as f:
            f.write(sql)
            fname = f.name
        try:
            code = self.generator.generate_class(fname)
            self.assertIn('class', code)
            self.assertIn('def get_user', code)
            self.assertIn('def create_user', code)
            self.assertIn('user_id', code)
            self.assertIn('name', code)
            self.assertIn('email', code)
        finally:
            os.remove(fname)

    def test_generate_class_output_file(self):
        sql = """
#get_one
SELECT 1;
        """
        with tempfile.NamedTemporaryFile('w+', delete=False, suffix='.sql') as f:
            f.write(sql)
            sql_fname = f.name
        py_fd, py_fname = tempfile.mkstemp(suffix='.py')
        os.close(py_fd)
        try:
            code = self.generator.generate_class(sql_fname, output_file_path=py_fname)
            self.assertTrue(os.path.exists(py_fname))
            with open(py_fname, 'r') as f:
                content = f.read()
                self.assertIn('class', content)
                self.assertIn('def get_one', content)
        finally:
            os.remove(sql_fname)
            os.remove(py_fname)

    def test_generate_multiple_classes(self):
        sql1 = """
#get_a
SELECT 1;
        """
        sql2 = """
#get_b
SELECT 2;
        """
        with tempfile.NamedTemporaryFile('w+', delete=False, suffix='.sql') as f1, \
             tempfile.NamedTemporaryFile('w+', delete=False, suffix='.sql') as f2:
            f1.write(sql1)
            f2.write(sql2)
            fname1 = f1.name
            fname2 = f2.name
        try:
            result = self.generator.generate_multiple_classes([fname1, fname2])
            self.assertEqual(len(result), 2)
            self.assertIn('tmp', list(result.keys())[0])
        finally:
            os.remove(fname1)
            os.remove(fname2)

    def test_generate_class_invalid_file(self):
        with self.assertRaises(FileNotFoundError):
            self.generator.generate_class('nonexistent_file.sql')

    def test_method_signature_generation(self):
        # Test various parameter scenarios
        test_cases = [
            ([], ''),
            (['user_id'], 'user_id: Any'),
            (['user_id', 'status'], 'user_id: Any, status: Any'),
            (['user_id', 'user_id'], 'user_id: Any'),  # Duplicate parameters
            (['user_id_123', 'status'], 'user_id_123: Any, status: Any'),
        ]
        
        for params, expected in test_cases:
            signature = self.generator._generate_method_signature(params)
            self.assertEqual(signature, expected)

    def test_method_docstring_generation(self):
        # Test fetch statement docstring
        method_info = {
            'type': 'select',
            'is_fetch': True,
            'statement_type': 'fetch',
            'parameters': ['user_id'],
            'has_returning': False
        }
        docstring = self.generator._generate_method_docstring('get_user', method_info)
        self.assertIn('Select operation: get_user', docstring[1])
        self.assertIn('Statement type: fetch', docstring[2])
        self.assertIn('user_id', docstring[5])
        self.assertIn('List of result rows', docstring[8])

        # Test execute statement docstring
        method_info = {
            'type': 'insert',
            'is_fetch': False,
            'statement_type': 'execute',
            'parameters': ['name', 'email'],
            'has_returning': True
        }
        docstring = self.generator._generate_method_docstring('create_user', method_info)
        self.assertIn('Insert operation: create_user', docstring[1])
        self.assertIn('Statement type: execute', docstring[2])
        self.assertIn('name', docstring[5])
        self.assertIn('email', docstring[6])
        self.assertIn('SQLAlchemy Result object', docstring[9])

        # Test method with no parameters
        method_info = {
            'type': 'select',
            'is_fetch': True,
            'statement_type': 'fetch',
            'parameters': [],
            'has_returning': False
        }
        docstring = self.generator._generate_method_docstring('get_all', method_info)
        self.assertIn('Select operation: get_all', docstring[1])
        self.assertNotIn('Args:', docstring)

    def test_method_body_generation(self):
        # Test fetch statement body
        method_info = {
            'type': 'select',
            'is_fetch': True,
            'parameters': ['user_id'],
            'has_returning': False
        }
        body = self.generator._generate_method_body('SELECT * FROM users WHERE id = :user_id', method_info)
        self.assertTrue(any('sql = """' in line for line in body))
        self.assertTrue(any('params = {' in line for line in body))
        self.assertTrue(any('"user_id": user_id,' in line for line in body))
        self.assertTrue(any('result = self.connection.execute(text(sql), params)' in line for line in body))
        self.assertTrue(any('return result.fetchall()' in line for line in body))

        # Test execute statement body
        method_info = {
            'type': 'insert',
            'is_fetch': False,
            'parameters': [],
            'has_returning': False
        }
        body = self.generator._generate_method_body('INSERT INTO users DEFAULT VALUES', method_info)
        self.assertTrue(any('result = self.connection.execute(text(sql))' in line for line in body))
        self.assertTrue(any('return result' in line for line in body))

    def test_complex_sql_generation(self):
        # Test CTE with multiple parameters
        sql = """
#get_user_stats
WITH user_orders AS (
    SELECT user_id, COUNT(*) as order_count
    FROM orders
    GROUP BY user_id
)
SELECT u.name, uo.order_count
FROM users u
LEFT JOIN user_orders uo ON u.id = uo.user_id
WHERE u.id = :user_id AND u.status = :status
        """
        with tempfile.NamedTemporaryFile('w+', delete=False, suffix='.sql') as f:
            f.write(sql)
            fname = f.name
        try:
            code = self.generator.generate_class(fname)
            self.assertIn('def get_user_stats', code)
            self.assertIn('user_id: Any, status: Any', code)
            self.assertIn('"user_id": user_id', code)
            self.assertIn('"status": status', code)
            self.assertIn('WITH user_orders AS', code)
        finally:
            os.remove(fname)

    def test_generated_code_syntax_validation(self):
        # Test that generated code is valid Python syntax
        sql = """
#get_user
SELECT * FROM users WHERE id = :user_id;
#create_user
INSERT INTO users (name, email) VALUES (:name, :email);
        """
        with tempfile.NamedTemporaryFile('w+', delete=False, suffix='.sql') as f:
            f.write(sql)
            fname = f.name
        try:
            code = self.generator.generate_class(fname)
            # Try to parse the generated code as Python
            ast.parse(code)
        finally:
            os.remove(fname)

    def test_generate_class_with_various_statement_types(self):
        sql = """
#get_users
SELECT * FROM users;

#create_user
INSERT INTO users (name) VALUES (:name);

#update_user
UPDATE users SET status = :status WHERE id = :user_id;

#delete_user
DELETE FROM users WHERE id = :user_id;

#show_tables
SHOW TABLES;

#describe_table
DESCRIBE users;

#with_cte
WITH cte AS (SELECT 1) SELECT * FROM cte;
        """
        with tempfile.NamedTemporaryFile('w+', delete=False, suffix='.sql') as f:
            f.write(sql)
            fname = f.name
        try:
            code = self.generator.generate_class(fname)
            # Check that all methods are generated
            self.assertIn('def get_users', code)
            self.assertIn('def create_user', code)
            self.assertIn('def update_user', code)
            self.assertIn('def delete_user', code)
            self.assertIn('def show_tables', code)
            self.assertIn('def describe_table', code)
            self.assertIn('def with_cte', code)
            
            # Check return types
            self.assertIn('-> List[Row]', code)  # Fetch statements
            self.assertIn('-> Result', code)     # Execute statements
            
            # Validate syntax
            ast.parse(code)
        finally:
            os.remove(fname)

    def test_generate_multiple_classes_with_output_dir(self):
        sql1 = """
#get_a
SELECT 1;
        """
        sql2 = """
#get_b
SELECT 2;
        """
        with tempfile.NamedTemporaryFile('w+', delete=False, suffix='.sql') as f1, \
             tempfile.NamedTemporaryFile('w+', delete=False, suffix='.sql') as f2:
            f1.write(sql1)
            f2.write(sql2)
            fname1 = f1.name
            fname2 = f2.name
        
        output_dir = tempfile.mkdtemp()
        try:
            result = self.generator.generate_multiple_classes([fname1, fname2], output_dir)
            self.assertEqual(len(result), 2)
            
            # Check that files were created
            files = os.listdir(output_dir)
            self.assertEqual(len(files), 2)
            self.assertTrue(all(f.endswith('.py') for f in files))
        finally:
            os.remove(fname1)
            os.remove(fname2)
            for file in os.listdir(output_dir):
                os.remove(os.path.join(output_dir, file))
            os.rmdir(output_dir)

if __name__ == '__main__':
    unittest.main() 