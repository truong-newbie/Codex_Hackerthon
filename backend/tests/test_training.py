def test_cross_tenant_training_denied(client, auth_headers_emp_a):
    # Employee Café A cannot train on Café B's SOP
    res = client.post(
        "/v1/training/start",
        headers=auth_headers_emp_a,
        json={"sop_id": "sop-complaint-b"}
    )
    assert res.status_code == 404

def test_training_flow_e2e(client, auth_headers_emp_a):
    # 1. Start training session
    start_res = client.post(
        "/v1/training/start",
        headers=auth_headers_emp_a,
        json={"sop_id": "sop-complaint-a"}
    )
    assert start_res.status_code == 200
    session_data = start_res.json()
    session_id = session_data["session_id"]
    assert "situation" in session_data["module"]
    assert "opening_message" in session_data["module"]

    # 2. Send 1st turn
    turn_res = client.post(
        f"/v1/training/{session_id}/turn",
        headers=auth_headers_emp_a,
        json={"message": "Dạ em chào anh, em rất xin lỗi vì sự bất tiện của ly cà phê này ạ. Em kiểm tra lại ngay cho anh."}
    )
    assert turn_res.status_code == 200
    turn_data = turn_res.json()
    assert turn_data["turn_no"] == 1
    assert len(turn_data["customer_text"]) > 0

    # 3. Evaluate session
    eval_res = client.post(
        f"/v1/training/{session_id}/evaluate",
        headers=auth_headers_emp_a
    )
    assert eval_res.status_code == 200
    eval_data = eval_res.json()
    assert "score" in eval_data
    assert "passed" in eval_data
    assert "evidence" in eval_data
    assert len(eval_data["evidence"]) >= 1

    # 4. Idempotency check: evaluating again returns same result
    eval_res_2 = client.post(
        f"/v1/training/{session_id}/evaluate",
        headers=auth_headers_emp_a
    )
    assert eval_res_2.status_code == 200
    assert eval_res_2.json()["score"] == eval_data["score"]
