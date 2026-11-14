from concurrent.futures import ThreadPoolExecutor
from threading import Event

from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import app
from app.database import SessionLocal
from app.models import TrainingResult, TrainingSession, Turn
from app.services.ai_service import ai_service


def test_start_turn_evaluate_replay_and_operation_owner(
    client, auth_headers_emp_a, auth_headers_emp_b,
):
    start_headers = {**auth_headers_emp_a, "Idempotency-Key": "start-replay-key"}
    start = client.post("/v1/training/start", headers=start_headers, json={"sop_id": "sop-complaint-a"})
    assert start.status_code == 200
    start_replay = client.post("/v1/training/start", headers=start_headers, json={"sop_id": "sop-complaint-a"})
    assert start_replay.status_code == 200
    assert start_replay.json() == start.json()
    session_id = start.json()["session_id"]
    assert start_replay.headers["X-Operation-ID"] == start.headers["X-Operation-ID"]

    conflict = client.post("/v1/training/start", headers=start_headers, json={"sop_id": "other-sop"})
    assert conflict.status_code == 409
    assert conflict.json()["code"] == "IDEMPOTENCY_CONFLICT"

    turn_headers = {**auth_headers_emp_a, "Idempotency-Key": "turn-replay-key"}
    body = {"message": "Dạ em xin lỗi anh, em kiểm tra hóa đơn và báo quản lý ngay ạ."}
    turn = client.post(f"/v1/training/{session_id}/turn", headers=turn_headers, json=body)
    assert turn.status_code == 200
    turn_replay = client.post(f"/v1/training/{session_id}/turn", headers=turn_headers, json=body)
    assert turn_replay.status_code == 200
    assert turn_replay.json() == turn.json()
    with SessionLocal() as db:
        assert db.query(Turn).filter(Turn.session_id == session_id).count() == 1

    eval_headers = {**auth_headers_emp_a, "Idempotency-Key": "eval-replay-key"}
    result = client.post(f"/v1/training/{session_id}/evaluate", headers=eval_headers)
    assert result.status_code == 200
    eval_replay = client.post(f"/v1/training/{session_id}/evaluate", headers=eval_headers)
    assert eval_replay.status_code == 200
    assert eval_replay.json() == result.json()
    with SessionLocal() as db:
        session = db.get(TrainingSession, session_id)
        assert session.state == "evaluated"
        assert session.completed is True

    operation_id = start.headers["X-Operation-ID"]
    own = client.get(f"/v1/operations/{operation_id}", headers=auth_headers_emp_a)
    assert own.status_code == 200
    assert own.json()["response"]["session_id"] == session_id
    other_tenant = client.get(f"/v1/operations/{operation_id}", headers=auth_headers_emp_b)
    assert other_tenant.status_code == 404


def test_failed_turn_can_retry_same_key(client, auth_headers_emp_a, monkeypatch):
    start = client.post("/v1/training/start", headers=auth_headers_emp_a, json={"sop_id": "sop-complaint-a"})
    session_id = start.json()["session_id"]
    headers = {**auth_headers_emp_a, "Idempotency-Key": "retry-turn-key"}
    body = {"message": "Dạ em xin lỗi và kiểm tra lại hóa đơn cho anh."}
    original = ai_service.simulate_customer

    def fail_once(**kwargs):
        raise HTTPException(status_code=502, detail="Temporary provider failure")

    monkeypatch.setattr(ai_service, "simulate_customer", fail_once)
    failed = client.post(f"/v1/training/{session_id}/turn", headers=headers, json=body)
    assert failed.status_code == 502
    monkeypatch.setattr(ai_service, "simulate_customer", original)
    retried = client.post(f"/v1/training/{session_id}/turn", headers=headers, json=body)
    assert retried.status_code == 200
    assert retried.json()["turn_no"] == 1


def test_concurrent_turns_use_database_reservation(client, auth_headers_emp_a, monkeypatch):
    start = client.post("/v1/training/start", headers=auth_headers_emp_a, json={"sop_id": "sop-complaint-a"})
    session_id = start.json()["session_id"]
    entered = Event()
    release = Event()
    original = ai_service.simulate_customer

    def paused_simulator(*args, **kwargs):
        entered.set()
        assert release.wait(10), "Simulator was not released"
        return original(*args, **kwargs)

    monkeypatch.setattr(ai_service, "simulate_customer", paused_simulator)
    first_headers = {**auth_headers_emp_a, "Idempotency-Key": "parallel-turn-one"}
    body = {"message": "Dạ em xin lỗi anh, em sẽ kiểm tra hóa đơn."}

    def first_request():
        with TestClient(app) as worker_client:
            return worker_client.post(f"/v1/training/{session_id}/turn", headers=first_headers, json=body)

    with ThreadPoolExecutor(max_workers=2) as workers:
        future = workers.submit(first_request)
        try:
            assert entered.wait(10), "First request did not reach simulator"
            same_key = client.post(f"/v1/training/{session_id}/turn", headers=first_headers, json=body)
            assert same_key.status_code == 409
            assert same_key.json()["code"] == "OPERATION_IN_PROGRESS"
            other_key = client.post(
                f"/v1/training/{session_id}/turn",
                headers={**auth_headers_emp_a, "Idempotency-Key": "parallel-turn-two"},
                json={"message": "Em sẽ hỏi quản lý ngay ạ."},
            )
            assert other_key.status_code == 409
            assert other_key.json()["code"] == "SESSION_BUSY"
        finally:
            release.set()
        assert future.result(timeout=10).status_code == 200
    with SessionLocal() as db:
        assert db.query(Turn).filter(Turn.session_id == session_id).count() == 1


def test_evaluate_freezes_transcript_against_new_turns(client, auth_headers_emp_a, monkeypatch):
    start = client.post("/v1/training/start", headers=auth_headers_emp_a, json={"sop_id": "sop-complaint-a"})
    session_id = start.json()["session_id"]
    first_turn = client.post(
        f"/v1/training/{session_id}/turn", headers=auth_headers_emp_a,
        json={"message": "Dạ em xin lỗi anh, em kiểm tra hóa đơn ngay ạ."},
    )
    assert first_turn.status_code == 200
    entered = Event()
    release = Event()
    original = ai_service.evaluate_session

    def paused_evaluator(*args, **kwargs):
        entered.set()
        assert release.wait(10), "Evaluator was not released"
        return original(*args, **kwargs)

    monkeypatch.setattr(ai_service, "evaluate_session", paused_evaluator)
    eval_headers = {**auth_headers_emp_a, "Idempotency-Key": "parallel-evaluate"}

    def first_evaluation():
        with TestClient(app) as worker_client:
            return worker_client.post(f"/v1/training/{session_id}/evaluate", headers=eval_headers)

    with ThreadPoolExecutor(max_workers=2) as workers:
        future = workers.submit(first_evaluation)
        try:
            assert entered.wait(10), "First evaluation did not reach evaluator"
            same_key = client.post(f"/v1/training/{session_id}/evaluate", headers=eval_headers)
            assert same_key.status_code == 409
            assert same_key.json()["code"] == "OPERATION_IN_PROGRESS"
            new_turn = client.post(
                f"/v1/training/{session_id}/turn",
                headers={**auth_headers_emp_a, "Idempotency-Key": "late-turn-key"},
                json={"message": "Em sẽ pha lại ly mới cho anh."},
            )
            assert new_turn.status_code == 409
            assert new_turn.json()["code"] == "SESSION_BUSY"
        finally:
            release.set()
        assert future.result(timeout=10).status_code == 200
    with SessionLocal() as db:
        assert db.query(TrainingResult).filter(TrainingResult.session_id == session_id).count() == 1
        assert db.query(Turn).filter(Turn.session_id == session_id).count() == 1
