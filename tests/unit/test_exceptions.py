from splurge_sql_generator import exceptions


def test_exceptions_inheritance_and_attributes():
    base = exceptions.SplurgeSqlGeneratorError("oops", details="more")
    assert isinstance(base, Exception)
    assert base.message == "oops"
    assert base.details == "more"

    fe = exceptions.FileError("file", details=None)
    assert isinstance(fe, exceptions.SplurgeSqlGeneratorError)

    se = exceptions.SqlValidationError("sql")
    assert isinstance(se, exceptions.ParsingError) is False
