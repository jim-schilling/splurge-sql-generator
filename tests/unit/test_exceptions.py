from splurge_sql_generator import exceptions


def test_exceptions_inheritance_and_attributes():
    base = exceptions.SplurgeSqlGeneratorError("oops", details={"error": "more"})
    assert isinstance(base, Exception)
    assert base.message == "oops"
    assert base.details == {"error": "more"}

    fe = exceptions.FileError("file", details={"type": "file"})
    assert isinstance(fe, exceptions.SplurgeSqlGeneratorError)

    se = exceptions.SplurgeSqlGeneratorSqlValidationError("sql")
    assert isinstance(se, exceptions.SplurgeSqlGeneratorError)
