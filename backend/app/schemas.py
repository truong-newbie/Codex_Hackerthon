from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import datetime

# --- Auth Schemas ---
class LoginRequest(BaseModel):
    username_or_email: str
    password: str

class TenantInfo(BaseModel):
    id: str
    name: str

class UserInfo(BaseModel):
    id: str
    username: str
    email: str
    full_name: Optional[str] = None
    role: str
    tenant_id: str
    tenant_name: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserInfo

# --- SOP & Rubric Schemas ---
class StepItem(BaseModel):
    id: str = Field(..., min_length=1)
    instruction: str = Field(..., min_length=1)

    @field_validator("id", "instruction")
    @classmethod
    def must_not_be_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Trường này không được để trống")
        return v.strip()

class RubricItem(BaseModel):
    id: str = Field(..., min_length=1)
    label: str = Field(..., min_length=1)
    weight: int = Field(..., ge=1, le=100)
    critical: bool = False

    @field_validator("id", "label")
    @classmethod
    def must_not_be_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Trường này không được để trống")
        return v.strip()

class SOPVersionDetail(BaseModel):
    id: str
    sop_id: str
    version_no: int
    status: str
    steps: List[StepItem]
    rubric: List[RubricItem]
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    created_at: datetime

class SOPDetailResponse(BaseModel):
    id: str
    tenant_id: str
    title: str
    active_version: Optional[SOPVersionDetail] = None
    versions: List[SOPVersionDetail] = []

class CreateDraftRequest(BaseModel):
    steps: List[StepItem] = Field(..., min_length=1)
    rubric: List[RubricItem] = Field(..., min_length=1)

class ApproveResponse(BaseModel):
    message: str
    active_version_id: str
    version_no: int

# --- AI & Training Schemas ---
class ModuleDraft(BaseModel):
    title: str
    learning_objective: str
    situation: str
    opening_message: str
    criteria: List[str]  # Must be subset of Rubric IDs
    next_practice_hint: str

class TrainingStartRequest(BaseModel):
    sop_id: str

class TrainingSessionResponse(BaseModel):
    session_id: str
    tenant_id: str
    sop_id: Optional[str] = None
    sop_version_id: str
    sop_version_no: int = 1
    sop_title: str
    module: ModuleDraft
    completed: bool
    turns_count: int
    ai_mode: str
    latency_ms: Optional[int] = None

class TrainingTurnRequest(BaseModel):
    message: str = Field(..., min_length=2, max_length=1000)

    @field_validator("message")
    @classmethod
    def message_not_blank(cls, v: str) -> str:
        if not v or len(v.strip()) < 2:
            raise ValueError("Tin nhắn phản hồi phải có ít nhất 2 ký tự")
        return v.strip()

class CustomerOutput(BaseModel):
    customer_message: str

class TurnDetail(BaseModel):
    turn_no: int
    employee_text: str
    customer_text: str
    created_at: datetime

class TrainingTurnResponse(BaseModel):
    session_id: str
    turn_no: int
    employee_text: str
    customer_text: str
    remaining_turns: int
    completed: bool
    ai_mode: str
    latency_ms: Optional[int] = None

class JudgmentDraft(BaseModel):
    criterion_id: str
    passed: bool
    exact_quote: str = ""
    explanation: str

class EvaluationDraft(BaseModel):
    judgments: List[JudgmentDraft]
    coaching_tip: str

class EvaluationEvidence(BaseModel):
    criterion_id: str
    label: str
    weight: int
    critical: bool
    passed: bool
    exact_quote: str
    explanation: str
    quote_verified: bool

class FinalResultResponse(BaseModel):
    session_id: str
    sop_version_id: str
    sop_version_no: Optional[int] = None
    score: int
    passed: bool
    critical_failure: bool
    evidence: List[EvaluationEvidence]
    coaching_tip: str
    ai_mode: str
    latency_ms: Optional[int] = None
    disclaimer: str = "Kết quả mô phỏng dùng cho mục đích đào tạo và rèn luyện kỹ năng, không thay thế cho quyết định đánh giá nhân sự chính thức."

class SessionSummaryItem(BaseModel):
    session_id: str
    sop_id: str
    sop_title: str
    sop_version_id: str
    sop_version_no: int
    completed: bool
    turns_count: int
    score: Optional[int] = None
    passed: Optional[bool] = None
    critical_failure: Optional[bool] = None
    ai_mode: str
    created_at: datetime

class TrainingSessionDetailResponse(BaseModel):
    session_id: str
    tenant_id: str
    sop_id: str
    sop_title: str
    sop_version_id: str
    sop_version_no: int
    module: ModuleDraft
    completed: bool
    turns: List[TurnDetail]
    result: Optional[FinalResultResponse] = None
    ai_mode: str
    created_at: datetime

# --- Manager Analytics Schemas ---
class ManagerSessionRecord(BaseModel):
    session_id: str
    employee_id: str
    employee_username: str
    employee_name: str
    sop_id: str
    sop_title: str
    sop_version_id: str
    sop_version_no: int
    completed: bool
    turns_count: int
    score: Optional[int] = None
    passed: Optional[bool] = None
    critical_failure: Optional[bool] = None
    evidence: List[EvaluationEvidence] = []
    coaching_tip: Optional[str] = None
    created_at: datetime

class TenantAnalyticsResponse(BaseModel):
    tenant_id: str
    tenant_name: str
    total_sessions: int
    completed_sessions: int
    pass_rate: float
    average_score: float
    critical_failure_count: int
    recent_sessions: List[ManagerSessionRecord] = []

