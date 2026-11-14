"""Short database transactions for idempotent AI-backed mutations.

The provider call happens between reserve and complete. A lease token fences
late workers; a database CAS controls each session across processes.
"""

import hashlib
import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Callable

from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..config import settings
from ..models import Operation, TrainingResult, TrainingSession, Turn


class OperationError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 409, operation_id: str | None = None):
        super().__init__(message)
        self.code = code
        self.status_code = status_code
        self.operation_id = operation_id


@dataclass(frozen=True)
class Reservation:
    operation_id: str
    lease_token: str | None
    snapshot: dict
    response: dict | None = None

    @property
    def replayed(self) -> bool:
        return self.response is not None


def payload_sha256(payload: dict) -> str:
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _now() -> datetime:
    # SQLAlchemy's SQLite DateTime round trip is naive; values remain UTC.
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _lease_deadline(now: datetime) -> datetime:
    return now + timedelta(seconds=settings.OPERATION_LEASE_SECONDS)


def _find(db: Session, tenant_id: str, user_id: str, kind: str, key: str) -> Operation | None:
    return db.query(Operation).filter(
        Operation.tenant_id == tenant_id,
        Operation.user_id == user_id,
        Operation.kind == kind,
        Operation.idempotency_key == key,
    ).first()


def _existing_state(operation: Operation, digest: str, now: datetime) -> Reservation | None:
    if operation.payload_sha256 != digest:
        raise OperationError("IDEMPOTENCY_CONFLICT", "Idempotency-Key đã dùng với dữ liệu khác", operation_id=operation.id)
    if operation.status == "succeeded":
        return Reservation(operation.id, None, operation.snapshot_json or {}, operation.response_json)
    if operation.status == "pending" and operation.lease_until and operation.lease_until > now:
        raise OperationError("OPERATION_IN_PROGRESS", "Thao tác đang xử lý", operation_id=operation.id)
    return None


def reserve_start(
    db: Session, tenant_id: str, user_id: str, key: str, digest: str,
    snapshot: dict | Callable[[], dict],
) -> Reservation:
    now = _now()
    existing = _find(db, tenant_id, user_id, "start", key)
    if existing:
        replay = _existing_state(existing, digest, now)
        if replay:
            return replay
        token = str(uuid.uuid4())
        condition = [Operation.id == existing.id, Operation.status == existing.status]
        if existing.lease_token is not None:
            condition.append(Operation.lease_token == existing.lease_token)
        changed = db.execute(
            update(Operation).where(*condition).values(
                status="pending", lease_token=token, lease_until=_lease_deadline(now),
                attempt=Operation.attempt + 1, error_code=None, updated_at=now,
            )
        ).rowcount
        if changed != 1:
            db.rollback()
            raise OperationError("OPERATION_IN_PROGRESS", "Thao tác vừa được xử lý bởi worker khác", operation_id=existing.id)
        db.commit()
        return Reservation(existing.id, token, existing.snapshot_json or {})

    if callable(snapshot):
        snapshot = snapshot()
    operation = Operation(
        tenant_id=tenant_id, user_id=user_id, kind="start", idempotency_key=key,
        payload_sha256=digest, snapshot_json=snapshot, status="pending",
        lease_token=str(uuid.uuid4()), lease_until=_lease_deadline(now),
    )
    try:
        db.add(operation)
        db.commit()
        return Reservation(operation.id, operation.lease_token, snapshot)
    except IntegrityError:
        db.rollback()
        return reserve_start(db, tenant_id, user_id, key, digest, snapshot)


def _clear_stale_busy(db: Session, session: TrainingSession, now: datetime) -> None:
    if not session.busy_operation_id:
        return
    busy = db.query(Operation).filter(Operation.id == session.busy_operation_id).first()
    if not busy or busy.status != "pending" or not busy.lease_until or busy.lease_until > now:
        raise OperationError("SESSION_BUSY", "Phiên học đang có thao tác xử lý", operation_id=session.busy_operation_id)
    changed = db.execute(
        update(Operation).where(
            Operation.id == busy.id, Operation.status == "pending", Operation.lease_token == busy.lease_token,
        ).values(status="failed", error_code="LEASE_EXPIRED", updated_at=now)
    ).rowcount
    if changed != 1:
        db.rollback()
        raise OperationError("SESSION_BUSY", "Phiên học vừa được worker khác xử lý", operation_id=busy.id)
    released = db.execute(
        update(TrainingSession).where(
            TrainingSession.id == session.id,
            TrainingSession.busy_operation_id == busy.id,
            TrainingSession.revision == session.revision,
        ).values(busy_operation_id=None, state="active", revision=TrainingSession.revision + 1)
    ).rowcount
    if released != 1:
        db.rollback()
        raise OperationError("SESSION_BUSY", "Trạng thái phiên vừa thay đổi", operation_id=busy.id)
    db.commit()
    db.refresh(session)


def reserve_session(
    db: Session, session: TrainingSession, kind: str, key: str, digest: str, snapshot: dict,
) -> Reservation:
    if kind not in {"turn", "evaluate"}:
        raise ValueError("Unsupported session operation")
    now = _now()
    existing = _find(db, session.tenant_id, session.user_id, kind, key)
    if existing:
        replay = _existing_state(existing, digest, now)
        if replay:
            return replay
        if existing.session_id != session.id:
            raise OperationError("IDEMPOTENCY_CONFLICT", "Idempotency-Key thuộc phiên khác", operation_id=existing.id)
    db.refresh(session)
    if session.busy_operation_id and (not existing or session.busy_operation_id != existing.id):
        _clear_stale_busy(db, session, now)
    if session.state != "active" and not (kind == "evaluate" and existing and session.busy_operation_id == existing.id):
        raise OperationError("SESSION_COMPLETED", "Phiên học không còn nhận thao tác mới")
    if existing and existing.snapshot_json:
        if existing.snapshot_json.get("turns_count") != len(session.turns):
            raise OperationError("STALE_OPERATION", "Transcript đã thay đổi; hãy tải lại phiên", operation_id=existing.id)
        snapshot = existing.snapshot_json
    else:
        if snapshot.get("revision") != session.revision or snapshot.get("turns_count") != len(session.turns):
            raise OperationError("STALE_SESSION", "Phiên vừa thay đổi; hãy tải lại trước khi gửi")
    if kind == "turn" and len(session.turns) >= 4:
        raise OperationError("TURN_LIMIT", "Phiên đã đủ 4 lượt đối thoại")
    if kind == "evaluate" and not session.turns:
        raise OperationError("EMPTY_TRANSCRIPT", "Cần ít nhất một lượt trước khi đánh giá", 400)

    token = str(uuid.uuid4())
    if existing:
        condition = [Operation.id == existing.id, Operation.status == existing.status]
        if existing.lease_token is not None:
            condition.append(Operation.lease_token == existing.lease_token)
        claimed = db.execute(
            update(Operation).where(*condition).values(
                status="pending", lease_token=token, lease_until=_lease_deadline(now),
                attempt=Operation.attempt + 1, error_code=None, updated_at=now,
                request_revision=session.revision + 1,
            )
        ).rowcount
        operation_id = existing.id
    else:
        operation = Operation(
            tenant_id=session.tenant_id, user_id=session.user_id, session_id=session.id,
            kind=kind, idempotency_key=key, payload_sha256=digest, snapshot_json=snapshot,
            status="pending", lease_token=token, lease_until=_lease_deadline(now),
            request_revision=session.revision + 1,
        )
        try:
            db.add(operation)
            db.flush()
            operation_id = operation.id
            claimed = 1
        except IntegrityError:
            db.rollback()
            return reserve_session(db, session, kind, key, digest, snapshot)
    if claimed != 1:
        db.rollback()
        raise OperationError("OPERATION_IN_PROGRESS", "Thao tác vừa được worker khác nhận", operation_id=operation_id)
    expected_busy = existing.id if existing and session.busy_operation_id == existing.id else None
    reserved = db.execute(
        update(TrainingSession).where(
            TrainingSession.id == session.id,
            TrainingSession.revision == session.revision,
            TrainingSession.busy_operation_id == expected_busy,
            TrainingSession.state == ("evaluating" if expected_busy and kind == "evaluate" else "active"),
        ).values(
            busy_operation_id=operation_id,
            state="evaluating" if kind == "evaluate" else "active",
            revision=TrainingSession.revision + 1,
        )
    ).rowcount
    if reserved != 1:
        db.rollback()
        raise OperationError("SESSION_BUSY", "Trạng thái phiên vừa thay đổi", operation_id=operation_id)
    db.commit()
    return Reservation(operation_id, token, snapshot)


def _claim_completion(db: Session, operation_id: str, token: str, response: dict) -> Operation:
    operation = db.query(Operation).filter(Operation.id == operation_id).first()
    if not operation:
        raise OperationError("OPERATION_NOT_FOUND", "Không tìm thấy thao tác", 404)
    changed = db.execute(
        update(Operation).where(
            Operation.id == operation_id, Operation.status == "pending", Operation.lease_token == token,
        ).values(status="succeeded", response_json=response, updated_at=_now())
    ).rowcount
    if changed != 1:
        db.rollback()
        raise OperationError("STALE_OPERATION", "Worker cũ không được ghi kết quả", operation_id=operation_id)
    return operation


def complete_start(db: Session, reservation: Reservation, session: TrainingSession, response: dict) -> None:
    operation = _claim_completion(db, reservation.operation_id, reservation.lease_token, response)
    db.add(session)
    try:
        db.flush()
        operation.session_id = session.id
        db.commit()
    except IntegrityError:
        db.rollback()
        raise OperationError("START_CONFLICT", "Không thể lưu phiên học", operation_id=reservation.operation_id)


def complete_turn(
    db: Session, reservation: Reservation, session_id: str,
    employee_text: str, customer_text: str, response: dict,
) -> None:
    operation = _claim_completion(db, reservation.operation_id, reservation.lease_token, response)
    changed = db.execute(
        update(TrainingSession).where(
            TrainingSession.id == session_id,
            TrainingSession.state == "active",
            TrainingSession.busy_operation_id == operation.id,
            TrainingSession.revision == operation.request_revision,
        ).values(busy_operation_id=None, revision=TrainingSession.revision + 1)
    ).rowcount
    if changed != 1:
        db.rollback()
        raise OperationError("STALE_OPERATION", "Phiên học đã thay đổi", operation_id=operation.id)
    turn = Turn(
        session_id=session_id, turn_no=reservation.snapshot["turns_count"] + 1,
        operation_id=operation.id, employee_text=employee_text, customer_text=customer_text,
    )
    db.add(turn)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise OperationError("TURN_CONFLICT", "Lượt đối thoại đã được ghi bởi thao tác khác", operation_id=operation.id)


def complete_evaluate(
    db: Session, reservation: Reservation, session_id: str,
    result: TrainingResult, response: dict,
) -> None:
    operation = _claim_completion(db, reservation.operation_id, reservation.lease_token, response)
    changed = db.execute(
        update(TrainingSession).where(
            TrainingSession.id == session_id,
            TrainingSession.state == "evaluating",
            TrainingSession.busy_operation_id == operation.id,
            TrainingSession.revision == operation.request_revision,
        ).values(
            busy_operation_id=None, state="evaluated", completed=True,
            revision=TrainingSession.revision + 1,
        )
    ).rowcount
    if changed != 1:
        db.rollback()
        raise OperationError("STALE_OPERATION", "Phiên học đã thay đổi", operation_id=operation.id)
    result.operation_id = operation.id
    db.add(result)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise OperationError("RESULT_CONFLICT", "Kết quả phiên đã được lưu", operation_id=operation.id)


def fail(db: Session, reservation: Reservation, error_code: str) -> None:
    if not reservation.lease_token:
        return
    operation = db.query(Operation).filter(Operation.id == reservation.operation_id).first()
    if not operation:
        return
    changed = db.execute(
        update(Operation).where(
            Operation.id == operation.id, Operation.status == "pending",
            Operation.lease_token == reservation.lease_token,
        ).values(status="failed", error_code=error_code, updated_at=_now())
    ).rowcount
    if changed != 1:
        db.rollback()
        return
    if operation.session_id:
        db.execute(
            update(TrainingSession).where(
                TrainingSession.id == operation.session_id,
                TrainingSession.busy_operation_id == operation.id,
                TrainingSession.revision == operation.request_revision,
            ).values(
                busy_operation_id=None, state="active", revision=TrainingSession.revision + 1,
            )
        )
    db.commit()
