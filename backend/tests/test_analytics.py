from datetime import datetime, timedelta, timezone

from app.database import SessionLocal
from app.models import TrainingResult, TrainingSession


def test_analytics_aggregates_beyond_recent_page(client, auth_headers_manager_a):
    now = datetime.now(timezone.utc)
    with SessionLocal() as db:
        for index in range(51):
            session = TrainingSession(
                tenant_id="tenant-cafe-a",
                user_id="user-emp-a",
                sop_version_id="version-sop-a-v1",
                module_json={},
                completed=index == 0,
                created_at=now + timedelta(seconds=index),
            )
            db.add(session)
            db.flush()
            if index == 0:
                db.add(TrainingResult(
                    session_id=session.id,
                    score=100,
                    passed=True,
                    critical_failure=False,
                    payload_json={"evidence": []},
                ))
        db.commit()

    response = client.get("/v1/admin/analytics", headers=auth_headers_manager_a)
    assert response.status_code == 200
    body = response.json()
    assert body["total_sessions"] == 51
    assert body["completed_sessions"] == 1
    assert body["pass_rate"] == 100.0
    assert body["average_score"] == 100.0
    assert len(body["recent_sessions"]) == 50
