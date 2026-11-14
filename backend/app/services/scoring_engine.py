import re
from typing import List, Dict, Tuple
from ..schemas import RubricItem, JudgmentDraft, EvaluationEvidence

PROMPT_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior)\s+instructions",
    r"bỏ\s+qua\s+(mọi|tất\s+cả)?\s*(quy\s+tắc|hướng\s+dẫn|chỉ\s+dẫn)",
    r"system\s*prompt",
    r"passed\s*[:=]\s*true",
    r"chấm\s+(tôi|em)\s+100\s*điểm",
    r"cho\s+(tôi|em)\s+đạt\s+hết",
    r"override\s+rubric",
]

def contains_prompt_injection(text: str) -> bool:
    """Phát hiện nỗ lực tấn công Prompt Injection từ nội dung nhập vào (BR-14, AT-16)."""
    if not text:
        return False
    lowered = text.lower()
    return any(re.search(pattern, lowered) for pattern in PROMPT_INJECTION_PATTERNS)

def normalize_text(text: str) -> str:
    """Loại bỏ ký tự đặc biệt, chuẩn hóa khoảng trắng và chuyển chữ thường để đối soát dẫn chứng."""
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r'[\r\n\t]+', ' ', text)
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def verify_quote_in_transcript(quote: str, employee_transcript: List[str]) -> bool:
    """
    Kiểm tra xem exact_quote do AI trích dẫn có thực sự xuất hiện trong phát ngôn của nhân viên không.
    Ngăn chặn tuyệt đối tình trạng LLM bịa đặt bằng chứng (Hallucinated Evidence) hoặc dùng câu Prompt Injection.
    """
    if not quote or not quote.strip():
        return False
        
    if contains_prompt_injection(quote):
        return False
        
    normalized_quote = normalize_text(quote)
    if len(normalized_quote) < 3:
        return False
        
    # Chỉ chấp nhận các lượt thoại không chứa mã độc Prompt Injection
    clean_turns = [
        normalize_text(t) for t in employee_transcript 
        if t and not contains_prompt_injection(t)
    ]
    combined_employee_text = " ".join(clean_turns)
    return normalized_quote in combined_employee_text

def compute_deterministic_result(
    rubric: List[RubricItem],
    judgments: List[JudgmentDraft],
    employee_transcript: List[str]
) -> Tuple[int, bool, bool, List[EvaluationEvidence]]:
    """
    Tính điểm xác định 100% dựa trên Rubric và đối soát bằng chứng phát ngôn:
    - Unknown criteria ID bị loại bỏ (BR-06, G5).
    - Quote sai, thiếu hoặc bịa -> passed=False, weight=0 (BR-08, AT-08).
    - Critical criteria bị fail -> passed=False toàn bài thi bất kể tổng điểm (BR-09, AT-09).
    """
    rubric_map: Dict[str, RubricItem] = {item.id: item for item in rubric}
    evidence_list: List[EvaluationEvidence] = []
    
    total_score = 0
    has_critical_failure = False
    
    # Chỉ giữ lại các judgment có criterion_id nằm trong rubric đã phê duyệt
    judgment_map = {
        j.criterion_id: j for j in judgments 
        if j.criterion_id in rubric_map
    }
    
    for crit_id, crit_def in rubric_map.items():
        judgment = judgment_map.get(crit_id)
        
        if not judgment:
            # AI bỏ sót tiêu chí -> Mặc định 0 điểm
            evidence_list.append(
                EvaluationEvidence(
                    criterion_id=crit_id,
                    label=crit_def.label,
                    weight=crit_def.weight,
                    critical=crit_def.critical,
                    passed=False,
                    exact_quote="",
                    explanation="Không có dữ liệu đánh giá cho tiêu chí này.",
                    quote_verified=False
                )
            )
            if crit_def.critical:
                has_critical_failure = True
            continue
            
        quote_verified = False
        passed = False
        explanation = judgment.explanation or ""
        
        if judgment.passed:
            # Phải kiểm chứng quote có thật trong transcript của nhân viên hay không
            if judgment.exact_quote and verify_quote_in_transcript(judgment.exact_quote, employee_transcript):
                quote_verified = True
                passed = True
                total_score += crit_def.weight
            else:
                # Quote bịa đặt hoặc thiếu quote chứng minh -> Bác bỏ điểm đạt
                quote_verified = False
                passed = False
                explanation = (explanation + " [BÁC BỎ: Bằng chứng trích dẫn không có thật hoặc không hợp lệ trong phát ngôn của nhân viên]").strip()
        else:
            passed = False
            quote_verified = verify_quote_in_transcript(judgment.exact_quote, employee_transcript) if judgment.exact_quote else False

        if crit_def.critical and not passed:
            has_critical_failure = True

        evidence_list.append(
            EvaluationEvidence(
                criterion_id=crit_id,
                label=crit_def.label,
                weight=crit_def.weight,
                critical=crit_def.critical,
                passed=passed,
                exact_quote=judgment.exact_quote or "",
                explanation=explanation,
                quote_verified=quote_verified
            )
        )
        
    overall_passed = (total_score >= 70) and not has_critical_failure
    
    return total_score, overall_passed, has_critical_failure, evidence_list
