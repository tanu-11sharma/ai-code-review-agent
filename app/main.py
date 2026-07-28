"""FastAPI app exposing the code review agent over HTTP."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel

from app.review import review_diff, review_result_to_dict

app = FastAPI(
    title="AI Code Review Agent",
    description=(
        "Rule-based agent that reviews a unified diff and comments on style issues, "
        "likely bugs, security smells, and missing test coverage."
    ),
    version="0.1.0",
)

SAMPLE_DIFF_PATH = Path(__file__).resolve().parent.parent / "samples" / "sample.diff"


class ReviewRequest(BaseModel):
    diff: str


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/sample-diff")
def sample_diff() -> dict:
    return {"diff": SAMPLE_DIFF_PATH.read_text()}


@app.post("/review")
def review(request: ReviewRequest) -> dict:
    result = review_diff(request.diff)
    return review_result_to_dict(result)


@app.get("/review/sample")
def review_sample() -> dict:
    """Convenience endpoint: reviews the bundled sample diff directly."""
    diff_text = SAMPLE_DIFF_PATH.read_text()
    result = review_diff(diff_text)
    return review_result_to_dict(result)
