from app.diff_parser import parse_diff

SAMPLE = """diff --git a/foo.py b/foo.py
index 111..222 100644
--- a/foo.py
+++ b/foo.py
@@ -1,3 +1,5 @@
 def foo():
-    return 1
+    return 2
+
+print("done")
"""


def test_parse_diff_extracts_file_and_added_lines():
    files = parse_diff(SAMPLE)
    assert len(files) == 1
    assert files[0].path == "foo.py"

    added_texts = [l.text for l in files[0].added_lines]
    assert "    return 2" in added_texts
    assert 'print("done")' in added_texts


def test_parse_diff_line_numbers_follow_hunk_header():
    files = parse_diff(SAMPLE)
    added = {l.text: l.line_no for l in files[0].added_lines}
    assert added["    return 2"] == 2
    assert added['print("done")'] == 4
