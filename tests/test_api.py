from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_sample_diff_endpoint_returns_diff_text():
    response = client.get("/sample-diff")
    assert response.status_code == 200
    assert "diff --git" in response.json()["diff"]


def test_review_sample_endpoint_returns_findings():
    response = client.get("/review/sample")
    assert response.status_code == 200
    body = response.json()
    assert body["summary"]["total_findings"] > 0
    assert len(body["findings"]) == body["summary"]["total_findings"]


def test_review_endpoint_with_custom_diff():
    diff_text = (
        "diff --git a/x.py b/x.py\n"
        "index 111..222 100644\n"
        "--- a/x.py\n"
        "+++ b/x.py\n"
        "@@ -1,1 +1,2 @@\n"
        " def x():\n"
        "+    print('hi')\n"
    )
    response = client.post("/review", json={"diff": diff_text})
    assert response.status_code == 200
    body = response.json()
    assert any("print()" in f["message"] for f in body["findings"])
