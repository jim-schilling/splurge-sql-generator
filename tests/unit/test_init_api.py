import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, NamedTuple

import pytest

from splurge_sql_generator import generate_class, generate_multiple_classes
from tests.unit.test_utils import create_sql_with_schema


class _InitAPIData(NamedTuple):
    """Container for test data and resources."""

    sql_file: Any
    schema_file: Any


@pytest.fixture
def init_api_data(sql_content, temp_dir):
    (sql_file, schema_file) = create_sql_with_schema(Path(temp_dir), "test.sql", sql_content)
    yield _InitAPIData(str(sql_file), str(schema_file))


@pytest.fixture
def temp_dir():
    _temp_dir_value = tempfile.mkdtemp()
    yield _temp_dir_value
    # Clean up the entire temp directory
    shutil.rmtree(_temp_dir_value, ignore_errors=True)


@pytest.fixture
def sql_content():
    return """# TestClass\n# test_method\nSELECT 1;"""


@pytest.fixture
def sql_file(init_api_data):
    return init_api_data.sql_file


@pytest.fixture
def schema_file(init_api_data):
    return init_api_data.schema_file


def test_generate_class(temp_dir, sql_content, sql_file, schema_file):
    code = generate_class(sql_file, schema_file_path=schema_file)
    assert "class TestClass" in code
    # Test output file
    output_file = sql_file + ".py"
    generate_class(sql_file, output_file_path=output_file, schema_file_path=schema_file)
    assert os.path.exists(output_file)
    with open(output_file) as f:
        assert "class TestClass" in f.read()


def test_generate_multiple_classes(temp_dir, sql_content, sql_file, schema_file):
    output_dir = sql_file + "_outdir"
    os.mkdir(output_dir)
    result = generate_multiple_classes([sql_file], output_dir=output_dir, schema_file_path=schema_file)
    assert "TestClass" in result
    out_file = os.path.join(output_dir, "test_class.py")
    assert os.path.exists(out_file)
    with open(out_file) as f:
        assert "class TestClass" in f.read()
