import json
import logging
from typing import List, Dict, Any
from fastapi import HTTPException, status
from ..config import settings
from ..schemas import (
    StepItem, RubricItem, ModuleDraft, CustomerOutput, 
    EvaluationDraft, JudgmentDraft
)

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        self.client = None
        if settings.GEMINI_API_KEY:
            try:
                from google import genai
                self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
            except Exception as e:
                logger.warning(f"Không thể khởi tạo Google GenAI Client: {e}")

    def is_live_ready(self) -> bool:
        return bool(settings.GEMINI_API_KEY and settings.AI_MODE == "live")

    def compile_module(self, sop_title: str, steps: List[StepItem], rubric: List[RubricItem]) -> ModuleDraft:
        """Module 1: Sinh bối cảnh tình huống và mục tiêu học tập từ SOP và Rubric."""
        if settings.AI_MODE == "live":
            if not settings.GEMINI_API_KEY:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Server đang cấu hình AI_MODE=live nhưng thiếu GEMINI_API_KEY."
                )
            try:
                from google.genai import types
                prompt = f"""
                Bạn là chuyên gia thiết kế đào tạo nhân sự F&B cho hệ thống ShiftLens.
                Hãy biên soạn một tình huống thực hành mô phỏng (ModuleDraft) dựa trên quy trình SOP và bộ tiêu chí sau:
                
                TIÊU ĐỀ SOP: {sop_title}
                CÁC BƯỚC QUY TRÌNH (STEPS):
                {json.dumps([s.model_dump() for s in steps], ensure_ascii=False, indent=2)}
                
                BỘ TIÊU CHÍ ĐÁNH GIÁ (RUBRIC):
                {json.dumps([r.model_dump() for r in rubric], ensure_ascii=False, indent=2)}
                
                YÊU CẦU:
                - Tạo bối cảnh tình huống (situation) thực tế tại quán cà phê liên quan đến SOP trên.
                - Câu mở đầu của khách hàng (opening_message) phải thể hiện sự không hài lòng hoặc yêu cầu cụ thể.
                - Mục tiêu học tập (learning_objective) ngắn gọn, rõ ràng.
                - Danh sách `criteria` CHỈ ĐƯỢC CHỨA các id tiêu chí có trong Rubric: {[r.id for r in rubric]}.
                """
                response = self.client.models.generate_content(
                    model=settings.GEMINI_MODEL,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=ModuleDraft,
                        temperature=0.3
                    )
                )
                return ModuleDraft.model_validate_json(response.text)
            except Exception as e:
                logger.error(f"Lỗi AI Compiler Live: {e}")
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Lỗi từ Google GenAI API: {str(e)}"
                )

        # STUB MODE
        return ModuleDraft(
            title=f"Mô phỏng: {sop_title}",
            learning_objective="Rèn luyện kỹ năng lắng nghe, xoa dịu khách hàng và xử lý đúng thẩm quyền theo quy định quán.",
            situation="Một khách hàng vừa nhận ly Cà phê Muối nhưng cảm thấy vị quá mặn, bọt sữa bị tách nước và đang tiến lại quầy với vẻ mặt bực bội.",
            opening_message="Em ơi, ly cà phê muối này mặn chát không uống nổi, kem sữa thì vữa hết rồi! Quán làm ăn kiểu gì thế này?",
            criteria=[r.id for r in rubric],
            next_practice_hint="Thử các tình huống khách hàng yêu cầu hoàn tiền ngay lập tức khi quán đang giờ cao điểm."
        )

    def simulate_customer(
        self,
        situation: str,
        opening_message: str,
        steps: List[StepItem],
        history: List[Dict[str, str]],
        employee_text: str
    ) -> CustomerOutput:
        """Module 2: Đóng vai khách hàng phản hồi theo từng lượt của nhân viên."""
        if settings.AI_MODE == "live":
            if not settings.GEMINI_API_KEY:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Server đang cấu hình AI_MODE=live nhưng thiếu GEMINI_API_KEY."
                )
            try:
                from google.genai import types
                prompt = f"""
                Bạn là một khách hàng đang khó chịu tại quán cà phê trong hệ thống đào tạo ShiftLens.
                
                BỐI CẢNH TÌNH HUỐNG: {situation}
                CÂU MỞ ĐẦU: {opening_message}
                
                LỊCH SỬ ĐỐI THOẠI TRƯỚC ĐÓ:
                {json.dumps(history, ensure_ascii=False, indent=2)}
                
                CÂU NÓI MỚI NHẤT CỦA NHÂN VIÊN:
                "{employee_text}"
                
                HÃY PHẢN HỒI LẠI TRONG VAI KHÁCH HÀNG:
                - Giữ phản hồi ngắn gọn (1-2 câu), tự nhiên, bộc lộ cảm xúc tương ứng với thái độ của nhân viên.
                - Nếu nhân viên nhã nhặn, lắng nghe và đưa ra giải pháp hợp lý, hãy dịu giọng bớt.
                - Nếu nhân viên chống chế, hãy tiếp tục bày tỏ sự không đồng tình.
                """
                response = self.client.models.generate_content(
                    model=settings.GEMINI_MODEL,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=CustomerOutput,
                        temperature=0.5
                    )
                )
                return CustomerOutput.model_validate_json(response.text)
            except Exception as e:
                logger.error(f"Lỗi AI Simulator Live: {e}")
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Lỗi từ Google GenAI API: {str(e)}"
                )

        # STUB MODE: phản hồi thông minh dựa trên độ dài và từ khóa của nhân viên
        emp_lower = employee_text.lower()
        if "xin lỗi" in emp_lower or "thông cảm" in emp_lower:
            return CustomerOutput(
                customer_message="Ừ, biết xin lỗi là được rồi. Nhưng giờ cốc này bỏ đi à? Bạn đổi cho tôi cốc khác hay xử lý thế nào?"
            )
        elif "đổi" in emp_lower or "làm lại" in emp_lower or "pha lại" in emp_lower:
            return CustomerOutput(
                customer_message="Được, thế làm lại ngay cho tôi cốc mới ít mặn thôi nhé, tôi đang vội đấy!"
            )
        elif "hoàn tiền" in emp_lower or "quản lý" in emp_lower:
            return CustomerOutput(
                customer_message="Được, bạn gọi quản lý ra đây giải quyết nhanh giúp tôi."
            )
        else:
            return CustomerOutput(
                customer_message="Tôi không đồng ý cách giải thích này. Bạn kiểm tra lại ngay cho tôi!"
            )

    def evaluate_session(
        self,
        steps: List[StepItem],
        rubric: List[RubricItem],
        transcript: List[Dict[str, str]]
    ) -> EvaluationDraft:
        """Module 3: Đánh giá bằng chứng phát ngôn theo Rubric."""
        if settings.AI_MODE == "live":
            if not settings.GEMINI_API_KEY:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Server đang cấu hình AI_MODE=live nhưng thiếu GEMINI_API_KEY."
                )
            try:
                from google.genai import types
                prompt = f"""
                Bạn là giám khảo chấm thi kỹ năng dịch vụ khách hàng ShiftLens.
                Nhiệm vụ: Đọc toàn bộ lịch sử đối thoại và đánh giá phát ngôn của nhân viên theo từng tiêu chí trong Rubric.
                
                QUY TRÌNH SOP:
                {json.dumps([s.model_dump() for s in steps], ensure_ascii=False, indent=2)}
                
                RUBRIC ĐÁNH GIÁ:
                {json.dumps([r.model_dump() for r in rubric], ensure_ascii=False, indent=2)}
                
                TOÀN BỘ TRANSCRIPT HỘI THOẠI:
                {json.dumps(transcript, ensure_ascii=False, indent=2)}
                
                QUY TẮC CỰC KỲ QUAN TRỌNG VỀ BẰNG CHỨNG (EXACT QUOTE):
                - Trường `exact_quote` BẮT BUỘC phải là một trích đoạn ngắn NGUYÊN VĂN từ các câu nói của Employee trong transcript.
                - KHÔNG ĐƯỢC tự ý sửa từ, paraphrase hay bịa đặt từ ngữ mà nhân viên không hề nói.
                - Nếu nhân viên không đạt hoặc không có phát ngôn tương ứng, để `exact_quote: ""` và `passed: false`.
                - Cung cấp `coaching_tip` cụ thể giúp nhân viên hoàn thiện kỹ năng hơn ở ca làm việc sau.
                """
                response = self.client.models.generate_content(
                    model=settings.GEMINI_MODEL,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=EvaluationDraft,
                        temperature=0.1
                    )
                )
                return EvaluationDraft.model_validate_json(response.text)
            except Exception as e:
                logger.error(f"Lỗi AI Evaluator Live: {e}")
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Lỗi từ Google GenAI API: {str(e)}"
                )

        # STUB MODE: Phân tích transcript nhân viên và trích xuất quote thật
        employee_turns = [t.get("employee", "") for t in transcript if t.get("employee")]
        full_emp_text = " ".join(employee_turns)
        
        judgments = []
        for r in rubric:
            cid = r.id
            label_lower = r.label.lower()
            
            passed = False
            exact_quote = ""
            explanation = ""
            
            if "lắng nghe" in label_lower or "xin lỗi" in label_lower or cid == "C1":
                for turn in employee_turns:
                    if "xin lỗi" in turn.lower():
                        passed = True
                        exact_quote = "xin lỗi"
                        explanation = "Nhân viên đã mở lời xin lỗi khách hàng kịp thời."
                        break
                if not passed and employee_turns:
                    explanation = "Chưa thể hiện sự lắng nghe và xin lỗi chân thành."
                    
            elif "xác minh" in label_lower or cid == "C2":
                for turn in employee_turns:
                    if any(w in turn.lower() for w in ["kiểm tra", "hóa đơn", "ly", "cốc", "xem lại"]):
                        passed = True
                        exact_quote = turn[:40]
                        explanation = "Nhân viên đã chủ động kiểm tra tình trạng món đồ uống."
                        break
                if not passed:
                    explanation = "Chưa xác minh rõ nguyên nhân sự cố với khách."
                    
            elif "policy" in label_lower or "chính sách" in label_lower or cid == "C3":
                for turn in employee_turns:
                    if any(w in turn.lower() for w in ["quản lý", "đổi", "pha lại", "quy định"]):
                        passed = True
                        exact_quote = turn[:40]
                        explanation = "Xử lý phù hợp theo quy định chuyển tiếp hoặc giải pháp cho phép."
                        break
                if not passed:
                    explanation = "Chưa tuân thủ đúng quy trình giải quyết sự cố của quán."
                    
            else: # C4: Xác nhận kết quả
                if len(employee_turns) >= 2:
                    passed = True
                    exact_quote = employee_turns[-1][:35]
                    explanation = "Đã có tương tác kết thúc và chốt giải pháp với khách."
                else:
                    passed = False
                    explanation = "Chưa xác nhận lại sự hài lòng của khách hàng."
                    
            judgments.append(
                JudgmentDraft(
                    criterion_id=cid,
                    passed=passed,
                    exact_quote=exact_quote,
                    explanation=explanation
                )
            )

        return EvaluationDraft(
            judgments=judgments,
            coaching_tip="Cần giữ bình tĩnh hơn khi khách phàn nàn gắt gỏng và luôn ghi nhớ giới hạn quyền hạn bồi thường của quán."
        )

ai_service = AIService()
