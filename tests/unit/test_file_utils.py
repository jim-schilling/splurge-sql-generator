import pytest
import yaml

from splurge_sql_generator.exceptions import SplurgeSqlGeneratorConfigurationError
from splurge_sql_generator.file_utils import SafeTextFileIoAdapter, YamlConfigReader


def test_yaml_config_reader_reads_dict(tmp_path):
    data = {"a": 1, "b": "two"}
    p = tmp_path / "conf.yaml"
    p.write_text(yaml.safe_dump(data), encoding="utf-8")

    reader = YamlConfigReader()
    out = reader.read(p)
    assert out == data


def test_yaml_config_reader_invalid_yaml(tmp_path):
    p = tmp_path / "bad.yaml"
    # This content doesn't raise a parser error but produces a dict-like structure
    content = "::notyaml::"
    p.write_text(content, encoding="utf-8")
    reader = YamlConfigReader()
    # Reader should return whatever YAML produced (a dict in this case)
    expected = yaml.safe_load(content)
    assert reader.read(p) == expected


def test_yaml_config_reader_syntax_error_raises(tmp_path):
    p = tmp_path / "really_bad.yaml"
    # Intentionally broken YAML that should raise YAMLError
    p.write_text(":\n -", encoding="utf-8")
    reader = YamlConfigReader()
    with pytest.raises(SplurgeSqlGeneratorConfigurationError):
        reader.read(p)


def test_safe_text_file_io_adapter_write_read(tmp_path):
    adapter = SafeTextFileIoAdapter()
    p = tmp_path / "sample.txt"
    adapter.write_text(p, "hello world")
    assert adapter.exists(p)
    content = adapter.read_text(p)
    assert content == "hello world"
