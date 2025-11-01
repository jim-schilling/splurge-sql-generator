from hypothesis import given
from hypothesis import strategies as st

from splurge_sql_generator import utils


@given(st.text(alphabet=st.characters(blacklist_categories=("Cc", "Cs")), min_size=1, max_size=40))
def test_to_snake_case_outputs_lowercase(s):
    # Ensure output is lowercase and contains no uppercase letters
    out = utils.to_snake_case(s)
    assert out == out.lower()
    # Note: Some Unicode characters may not have a lowercase form, so we just verify
    # that the output is consistent with calling lower()
    assert out.isupper() is False or out == out.lower()


@given(st.one_of(st.none(), st.text()))
def test_normalize_string_and_is_empty_or_whitespace_roundtrip(val):
    normalized = utils.normalize_string(val)
    # normalize_string always returns a str
    assert isinstance(normalized, str)

    # is_empty_or_whitespace should agree with normalized == ""
    assert utils.is_empty_or_whitespace(val) == (normalized == "")


def test_format_error_context():
    assert utils.format_error_context(None) == ""
    assert utils.format_error_context("/path/to/file") == " in /path/to/file"
