import re
from typing import List, Dict, Any, Tuple
from ..schemas import RubricItem, JudgmentDraft, EvaluationEvidence

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
    Ngăn chặn tuyệt đối tình trạng LLM bịa đặt bằng chứng (Hallucinated Evidence).
    """
    if not quote or not quote.strip():
        return False
        
    normalized_quote = normalize_text(quote)
    if len(normalized_quote) < 3:
        return False
        
    combined_employee_text = " ".join([normalize_text(t) for t in employee_transcript])
    return normalized_quote in combined_employee_text

def compute_deterministic_result(
    rubric: List[RubricItem],
    judgments: List[JudgmentDraft],
    employee_transcript: List[str]
) -> Tuple[int, bool, bool, List[EvaluationEvidence]]:
    """
    Tính điểm xác định 100% dựa trên Rubric và đối soát bằng chứng phát ngôn:
    - Quote sai hoặc bịa -> passed=False, weight=0.
    - Critical criteria bị fail -> passed=False toàn bài thi (bất kể tổng điểm).
    """
    rubric_map: Dict[str, RubricItem] = {item.id: item for item in rubric}
    evidence_list: List[EvaluationEvidence] = []
    
    total_score = 0
    has_critical_failure = False
    
    judgment_map = {j.criterion_id: j for j in judgments}
    
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
        
        if judgment.passed:
            # Phải kiểm chứng quote có thật trong transcript của nhân viên hay không
            if judgment.exact_quote and verify_quote_in_transcript(judgment.exact_quote, employee_transcript):
                quote_verified = True
                passed = True
                total_score += crit_def.weight
            else:
                # Quote bịa đặt hoặc thiếu quote chứng minh
                quote_verified = False
                passed = False
                explanation_extra = " [CẢNH BÁO: Bằng chứng trích dẫn không có thật trong phát ngôn của nhân viên]"
                judgment.explanation = (judgment.explanation or "") + explanation_extra
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
                explanation=judgment.explanation or "",
                quote_verified=quote_verified
            )
        )
        
    overall_passed = (total_score >= 70) and not has_critical_failure
    
    return total_score, overall_passed, has_critical_failure, evidence_list
