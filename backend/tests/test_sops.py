def test_list_sops_cafe_a(client, auth_headers_emp_a):
    res = client.get("/v1/sops", headers=auth_headers_emp_a)
    assert res.status_code == 200
    sops = res.json()
    assert len(sops) >= 1
    assert "nghiêm ngặt" in sops[0]["title"]
    assert sops[0]["tenant_id"] == "tenant-cafe-a"

def test_employee_cannot_create_draft(client, auth_headers_emp_a):
    # Employee cannot create draft (403 forbidden)
    res = client.post(
        "/v1/admin/sops/sop-complaint-a/draft",
        headers=auth_headers_emp_a,
        json={
            "steps": [{"id": "S1", "instruction": "Test"}],
            "rubric": [{"id": "C1", "label": "Test", "weight": 100, "critical": False}]
        }
    )
    assert res.status_code == 403

def test_manager_create_draft_and_approve(client, auth_headers_manager_a):
    # 1. Manager creates draft
    draft_res = client.post(
        "/v1/admin/sops/sop-complaint-a/draft",
        headers=auth_headers_manager_a,
        json={
            "steps": [
                {"id": "S1", "instruction": "Bước 1 mới"},
                {"id": "S2", "instruction": "Bước 2 mới"}
            ],
            "rubric": [
                {"id": "C1", "label": "Tiêu chí 1", "weight": 50, "critical": False},
                {"id": "C2", "label": "Tiêu chí 2", "weight": 50, "critical": True}
            ]
        }
    )
    assert draft_res.status_code == 200
    draft_data = draft_res.json()
    assert draft_data["status"] == "draft"
    version_id = draft_data["id"]

    # 2. Manager approves draft
    appr_res = client.post(
        f"/v1/admin/sop-versions/{version_id}/approve",
        headers=auth_headers_manager_a
    )
    assert appr_res.status_code == 200
    assert appr_res.json()["active_version_id"] == version_id
