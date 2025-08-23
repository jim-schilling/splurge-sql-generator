import os
import tempfile
import unittest
from splurge_sql_generator import generate_class, generate_multiple_classes

class TestInitAPI(unittest.TestCase):
    def setUp(self):
        self.sql_content = """# TestClass\n# test_method\nSELECT 1;"""
        self.temp_sql = tempfile.NamedTemporaryFile("w+", delete=False, suffix=".sql")
        self.temp_sql.write(self.sql_content)
        self.temp_sql.close()
        self.sql_file = self.temp_sql.name

    def tearDown(self):
        os.remove(self.sql_file)
        if hasattr(self, 'output_file') and os.path.exists(self.output_file):
            os.remove(self.output_file)
        if hasattr(self, 'output_dir') and os.path.exists(self.output_dir):
            for f in os.listdir(self.output_dir):
                os.remove(os.path.join(self.output_dir, f))
            os.rmdir(self.output_dir)

    def test_generate_class(self):
        code = generate_class(self.sql_file)
        self.assertIn('class TestClass', code)
        # Test output file
        self.output_file = self.sql_file + '.py'
        code2 = generate_class(self.sql_file, output_file_path=self.output_file)
        self.assertTrue(os.path.exists(self.output_file))
        with open(self.output_file) as f:
            self.assertIn('class TestClass', f.read())

    def test_generate_multiple_classes(self):
        self.output_dir = self.sql_file + '_outdir'
        os.mkdir(self.output_dir)
        result = generate_multiple_classes([self.sql_file], output_dir=self.output_dir)
        self.assertIn('TestClass', result)
        out_file = os.path.join(self.output_dir, 'test_class.py')
        self.assertTrue(os.path.exists(out_file))
        with open(out_file) as f:
            self.assertIn('class TestClass', f.read())

if __name__ == '__main__':
    unittest.main() 