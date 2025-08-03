# backend/test_approval_functionality.py
# Simple test script to verify approval system functionality

from src.services.approval_service import approval_service
from src.database import schemas
from src.utils.constants import UserRole

def test_approval_permissions():
    """Test approval permission logic"""
    print("Testing approval permission logic...")
    
    # Create test users
    developer = schemas.UserInDB(
        uid="dev-uid",
        email="dev@test.com",
        username="developer",
        full_name="Developer User",
        role=UserRole.DEVELOPER,
        is_active=True,
        is_approved=True,
        school_id="school-1",
        created_at="2024-01-01T00:00:00",
        updated_at="2024-01-01T00:00:00"
    )
    
    admin = schemas.UserInDB(
        uid="admin-uid",
        email="admin@test.com",
        username="admin",
        full_name="Admin User",
        role=UserRole.ADMIN,
        is_active=True,
        is_approved=True,
        school_id="school-1",
        created_at="2024-01-01T00:00:00",
        updated_at="2024-01-01T00:00:00"
    )
    
    head_teacher = schemas.UserInDB(
        uid="head-uid",
        email="head@test.com",
        username="head_teacher",
        full_name="Head Teacher",
        role=UserRole.THIRD_GRADE_HEAD,
        is_active=True,
        is_approved=True,
        school_id="school-1",
        created_at="2024-01-01T00:00:00",
        updated_at="2024-01-01T00:00:00"
    )
    
    homeroom_teacher = schemas.UserInDB(
        uid="homeroom-uid",
        email="homeroom@test.com",
        username="homeroom_teacher",
        full_name="Homeroom Teacher",
        role=UserRole.THIRD_GRADE_HOMEROOM,
        is_active=True,
        is_approved=False,
        school_id="school-1",
        created_at="2024-01-01T00:00:00",
        updated_at="2024-01-01T00:00:00"
    )
    
    general_teacher = schemas.UserInDB(
        uid="general-uid",
        email="general@test.com",
        username="general_teacher",
        full_name="General Teacher",
        role=UserRole.GENERAL_TEACHER,
        is_active=True,
        is_approved=False,
        school_id="school-1",
        created_at="2024-01-01T00:00:00",
        updated_at="2024-01-01T00:00:00"
    )
    
    different_school_teacher = schemas.UserInDB(
        uid="diff-school-uid",
        email="diff@test.com",
        username="diff_teacher",
        full_name="Different School Teacher",
        role=UserRole.THIRD_GRADE_HOMEROOM,
        is_active=True,
        is_approved=False,
        school_id="school-2",  # Different school
        created_at="2024-01-01T00:00:00",
        updated_at="2024-01-01T00:00:00"
    )
    
    # Test approval permissions
    print("\n1. Testing approval permissions:")
    
    # Developer should have approval permission
    assert approval_service._has_approval_permission(developer) == True
    print("✓ Developer has approval permission")
    
    # Admin should have approval permission
    assert approval_service._has_approval_permission(admin) == True
    print("✓ Admin has approval permission")
    
    # Head teacher should have approval permission
    assert approval_service._has_approval_permission(head_teacher) == True
    print("✓ Head teacher has approval permission")
    
    # Homeroom teacher should NOT have approval permission
    assert approval_service._has_approval_permission(homeroom_teacher) == False
    print("✓ Homeroom teacher does NOT have approval permission")
    
    # General teacher should NOT have approval permission
    assert approval_service._has_approval_permission(general_teacher) == False
    print("✓ General teacher does NOT have approval permission")
    
    print("\n2. Testing hierarchical approval rules:")
    
    # Developer can approve head teacher
    assert approval_service._can_approve_user(developer, head_teacher) == True
    print("✓ Developer can approve head teacher")
    
    # Admin can approve head teacher
    assert approval_service._can_approve_user(admin, head_teacher) == True
    print("✓ Admin can approve head teacher")
    
    # Head teacher can approve homeroom teacher (same school)
    assert approval_service._can_approve_user(head_teacher, homeroom_teacher) == True
    print("✓ Head teacher can approve homeroom teacher (same school)")
    
    # Head teacher can approve general teacher (same school)
    assert approval_service._can_approve_user(head_teacher, general_teacher) == True
    print("✓ Head teacher can approve general teacher (same school)")
    
    # Head teacher CANNOT approve teacher from different school
    assert approval_service._can_approve_user(head_teacher, different_school_teacher) == False
    print("✓ Head teacher CANNOT approve teacher from different school")
    
    # Homeroom teacher CANNOT approve other users
    assert approval_service._can_approve_user(homeroom_teacher, general_teacher) == False
    print("✓ Homeroom teacher CANNOT approve other users")
    
    print("\n3. Testing school validation:")
    
    # Same school validation should pass
    assert approval_service._validate_same_school(head_teacher, homeroom_teacher) == True
    print("✓ Same school validation passes")
    
    # Different school validation should fail
    assert approval_service._validate_same_school(head_teacher, different_school_teacher) == False
    print("✓ Different school validation fails")
    
    print("\n✅ All approval permission tests passed!")

def test_role_hierarchy():
    """Test role hierarchy logic"""
    print("\nTesting role hierarchy...")
    
    # Test role hierarchy levels
    from src.utils.constants import UserRoleGroups
    
    print(f"System admin roles: {[role.value for role in UserRoleGroups.SYSTEM_ADMIN_ROLES]}")
    print(f"Selectable roles: {[role.value for role in UserRoleGroups.SELECTABLE_ROLES]}")
    print(f"Approval roles: {[role.value for role in UserRoleGroups.APPROVAL_ROLES]}")
    
    # Verify hierarchy structure
    assert UserRole.DEVELOPER in UserRoleGroups.SYSTEM_ADMIN_ROLES
    assert UserRole.ADMIN in UserRoleGroups.SYSTEM_ADMIN_ROLES
    assert UserRole.THIRD_GRADE_HEAD in UserRoleGroups.SELECTABLE_ROLES
    assert UserRole.THIRD_GRADE_HOMEROOM in UserRoleGroups.SELECTABLE_ROLES
    assert UserRole.GENERAL_TEACHER in UserRoleGroups.SELECTABLE_ROLES
    
    print("✅ Role hierarchy structure is correct!")

if __name__ == "__main__":
    print("🚀 Testing Hierarchical Approval System")
    print("=" * 50)
    
    try:
        test_approval_permissions()
        test_role_hierarchy()
        
        print("\n🎉 All tests passed! Hierarchical approval system is working correctly.")
        print("\nApproval Flow Summary:")
        print("1. Developer/Admin → 3학년 부장 승인")
        print("2. 3학년 부장 → 3학년 담임/일반교사 승인 (같은 학교만)")
        print("3. 학교 코드 일치 검증 적용")
        print("4. 승인/거부 상태 관리 구현")
        print("5. 승인 로그 및 알림 시스템 준비")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()