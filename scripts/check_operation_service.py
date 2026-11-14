"""Exercise operation replay and fencing using an isolated migrated SQLite DB."""

import sys
import tempfile
from datetime import timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend" / ".deps"))
sys.path.insert(0, str(ROOT / "backend"))

from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.config import settings  # noqa: E402
from app.models import Account, Membership, Operation, SOP, SOPVersion, Tenant, TrainingResult, TrainingSession, Turn  # noqa: E402
from app.services.operation_service import (  # noqa: E402
    OperationError, _now, complete_evaluate, complete_start, complete_turn,
    payload_sha256, reserve_session, reserve_start,
)
from check_alembic_migrations import upgrade  # noqa: E402


def check() -> None:
    with tempfile.TemporaryDirectory(prefix="shiftlens-operation-check-") as directory:
        database = Path(directory, "operations.db")
        upgrade(database)
        engine = create_engine(f"sqlite:///{database.as_posix()}")
        with Session(engine) as db:
            db.add_all([
                Tenant(id="tenant", name="Café"),
                Account(id="user", username="user", email="user@example.com", password_hash="test"),
            ])
            db.flush()
            db.add_all([
                Membership(user_id="user", tenant_id="tenant", role="employee"),
                SOP(id="sop", tenant_id="tenant", title="Complaint", active_version_id="version"),
            ])
            db.flush()
            db.add(SOPVersion(
                id="version", sop_id="sop", version_no=1, status="approved",
                steps_json=[], rubric_json=[],
            ))
            db.commit()

        start_payload = payload_sha256({"sop_id": "sop"})
        start_snapshot = {"sop_version_id": "version", "sop_title": "Complaint"}
        with Session(engine) as db:
            reserved = reserve_start(db, "tenant", "user", "start-key", start_payload, start_snapshot)
            assert not reserved.replayed
            session = TrainingSession(
                id="session", tenant_id="tenant", user_id="user",
                sop_version_id="version", module_json={},
            )
            complete_start(db, reserved, session, {"session_id": "session"})
            replay = reserve_start(db, "tenant", "user", "start-key", start_payload, start_snapshot)
            assert replay.response == {"session_id": "session"}
            try:
                reserve_start(db, "tenant", "user", "start-key", payload_sha256({"sop_id": "other"}), start_snapshot)
            except OperationError as error:
                assert error.code == "IDEMPOTENCY_CONFLICT"
            else:
                raise AssertionError("Different payload was accepted under the same key")

        turn_digest = payload_sha256({"session_id": "session", "message": "Xin lỗi anh"})
        with Session(engine) as db:
            session = db.get(TrainingSession, "session")
            old = reserve_session(db, session, "turn", "turn-key", turn_digest, {
                "revision": session.revision, "turns_count": 0,
            })
            other = db.get(TrainingSession, "session")
            try:
                reserve_session(db, other, "turn", "other-key", turn_digest, {
                    "revision": other.revision, "turns_count": 0,
                })
            except OperationError as error:
                assert error.code == "SESSION_BUSY"
            else:
                raise AssertionError("Concurrent turn reservation was accepted")
            operation = db.get(Operation, old.operation_id)
            operation.lease_until = _now() - timedelta(seconds=1)
            db.commit()
            replacement = reserve_session(db, session, "turn", "turn-key", turn_digest, {
                "revision": session.revision, "turns_count": 0,
            })
            assert replacement.lease_token != old.lease_token
            response = {"session_id": "session", "turn_no": 1}
            try:
                complete_turn(db, old, "session", "Xin lỗi anh", "Tôi nghe đây", response)
            except OperationError as error:
                assert error.code == "STALE_OPERATION"
            else:
                raise AssertionError("Stale worker committed a turn")
            complete_turn(db, replacement, "session", "Xin lỗi anh", "Tôi nghe đây", response)
            assert db.query(Turn).filter(Turn.session_id == "session").count() == 1
            replay = reserve_session(db, session, "turn", "turn-key", turn_digest, {})
            assert replay.response == response

        with Session(engine) as db:
            session = db.get(TrainingSession, "session")
            evaluation = reserve_session(db, session, "evaluate", "eval-key", payload_sha256({"session_id": "session"}), {
                "revision": session.revision, "turns_count": 1,
            })
            response = {"session_id": "session", "score": 100}
            result = TrainingResult(
                session_id="session", score=100, passed=True,
                critical_failure=False, payload_json=response,
            )
            complete_evaluate(db, evaluation, "session", result, response)
            assert db.get(TrainingSession, "session").state == "evaluated"
            assert db.query(TrainingResult).filter(TrainingResult.session_id == "session").count() == 1
            replay = reserve_session(db, session, "evaluate", "eval-key", payload_sha256({"session_id": "session"}), {})
            assert replay.response == response
        engine.dispose()
    print("Operation service checks passed")


if __name__ == "__main__":
    check()
