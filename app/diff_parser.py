"""A small, hand-rolled unified-diff parser.

We only need enough of the unified diff format to know, per file: which lines
were added (with their line numbers in the new file) and which files changed
overall. That's enough to drive rule-based review comments without pulling in
a heavyweight diff library.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

FILE_HEADER_RE = re.compile(r"^\+\+\+ b/(.+)$")
HUNK_HEADER_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")


@dataclass
class AddedLine:
    line_no: int
    text: str


@dataclass
class FileDiff:
    path: str
    added_lines: list[AddedLine] = field(default_factory=list)

    @property
    def added_text(self) -> str:
        return "\n".join(l.text for l in self.added_lines)


def parse_diff(diff_text: str) -> list[FileDiff]:
    """Parse a unified diff (as produced by `git diff`) into FileDiff objects."""
    files: list[FileDiff] = []
    current: FileDiff | None = None
    new_line_no = 0

    for raw_line in diff_text.splitlines():
        file_match = FILE_HEADER_RE.match(raw_line)
        if file_match:
            current = FileDiff(path=file_match.group(1))
            files.append(current)
            continue

        hunk_match = HUNK_HEADER_RE.match(raw_line)
        if hunk_match:
            new_line_no = int(hunk_match.group(1))
            continue

        if current is None:
            continue

        if raw_line.startswith("+++") or raw_line.startswith("---"):
            continue

        if raw_line.startswith("+"):
            current.added_lines.append(AddedLine(line_no=new_line_no, text=raw_line[1:]))
            new_line_no += 1
        elif raw_line.startswith("-"):
            # Removed line: doesn't consume a new-file line number.
            continue
        else:
            # Context line (or the leading " " unified-diff marker).
            new_line_no += 1

    return files
