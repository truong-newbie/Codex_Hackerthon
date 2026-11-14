from app.schemas import RubricItem, JudgmentDraft
from app.services.scoring_engine import (
    verify_quote_in_transcript,
    compute_deterministic_result
)

def test_verify_quote_in_transcript():
    transcript = [
        "Dạ em chào anh ạ, em rất xin lỗi anh vì sự cố này",
        "Em sẽ báo quản lý hỗ trợ anh ngay lập tức"
    ]
    # Exact quote present
    assert verify_quote_in_transcript("rất xin lỗi anh", transcript) is True
    # Quote with minor whitespace / punctuation differences
    assert verify_quote_in_transcript("rất xin lỗi anh!", transcript) is True
    # Fabricated quote not in transcript
    assert verify_quote_in_transcript("Em xin phép hoàn tiền 100% cho anh", transcript) is False

def test_quote_cannot_cross_employee_turn_boundary():
    transcript = ["Em xin lỗi anh", "xin phép báo quản lý"]
    assert verify_quote_in_transcript("anh xin phép", transcript) is False

def test_hallucinated_quote_scoring_zero():
    rubric = [
        RubricItem(id="C1", label="Xin lỗi", weight=30, critical=False),
        RubricItem(id="C2", label="Đổi món", weight=70, critical=True)
    ]
    judgments = [
        JudgmentDraft(criterion_id="C1", passed=True, exact_quote="xin lỗi anh", explanation="Có xin lỗi"),
        # AI falsely claimed employee said this:
        JudgmentDraft(criterion_id="C2", passed=True, exact_quote="Em đổi món ngay cho anh nhé", explanation="Bịa đặt quote")
    ]
    transcript = ["Dạ em xin lỗi anh nhiều ạ!"]

    score, passed, critical_failure, evidence = compute_deterministic_result(rubric, judgments, transcript)
    
    # C1 passed (30 pts), C2 rejected because quote is hallucinated (0 pts)
    assert score == 30
    assert passed is False
    assert critical_failure is True  # C2 is critical and failed
    assert evidence[1].quote_verified is False
