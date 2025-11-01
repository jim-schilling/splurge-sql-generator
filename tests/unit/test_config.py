from splurge_sql_generator import config


def test_default_config_to_dict():
    d = config.DEFAULT_CONFIG.to_dict()
    assert d["default_encoding"] == "utf-8"
    assert d["sql_type_mapping_file"] == "types.yaml"
    assert d["validate_parameters"] is False
    assert d["strict_mode"] is False


def test_from_env_overrides(monkeypatch):
    monkeypatch.setenv("SPLURGE_DEFAULT_ENCODING", "latin-1")
    monkeypatch.setenv("SPLURGE_SQL_TYPE_MAPPING_FILE", "custom.yaml")
    monkeypatch.setenv("SPLURGE_VALIDATE_PARAMETERS", "true")
    monkeypatch.setenv("SPLURGE_STRICT_MODE", "true")

    cfg = config.GeneratorConfig.from_env()
    assert cfg.default_encoding == "latin-1"
    assert cfg.sql_type_mapping_file == "custom.yaml"
    assert cfg.validate_parameters is True
    assert cfg.strict_mode is True
