export interface UserInfo {
  id: string;
  username: string;
  email: string;
  full_name?: string;
  role: 'manager' | 'employee';
  tenant_id: string;
  tenant_name: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: UserInfo;
}

export interface StepItem {
  id: string;
  instruction: string;
}

export interface RubricItem {
  id: string;
  label: string;
  weight: number;
  critical: boolean;
}

export interface SOPVersionDetail {
  id: string;
  sop_id: string;
  version_no: number;
  status: string;
  steps: StepItem[];
  rubric: RubricItem[];
  approved_by?: string;
  approved_at?: string;
  created_at: string;
}

export interface SOPDetailResponse {
  id: string;
  tenant_id: string;
  title: string;
  active_version?: SOPVersionDetail;
  versions: SOPVersionDetail[];
}

export interface ModuleDraft {
  title: string;
  learning_objective: string;
  situation: string;
  opening_message: string;
  criteria: string[];
  next_practice_hint: string;
}

export interface TrainingSessionResponse {
  session_id: string;
  tenant_id: string;
  sop_version_id: string;
  sop_title: string;
  module: ModuleDraft;
  completed: boolean;
  turns_count: number;
  ai_mode: string;
}

export interface TrainingTurnResponse {
  session_id: string;
  turn_no: number;
  employee_text: string;
  customer_text: string;
  remaining_turns: number;
  completed: boolean;
  ai_mode: string;
}

export interface EvaluationEvidence {
  criterion_id: string;
  label: string;
  weight: number;
  critical: boolean;
  passed: boolean;
  exact_quote: string;
  explanation: string;
  quote_verified: boolean;
}

export interface FinalResultResponse {
  session_id: string;
  sop_version_id: string;
  score: number;
  passed: boolean;
  critical_failure: boolean;
  evidence: EvaluationEvidence[];
  coaching_tip: string;
  ai_mode: string;
  disclaimer: string;
}

export interface HealthResponse {
  status: string;
  ai_mode: string;
  live_ready: boolean;
  version: string;
}
