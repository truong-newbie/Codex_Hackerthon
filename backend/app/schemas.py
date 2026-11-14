from pydantic import BaseModel, Field
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
    id: str
    instruction: str

class RubricItem(BaseModel):
    id: str
    label: str
    weight: int = Field(..., ge=0, le=100)
    critical: bool = False

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
    steps: List[StepItem]
    rubric: List[RubricItem]

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
    sop_version_id: str
    sop_title: str
    module: ModuleDraft
    completed: bool
    turns_count: int
    ai_mode: str

class TrainingTurnRequest(BaseModel):
    message: str = Field(..., min_length=2, max_length=1000)

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
    score: int
    passed: bool
    critical_failure: bool
    evidence: List[EvaluationEvidence]
    coaching_tip: str
    ai_mode: str
    disclaimer: str = "Kết quả mô phỏng dùng cho mục đích đào tạo và rèn luyện kỹ năng, không thay thế cho quyết định đánh giá nhân sự chính thức."
