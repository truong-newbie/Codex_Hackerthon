def test_manager_creates_sop_draft_and_approval_publishes_it(
    client, auth_headers_manager_a, auth_headers_emp_a, auth_headers_emp_b,
):
    payload = {
        "title": "Xử lý phản hồi về thời gian chờ",
        "steps": [{"id": "S1", "instruction": "Xin lỗi và xác minh đơn hàng."}],
        "rubric": [{"id": "C1", "label": "Xác minh đơn hàng", "weight": 100, "critical": True}],
    }
    denied = client.post("/v1/admin/sops", headers=auth_headers_emp_a, json=payload)
    assert denied.status_code == 403

    created = client.post("/v1/admin/sops", headers=auth_headers_manager_a, json=payload)
    assert created.status_code == 201
    sop = created.json()
    assert sop["tenant_id"] == "tenant-cafe-a"
    assert sop["active_version"] is None
    assert sop["versions"][0]["status"] == "draft"
    sop_id = sop["id"]
    version_id = sop["versions"][0]["id"]

    employee_before = client.get("/v1/sops", headers=auth_headers_emp_a).json()
    assert all(item["id"] != sop_id for item in employee_before)
    tenant_b = client.get("/v1/sops", headers=auth_headers_emp_b).json()
    assert all(item["id"] != sop_id for item in tenant_b)

    approved = client.post(
        f"/v1/admin/sop-versions/{version_id}/approve", headers=auth_headers_manager_a
    )
    assert approved.status_code == 200
    employee_after = client.get("/v1/sops", headers=auth_headers_emp_a).json()
    published = next(item for item in employee_after if item["id"] == sop_id)
    assert published["active_version"]["id"] == version_id
