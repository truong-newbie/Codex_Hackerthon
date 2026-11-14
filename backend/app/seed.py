from datetime import datetime, timezone
from sqlalchemy.exc import SQLAlchemyError
from .database import engine, SessionLocal
from .models import Tenant, Account, Membership, SOP, SOPVersion
from .auth import hash_password
from .config import settings

def seed_database():
    if settings.ENVIRONMENT == "production":
        raise RuntimeError("Demo seed is disabled in production")
    if settings.ENVIRONMENT != "test" and not settings.DEMO_MODE:
        raise RuntimeError("Set DEMO_MODE=true explicitly before creating demo accounts")
    if settings.ENVIRONMENT != "test":
        try:
            with engine.connect() as connection:
                version = connection.exec_driver_sql(
                    "SELECT version_num FROM alembic_version"
                ).scalar_one_or_none()
        except SQLAlchemyError as error:
            raise RuntimeError("Run and verify 'alembic upgrade head' before demo seed") from error
        if version != "20261114_0002":
            raise RuntimeError("Run and verify 'alembic upgrade head' before demo seed")
    db = SessionLocal()
    
    try:
        # Check if already seeded
        if db.query(Tenant).first():
            print("Database already has data. Skipping seed.")
            return

        print("Seeding ShiftLens initial data...")
        
        # 1. Seed Tenant A: Café Sữa Đá Cầu Giấy (Strict No-Refund)
        tenant_a = Tenant(
            id="tenant-cafe-a",
            name="Café Sữa Đá Cầu Giấy"
        )
        db.add(tenant_a)
        
        # Accounts for Tenant A
        manager_a = Account(
            id="user-manager-a",
            username="manager_a",
            email="manager_a@shiftlens.com",
            password_hash=hash_password("ShiftLens@2026"),
            full_name="Nguyễn Văn Quản Lý (Café A)"
        )
        emp_a = Account(
            id="user-emp-a",
            username="emp_a",
            email="emp_a@shiftlens.com",
            password_hash=hash_password("ShiftLens@2026"),
            full_name="Trần Thị Nhân Viên (Café A)"
        )
        db.add_all([manager_a, emp_a])
        db.flush()
        
        # Memberships for Tenant A
        mem_m_a = Membership(user_id=manager_a.id, tenant_id=tenant_a.id, role="manager")
        mem_e_a = Membership(user_id=emp_a.id, tenant_id=tenant_a.id, role="employee")
        db.add_all([mem_m_a, mem_e_a])
        
        # SOP for Tenant A
        sop_a = SOP(
            id="sop-complaint-a",
            tenant_id=tenant_a.id,
            title="Quy trình xử lý phàn nàn đồ uống (Chính sách nghiêm ngặt)",
            active_version_id="version-sop-a-v1"
        )
        db.add(sop_a)
        db.flush()
        
        sop_a_v1 = SOPVersion(
            id="version-sop-a-v1",
            sop_id=sop_a.id,
            version_no=1,
            status="approved",
            steps_json=[
                {"id": "S1", "instruction": "Lắng nghe chân thành và gửi lời xin lỗi khách hàng ngay khi tiếp nhận."},
                {"id": "S2", "instruction": "Xác minh hóa đơn và tình trạng thực tế của ly đồ uống."},
                {"id": "S3", "instruction": "Đề xuất đổi ly đồ uống mới đúng công thức; tuyệt đối không tự ý hoàn tiền mà phải xin ý kiến quản lý."}
            ],
            rubric_json=[
                {"id": "C1", "label": "Lắng nghe & Xin lỗi chân thành", "weight": 20, "critical": False},
                {"id": "C2", "label": "Xác minh hóa đơn & lỗi pha chế", "weight": 30, "critical": False},
                {"id": "C3", "label": "Tuân thủ chính sách: Không tự ý hoàn tiền khi chưa xin phép quản lý", "weight": 35, "critical": True},
                {"id": "C4", "label": "Xác nhận sự đồng thuận và cảm ơn khách", "weight": 15, "critical": False}
            ],
            approved_by=manager_a.id,
            approved_at=datetime.now(timezone.utc)
        )
        db.add(sop_a_v1)

        # 2. Seed Tenant B: Hanoi Craft Coffee Roasters (Flexible Under 50k)
        tenant_b = Tenant(
            id="tenant-cafe-b",
            name="Hanoi Craft Coffee Roasters"
        )
        db.add(tenant_b)
        
        manager_b = Account(
            id="user-manager-b",
            username="manager_b",
            email="manager_b@shiftlens.com",
            password_hash=hash_password("ShiftLens@2026"),
            full_name="Lê Hoàng Quản Lý (Café B)"
        )
        emp_b = Account(
            id="user-emp-b",
            username="emp_b",
            email="emp_b@shiftlens.com",
            password_hash=hash_password("ShiftLens@2026"),
            full_name="Phạm Minh Nhân Viên (Café B)"
        )
        db.add_all([manager_b, emp_b])
        db.flush()
        
        mem_m_b = Membership(user_id=manager_b.id, tenant_id=tenant_b.id, role="manager")
        mem_e_b = Membership(user_id=emp_b.id, tenant_id=tenant_b.id, role="employee")
        db.add_all([mem_m_b, mem_e_b])
        
        sop_b = SOP(
            id="sop-complaint-b",
            tenant_id=tenant_b.id,
            title="Quy trình xử lý phàn nàn đồ uống (Chính sách linh hoạt dưới 50k)",
            active_version_id="version-sop-b-v1"
        )
        db.add(sop_b)
        db.flush()
        
        sop_b_v1 = SOPVersion(
            id="version-sop-b-v1",
            sop_id=sop_b.id,
            version_no=1,
            status="approved",
            steps_json=[
                {"id": "S1", "instruction": "Lắng nghe với thái độ tôn trọng và mở lời xin lỗi khách."},
                {"id": "S2", "instruction": "Kiểm tra ly nước và nguyên nhân pha chế chưa đạt chuẩn."},
                {"id": "S3", "instruction": "Chủ động đề xuất pha lại ly mới hoặc đổi món khác tương đương giá trị (dưới 50.000đ)."}
            ],
            rubric_json=[
                {"id": "C1", "label": "Lắng nghe & Xin lỗi khách hàng", "weight": 20, "critical": False},
                {"id": "C2", "label": "Kiểm tra thức uống & nguyên nhân", "weight": 30, "critical": False},
                {"id": "C3", "label": "Chủ động xử lý linh hoạt: Đổi mới hoặc hoàn dưới 50.000đ", "weight": 35, "critical": True},
                {"id": "C4", "label": "Lời chúc và tri ân khách hàng", "weight": 15, "critical": False}
            ],
            approved_by=manager_b.id,
            approved_at=datetime.now(timezone.utc)
        )
        db.add(sop_b_v1)
        
        db.commit()
        print("Seeded successfully!")
        print("Tài khoản mẫu (mật khẩu chung: ShiftLens@2026):")
        print("- Café A: Quản lý: manager_a | Nhân viên: emp_a")
        print("- Café B: Quản lý: manager_b | Nhân viên: emp_b")
        
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
