"""Rule-based static checks applied to the added lines of a diff.

Each rule is a small function: (FileDiff) -> list[Finding]. This is not a
real linter (no AST analysis) — it's a transparent, regex/heuristic-based
"reviewer" that mirrors the kinds of things a human reviewer flags in a PR:
obvious bugs, risky patterns, style nits, and missing test coverage. Keeping
each rule tiny and independent makes it easy to see exactly why a comment was
raised and to add new rules later.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.diff_parser import FileDiff

SEVERITY_HIGH = "high"
SEVERITY_MEDIUM = "medium"
SEVERITY_LOW = "low"

CATEGORY_BUG = "bug"
CATEGORY_SECURITY = "security"
CATEGORY_STYLE = "style"
CATEGORY_TESTS = "missing-tests"


@dataclass
class Finding:
    file: str
    line: int | None
    severity: str
    category: str
    message: str


def rule_bare_except(file_diff: FileDiff) -> list[Finding]:
    findings = []
    for line in file_diff.added_lines:
        if re.match(r"^\s*except\s*:\s*$", line.text):
            findings.append(
                Finding(
                    file=file_diff.path,
                    line=line.line_no,
                    severity=SEVERITY_HIGH,
                    category=CATEGORY_BUG,
                    message="Bare `except:` silently swallows all exceptions (including "
                    "KeyboardInterrupt/SystemExit). Catch a specific exception type and "
                    "log or re-raise it.",
                )
            )
    return findings


def rule_mutable_default_argument(file_diff: FileDiff) -> list[Finding]:
    findings = []
    pattern = re.compile(r"def\s+\w+\([^)]*=\s*(\[\]|\{\})")
    for line in file_diff.added_lines:
        if pattern.search(line.text):
            findings.append(
                Finding(
                    file=file_diff.path,
                    line=line.line_no,
                    severity=SEVERITY_HIGH,
                    category=CATEGORY_BUG,
                    message="Mutable default argument (`[]`/`{}`). It's shared across calls "
                    "and will leak state between invocations. Use `None` and initialize "
                    "inside the function body instead.",
                )
            )
    return findings


def rule_print_statement(file_diff: FileDiff) -> list[Finding]:
    findings = []
    for line in file_diff.added_lines:
        if re.match(r"^\s*print\(", line.text):
            findings.append(
                Finding(
                    file=file_diff.path,
                    line=line.line_no,
                    severity=SEVERITY_LOW,
                    category=CATEGORY_STYLE,
                    message="`print()` left in application code. Use the `logging` module "
                    "so verbosity can be controlled and output goes to the right place "
                    "in production.",
                )
            )
    return findings


def rule_todo_fixme(file_diff: FileDiff) -> list[Finding]:
    findings = []
    for line in file_diff.added_lines:
        if re.search(r"#\s*(TODO|FIXME)", line.text, re.IGNORECASE):
            findings.append(
                Finding(
                    file=file_diff.path,
                    line=line.line_no,
                    severity=SEVERITY_LOW,
                    category=CATEGORY_STYLE,
                    message="TODO/FIXME comment introduced in this change. Consider filing "
                    "a tracked issue instead of leaving it inline, or resolving it before "
                    "merging.",
                )
            )
    return findings


def rule_hardcoded_secret(file_diff: FileDiff) -> list[Finding]:
    findings = []
    pattern = re.compile(
        r"(API_KEY|SECRET|PASSWORD|TOKEN)\s*=\s*[\"'][^\"']{8,}[\"']", re.IGNORECASE
    )
    for line in file_diff.added_lines:
        if pattern.search(line.text):
            findings.append(
                Finding(
                    file=file_diff.path,
                    line=line.line_no,
                    severity=SEVERITY_HIGH,
                    category=CATEGORY_SECURITY,
                    message="Possible hardcoded credential/secret. Load this from an "
                    "environment variable or secrets manager instead of committing it to "
                    "source control.",
                )
            )
    return findings


def rule_string_formatted_sql(file_diff: FileDiff) -> list[Finding]:
    findings = []
    pattern = re.compile(r"(SELECT|UPDATE|DELETE|INSERT)\b.*%s", re.IGNORECASE)
    for line in file_diff.added_lines:
        if pattern.search(line.text) and "%" in line.text:
            findings.append(
                Finding(
                    file=file_diff.path,
                    line=line.line_no,
                    severity=SEVERITY_HIGH,
                    category=CATEGORY_SECURITY,
                    message="SQL string built with `%` string formatting is vulnerable to "
                    "SQL injection. Use parameterized queries (e.g. `cursor.execute(query, "
                    "(param,))`) instead.",
                )
            )
    return findings


def rule_line_too_long(file_diff: FileDiff, max_length: int = 100) -> list[Finding]:
    findings = []
    for line in file_diff.added_lines:
        if len(line.text) > max_length:
            findings.append(
                Finding(
                    file=file_diff.path,
                    line=line.line_no,
                    severity=SEVERITY_LOW,
                    category=CATEGORY_STYLE,
                    message=f"Line is {len(line.text)} characters, over the {max_length}-"
                    "character guideline. Consider breaking it up for readability.",
                )
            )
    return findings


PER_FILE_RULES = [
    rule_bare_except,
    rule_mutable_default_argument,
    rule_print_statement,
    rule_todo_fixme,
    rule_hardcoded_secret,
    rule_string_formatted_sql,
    rule_line_too_long,
]


def rule_missing_tests(all_files: list[FileDiff]) -> list[Finding]:
    """Flags a diff that changes source files but no test files.

    This is a coarse heuristic (path contains "test"), same as a human
    skimming the file list in a PR — not a coverage tool.
    """
    source_files = [f for f in all_files if f.path.endswith(".py") and "test" not in f.path.lower()]
    test_files = [f for f in all_files if "test" in f.path.lower()]

    if source_files and not test_files:
        changed = ", ".join(f.path for f in source_files)
        return [
            Finding(
                file=changed,
                line=None,
                severity=SEVERITY_MEDIUM,
                category=CATEGORY_TESTS,
                message=f"This diff changes {changed} but doesn't add or modify any test "
                "file. Consider adding a test that covers the new behavior.",
            )
        ]
    return []
