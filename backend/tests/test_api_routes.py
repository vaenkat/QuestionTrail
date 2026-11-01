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


def test_ingest_text_source_and_analyze_dynamically():
    # 1. Create project
    create_resp = client.post(
        "/api/projects",
        json={
            "objective": "Assess global quantum computing security risks",
            "categories": [
                {
                    "id": "cat-post-quantum",
                    "name": "Post-Quantum Cryptography",
                    "description": "Migration timelines and cryptographic vulnerabilities.",
                    "evaluation_question": "What algorithms are deprecated by NIST?",
                    "enabled": True,
                }
            ],
        },
    )
    assert create_resp.status_code == 200
    proj_id = create_resp.json()["id"]

    # 2. Ingest raw text source
    ingest_resp = client.post(
        f"/api/projects/{proj_id}/sources/text",
        json={
            "title": "NIST Post-Quantum Cryptography Standards 2026",
            "content": "NIST finalized ML-KEM and ML-DSA standards. Legacy RSA-2048 is flagged as vulnerable to quantum cryptanalysis.",
            "publication_date": "2026-08-15",
            "url": "https://csrc.nist.gov/pqc",
        },
    )
    assert ingest_resp.status_code == 200
    data = ingest_resp.json()
    assert len(data["sources"]) == 1
    assert data["sources"][0]["title"] == "NIST Post-Quantum Cryptography Standards 2026"

    # 3. Analyze dynamically (not curated scholarship!)
    analyze_resp = client.post(f"/api/projects/{proj_id}/analyze")
    assert analyze_resp.status_code == 200
    res = analyze_resp.json()
    assert res["mode"] in ("live", "mock", "precomputed")
    result = res["result"]
    assert result["project_id"] == proj_id
    assert len(result["claims"]) >= 1
    # Check that the claim links to our custom NIST source
    assert result["claims"][0]["evidence_refs"][0]["source_id"] == data["sources"][0]["id"]


def test_ingest_pdf_source_endpoint():
    # 1. Create project
    create_resp = client.post(
        "/api/projects",
        json={
            "objective": "Analyze corporate governance reports",
            "categories": [],
        },
    )
    proj_id = create_resp.json()["id"]

    # 2. Upload invalid PDF format -> 400
    fail_upload = client.post(
        f"/api/projects/{proj_id}/sources/pdf",
        files={"file": ("test.pdf", b"NOT_A_VALID_PDF_FILE", "application/pdf")},
    )
    assert fail_upload.status_code == 400
    assert "standard PDF header" in fail_upload.json()["detail"]


def test_ingest_url_ssrf_rejection():
    # 1. Create project
    create_resp = client.post(
        "/api/projects",
        json={"objective": "Security evaluation", "categories": []},
    )
    proj_id = create_resp.json()["id"]

    # 2. Ingest localhost URL -> 400 Bad Request
    ssrf_resp = client.post(
        f"/api/projects/{proj_id}/sources/url",
        json={"url": "http://127.0.0.1:8080/admin"},
    )
    assert ssrf_resp.status_code == 400
    assert "forbidden" in ssrf_resp.json()["detail"].lower()
