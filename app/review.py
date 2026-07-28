"""Orchestrates the review: parse a diff, run every rule, summarize results."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from app.diff_parser import parse_diff
from app.rules import PER_FILE_RULES, Finding, rule_missing_tests


@dataclass
class ReviewResult:
    findings: list[Finding]
    summary: dict


def review_diff(diff_text: str) -> ReviewResult:
    files = parse_diff(diff_text)

    findings: list[Finding] = []
    for file_diff in files:
        for rule in PER_FILE_RULES:
            findings.extend(rule(file_diff))

    findings.extend(rule_missing_tests(files))

    # Stable ordering: by file, then by line (findings with no line go last).
    findings.sort(key=lambda f: (f.file, f.line if f.line is not None else float("inf")))

    by_severity: dict[str, int] = {}
    by_category: dict[str, int] = {}
    for f in findings:
        by_severity[f.severity] = by_severity.get(f.severity, 0) + 1
        by_category[f.category] = by_category.get(f.category, 0) + 1

    summary = {
        "files_reviewed": len(files),
        "total_findings": len(findings),
        "by_severity": by_severity,
        "by_category": by_category,
    }

    return ReviewResult(findings=findings, summary=summary)


def review_result_to_dict(result: ReviewResult) -> dict:
    return {
        "summary": result.summary,
        "findings": [asdict(f) for f in result.findings],
    }
