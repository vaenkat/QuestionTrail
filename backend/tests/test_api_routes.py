"""Integration tests for FastAPI endpoints."""

from fastapi.testclient import TestClient
from questiontrail.main import app

client = TestClient(app)


def test_propose_categories_success():
    response = client.post(
        "/api/categories/propose",
        json={"objective": "Investigate Reliance Foundation Scholarship criteria"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["objective"] == "Investigate Reliance Foundation Scholarship criteria"
    assert len(data["categories"]) >= 3
    for cat in data["categories"]:
        assert cat["id"].startswith("cat-")
        assert len(cat["name"]) > 0
        assert len(cat["evaluation_question"]) > 0


def test_propose_categories_validation_error():
    response = client.post(
        "/api/categories/propose",
        json={"objective": "  "},
    )
    assert response.status_code == 422  # pydantic min_length validation


def test_project_lifecycle_end_to_end():
    # 1. Propose categories
    cat_resp = client.post(
        "/api/categories/propose",
        json={"objective": "Reliance Foundation Scholarship 2026-27"},
    )
    categories = cat_resp.json()["categories"]

    # 2. Create project
    create_resp = client.post(
        "/api/projects",
        json={
            "objective": "Reliance Foundation Scholarship 2026-27",
            "categories": categories,
        },
    )
    assert create_resp.status_code == 200
    project = create_resp.json()
    project_id = project["id"]
    assert project_id.startswith("proj-")

    # 3. Get project details (before loading sources)
    detail_resp = client.get(f"/api/projects/{project_id}")
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert detail["project"]["id"] == project_id
    assert len(detail["sources"]) == 0
    assert detail["has_analysis"] is False

    # 4. Attempt to analyze without sources -> 400 Bad Request
    fail_analyze = client.post(f"/api/projects/{project_id}/analyze")
    assert fail_analyze.status_code == 400
    assert "zero sources" in fail_analyze.json()["detail"]

    # 5. Load curated demo dataset
    demo_resp = client.post(f"/api/projects/{project_id}/load-demo")
    assert demo_resp.status_code == 200
    demo_data = demo_resp.json()
    assert len(demo_data["sources"]) == 5

    # 6. Run analysis
    analyze_resp = client.post(f"/api/projects/{project_id}/analyze")
    assert analyze_resp.status_code == 200
    analysis = analyze_resp.json()
    assert "result" in analysis
    assert "mode" in analysis
    assert analysis["mode"] == "precomputed"
    result = analysis["result"]
    assert len(result["claims"]) >= 7
    assert len(result["findings"]) >= 3
    assert len(result["actions"]) >= 3

    # 7. Generate report
    report_resp = client.get(f"/api/projects/{project_id}/report")
    assert report_resp.status_code == 200
    report = report_resp.json()
    assert report["project_id"] == project_id
    assert report["total_claims"] == len(result["claims"])
    assert report["total_findings"] == len(result["findings"])
    assert report["total_actions"] == len(result["actions"])
    assert "# Research Verification Report" in report["markdown_report"]
    assert "Verification Checklist" in report["markdown_report"]


def test_get_nonexistent_project_returns_404():
    response = client.get("/api/projects/proj-nonexistent-999")
    assert response.status_code == 404
