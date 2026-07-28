from app.diff_parser import parse_diff
from app.review import review_diff
from pathlib import Path

SAMPLE_DIFF_PATH = Path(__file__).resolve().parent.parent / "samples" / "sample.diff"


def _sample_result():
    diff_text = SAMPLE_DIFF_PATH.read_text()
    return review_diff(diff_text)


def test_detects_bare_except():
    result = _sample_result()
    messages = [f.message for f in result.findings]
    assert any("Bare `except:`" in m for m in messages)


def test_detects_mutable_default_argument():
    result = _sample_result()
    categories = [(f.category, f.message) for f in result.findings]
    assert any("Mutable default argument" in m for _, m in categories)


def test_detects_print_statement():
    result = _sample_result()
    assert any("print()" in f.message for f in result.findings)


def test_detects_todo_comment():
    result = _sample_result()
    assert any("TODO/FIXME" in f.message for f in result.findings)


def test_detects_hardcoded_secret():
    result = _sample_result()
    assert any(f.category == "security" and "credential" in f.message for f in result.findings)


def test_detects_sql_string_formatting():
    result = _sample_result()
    assert any("SQL injection" in f.message for f in result.findings)


def test_flags_missing_tests():
    result = _sample_result()
    assert any(f.category == "missing-tests" for f in result.findings)


def test_summary_counts_match_findings():
    result = _sample_result()
    assert result.summary["total_findings"] == len(result.findings)
    assert sum(result.summary["by_severity"].values()) == len(result.findings)


def test_diff_with_accompanying_test_file_does_not_flag_missing_tests():
    diff_text = (
        "diff --git a/app/util.py b/app/util.py\n"
        "index 111..222 100644\n"
        "--- a/app/util.py\n"
        "+++ b/app/util.py\n"
        "@@ -1,1 +1,2 @@\n"
        " def util():\n"
        "+    return True\n"
        "diff --git a/tests/test_util.py b/tests/test_util.py\n"
        "index 111..222 100644\n"
        "--- a/tests/test_util.py\n"
        "+++ b/tests/test_util.py\n"
        "@@ -1,1 +1,2 @@\n"
        " def test_util():\n"
        "+    assert True\n"
    )
    result = review_diff(diff_text)
    assert not any(f.category == "missing-tests" for f in result.findings)
