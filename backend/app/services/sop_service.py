from datetime import datetime, timezone
from typing import List
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from ..models import SOP, SOPVersion
from ..schemas import StepItem, RubricItem, SOPVersionDetail, SOPDetailResponse

class SOPService:
    @staticmethod
    def get_tenant_sops(db: Session, tenant_id: str, role: str = "employee") -> List[SOPDetailResponse]:
        sops = db.query(SOP).filter(SOP.tenant_id == tenant_id).all()
        results = []
        for sop in sops:
            active_version_detail = None
            versions_list = []
            
            for v in sorted(sop.versions, key=lambda x: x.version_no, reverse=True):
                # FR-03: Draft versions must not be exposed to employees
                if role != "manager" and v.status == "draft":
                    continue
                    
                v_detail = SOPVersionDetail(
                    id=v.id,
                    sop_id=v.sop_id,
                    version_no=v.version_no,
                    status=v.status,
                    steps=[StepItem(**s) for s in v.steps_json],
                    rubric=[RubricItem(**r) for r in v.rubric_json],
                    approved_by=v.approved_by,
                    approved_at=v.approved_at,
                    created_at=v.created_at
                )
                versions_list.append(v_detail)
                if sop.active_version_id == v.id and v.status == "approved":
                    active_version_detail = v_detail

            if role != "manager" and active_version_detail is None:
                continue

            results.append(
                SOPDetailResponse(
                    id=sop.id,
                    tenant_id=sop.tenant_id,
                    title=sop.title,
                    active_version=active_version_detail,
                    versions=versions_list
                )
            )
        return results

    @staticmethod
    def _validate_steps_rubric(steps: List[StepItem], rubric: List[RubricItem]) -> None:
        step_ids = [s.id for s in steps]
        if len(step_ids) != len(set(step_ids)):
            raise HTTPException(status_code=422, detail="Danh sách các bước (steps) chứa ID bị trùng lặp")
        criterion_ids = [r.id for r in rubric]
        if len(criterion_ids) != len(set(criterion_ids)):
            raise HTTPException(status_code=422, detail="Danh sách tiêu chí đánh giá (rubric) chứa ID bị trùng lặp")
        total_weight = sum(r.weight for r in rubric)
        if total_weight != 100:
            raise HTTPException(status_code=422, detail=f"Tổng trọng số Rubric phải bằng 100 (Hiện tại: {total_weight})")

    @staticmethod
    def create_sop(
        db: Session, tenant_id: str, title: str,
        steps: List[StepItem], rubric: List[RubricItem]
    ) -> SOPDetailResponse:
        SOPService._validate_steps_rubric(steps, rubric)
        existing = db.query(SOP).filter(SOP.tenant_id == tenant_id, SOP.title == title).first()
        if existing:
            raise HTTPException(status_code=409, detail="Tên SOP đã tồn tại trong cửa hàng")
        sop = SOP(tenant_id=tenant_id, title=title)
        db.add(sop)
        db.flush()
        version = SOPVersion(
            sop_id=sop.id, version_no=1, status="draft",
            steps_json=[s.model_dump() for s in steps],
            rubric_json=[r.model_dump() for r in rubric],
        )
        db.add(version)
        db.commit()
        db.refresh(sop)
        db.refresh(version)
        return SOPDetailResponse(
            id=sop.id, tenant_id=tenant_id, title=sop.title, active_version=None,
            versions=[SOPVersionDetail(
                id=version.id, sop_id=sop.id, version_no=1, status="draft",
                steps=steps, rubric=rubric, created_at=version.created_at,
            )],
        )

    @staticmethod
    def create_draft_version(
        db: Session,
        sop_id: str,
        tenant_id: str,
        steps: List[StepItem],
        rubric: List[RubricItem]
    ) -> SOPVersionDetail:
        sop = db.query(SOP).filter(SOP.id == sop_id, SOP.tenant_id == tenant_id).first()
        if not sop:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy SOP")
            
        SOPService._validate_steps_rubric(steps, rubric)
            
        # Determine next version number
        highest_version = db.query(SOPVersion).filter(SOPVersion.sop_id == sop_id).order_by(SOPVersion.version_no.desc()).first()
        next_version_no = (highest_version.version_no + 1) if highest_version else 1
        
        new_version = SOPVersion(
            sop_id=sop.id,
            version_no=next_version_no,
            status="draft",
            steps_json=[s.model_dump() for s in steps],
            rubric_json=[r.model_dump() for r in rubric]
        )
        db.add(new_version)
        db.commit()
        db.refresh(new_version)
        
        return SOPVersionDetail(
            id=new_version.id,
            sop_id=new_version.sop_id,
            version_no=new_version.version_no,
            status=new_version.status,
            steps=steps,
            rubric=rubric,
            created_at=new_version.created_at
        )

    @staticmethod
    def approve_version(
        db: Session,
        version_id: str,
        tenant_id: str,
        manager_id: str
    ) -> SOPVersion:
        version = db.query(SOPVersion).filter(SOPVersion.id == version_id).first()
        if not version:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy phiên bản SOP")
            
        sop = db.query(SOP).filter(SOP.id == version.sop_id, SOP.tenant_id == tenant_id).first()
        if not sop:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy SOP thuộc cửa hàng của bạn")
            
        if version.status == "approved":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Phiên bản này đã được phê duyệt trước đó")
            
        if version.status == "superseded":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Phiên bản cũ đã hết hiệu lực, vui lòng tạo bản thảo mới")
            
        # Supersede old approved versions
        old_versions = db.query(SOPVersion).filter(
            SOPVersion.sop_id == sop.id,
            SOPVersion.status == "approved"
        ).all()
        for old_v in old_versions:
            old_v.status = "superseded"
            
        version.status = "approved"
        version.approved_by = manager_id
        version.approved_at = datetime.now(timezone.utc)
        sop.active_version_id = version.id
        
        db.commit()
        db.refresh(version)
        return version

sop_service = SOPService()
