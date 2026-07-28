# AI Code Review Agent

A small, rule-based agent that reviews a unified diff and leaves the kind of
comments a human reviewer would: likely bugs, security smells, style nits,
and missing test coverage — each attributed to the exact file and line it
came from.

## What it does

Feed it a `git diff`-style unified diff and it:

1. **Parses** the diff with a small hand-rolled parser (no external diff
   library) to find exactly which lines were added, in which files, at which
   line numbers.
2. **Runs a set of independent rules** over the added lines: bare `except:`
   blocks, mutable default arguments, leftover `print()`/`TODO` markers,
   hardcoded credentials, SQL built with unsafe string formatting, overly
   long lines, and a "no test file touched" heuristic for diffs that change
   source but not tests.
3. **Returns structured findings** — file, line, severity (`high` / `medium`
   / `low`), category (`bug` / `security` / `style` / `missing-tests`), and a
   human-readable message — plus a summary count by severity and category.

This is a demo/reference implementation, not a replacement for a real
linter, static analyzer, or human reviewer — it's intentionally transparent
regex/heuristic rules rather than AST-based analysis or an LLM call, so every
comment it produces is traceable to the rule that raised it.

## Why this is relevant

Agentic code-review tooling — bots that comment on pull requests the way a
teammate would — is one of the most visible current applications of AI in
developer workflows. This project shows the core mechanics of that pattern
(diff parsing → rule evaluation → structured, cited findings) without
depending on a hosted LLM or a specific CI platform, so it's easy to read
end-to-end and to extend with new rules.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
uvicorn app.main:app --reload
```

Review the bundled sample diff (a synthetic payments-module change with
several planted issues) with a single call:

```bash
curl http://127.0.0.1:8000/review/sample
```

Or submit your own diff:

```bash
curl -X POST http://127.0.0.1:8000/review \
  -H "Content-Type: application/json" \
  -d "$(python3 -c 'import json,sys; print(json.dumps({"diff": open("samples/sample.diff").read()}))')"
```

Example finding from the sample diff:

```json
{
  "file": "payments/charge.py",
  "line": 15,
  "severity": "high",
  "category": "bug",
  "message": "Bare `except:` silently swallows all exceptions (including KeyboardInterrupt/SystemExit). Catch a specific exception type and log or re-raise it."
}
```

## Test

```bash
pytest -v
```

## Project layout

```
app/
  diff_parser.py   # Hand-rolled unified-diff parser
  rules.py         # Independent rule functions -> Finding objects
  review.py        # Orchestrates rules + builds the summary
  main.py          # FastAPI app: /health, /sample-diff, /review, /review/sample
samples/
  sample.diff      # Synthetic diff with planted issues for the demo
tests/
  test_diff_parser.py
  test_rules.py
  test_api.py
```

## Notes / disclaimers

- `samples/sample.diff` is entirely synthetic demo code (a fictional
  payments module) written to exercise the rules — it is not real production
  code, and the "API key" in it is an obvious placeholder string, not a real
  credential.
- This agent only reads diff text you give it; it never touches a real
  repository, CI system, or live external service.
- This is a demo/reference implementation, not a production code-review
  system.
