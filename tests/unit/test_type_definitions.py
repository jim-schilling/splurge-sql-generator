from splurge_sql_generator import type_definitions


def test_typed_dicts_exist():
    # Ensure the TypedDict classes are importable and have __annotations__
    assert hasattr(type_definitions, "ColumnInfo")
    assert hasattr(type_definitions, "MethodInfo")
    assert hasattr(type_definitions, "TableDefinition")

    assert isinstance(type_definitions.ColumnInfo.__annotations__, dict)
    assert isinstance(type_definitions.MethodInfo.__annotations__, dict)
    assert isinstance(type_definitions.TableDefinition.__annotations__, dict)
