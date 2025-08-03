# backend/src/routes/auth.py
# Authentication related API routes using Firebase

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from datetime import datetime
from ..services import auth_service
from ..database import schemas
from ..utils.auth_decorators import has_role
from ..utils.constants import UserRole

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
def register_user(user_data: schemas.UserCreate):
    """
    Register a new user (public endpoint for teacher registration).
    1. Checks if a user with the given email already exists in Firestore.
    2. Creates the user in Firebase Authentication.
    3. Saves the user's details in Firestore with is_approved=False.
    4. Returns success message for admin approval.
    """
    # Check if user already exists in Firestore
    if auth_service.get_user_by_email_from_firestore(user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 등록된 이메일입니다."
        )

    # Create user in Firebase Authentication
    firebase_user = auth_service.create_firebase_user(email=user_data.email, password=user_data.password)
    
    # Save user details in Firestore (pending approval)
    user_doc = auth_service.set_user_role_in_firestore(firebase_user.uid, user_data, is_approved=False)
    
    return {
        "message": "회원가입이 완료되었습니다. 관리자 승인 후 이용 가능합니다.",
        "uid": firebase_user.uid,
        "email": user_data.email,
        "status": "pending_approval"
    }

@router.post("/register-with-invitation", response_model=dict, status_code=status.HTTP_201_CREATED)
def register_user_with_invitation(user_data: schemas.UserCreateWithInvitation):
    """
    초대 링크를 통한 회원가입 (공개 엔드포인트)
    1. 초대 코드 유효성 검증
    2. 이메일 중복 확인
    3. Firebase Authentication에 사용자 생성
    4. 초대 정보를 기반으로 학교 자동 매핑
    5. 사용자 정보를 Firestore에 저장 (승인 대기 상태)
    6. 초대 코드 사용 처리
    """
    from ..services.invitation_service import invitation_service
    
    # 초대 코드 유효성 검증
    invitation_validation = invitation_service.validate_invitation_code(user_data.invitation_code)
    
    if not invitation_validation.is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=invitation_validation.error_message or "유효하지 않은 초대 코드입니다."
        )
    
    # 이메일 중복 확인
    if auth_service.get_user_by_email_from_firestore(user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 등록된 이메일입니다."
        )
    
    # 초대된 역할과 입력된 역할 일치 확인
    if user_data.role != invitation_validation.invited_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="초대된 역할과 선택한 역할이 일치하지 않습니다."
        )
    
    # Firebase Authentication에 사용자 생성
    firebase_user = auth_service.create_firebase_user(email=user_data.email, password=user_data.password)
    
    # 초대 정보를 기반으로 사용자 데이터 수정
    user_data.school_name = invitation_validation.school_name  # 학교 자동 매핑
    
    # Firestore에 사용자 정보 저장 (승인 대기 상태)
    user_doc = auth_service.set_user_role_in_firestore(
        firebase_user.uid, 
        user_data, 
        is_approved=False,
        invitation_school_id=invitation_validation.school_id
    )
    
    # 초대 코드 사용 처리
    invitation_service.use_invitation_code(user_data.invitation_code)
    
    return {
        "message": "초대 링크를 통한 회원가입이 완료되었습니다. 승인 후 이용 가능합니다.",
        "uid": firebase_user.uid,
        "email": user_data.email,
        "school_name": invitation_validation.school_name,
        "role": user_data.role.value,
        "status": "pending_approval"
    }

@router.post("/admin/register", response_model=schemas.UserInDB, status_code=status.HTTP_201_CREATED)
def admin_register_user(user_data: schemas.UserCreate, current_user: schemas.UserInDB = Depends(has_role([UserRole.ADMIN]))):
    """
    Register a new user by admin (admin only endpoint).
    1. Checks if a user with the given email already exists in Firestore.
    2. Creates the user in Firebase Authentication.
    3. Saves the user's role and other details in Firestore with is_approved=True.
    """
    # Check if user already exists in Firestore
    if auth_service.get_user_by_email_from_firestore(user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists."
        )

    # Create user in Firebase Authentication
    firebase_user = auth_service.create_firebase_user(email=user_data.email, password=user_data.password)
    
    # Save user details in Firestore (auto-approved by admin)
    user_doc = auth_service.set_user_role_in_firestore(firebase_user.uid, user_data, is_approved=True)
    
    return schemas.UserInDB(**user_doc)

@router.get("/me", response_model=schemas.UserInDB)
async def read_users_me(current_user: schemas.UserInDB = Depends(auth_service.get_current_user)):
    """
    Get the profile of the currently authenticated user.
    """
    return current_user

# 승인 관련 API 엔드포인트 (레거시 호환성을 위해 유지)
@router.get("/pending-users", response_model=List[schemas.UserInDB])
async def get_pending_users(current_user: schemas.UserInDB = Depends(has_role([UserRole.ADMIN, UserRole.DEVELOPER]))):
    """
    Get all users pending approval (admin/developer only).
    
    Note: This is a legacy endpoint. New implementations should use /approval/pending-users
    which supports hierarchical approval.
    """
    return auth_service.get_pending_users()

@router.post("/approve-user", response_model=dict)
async def approve_user(
    approval_data: schemas.UserApproval, 
    current_user: schemas.UserInDB = Depends(has_role([UserRole.ADMIN, UserRole.DEVELOPER]))
):
    """
    Approve or reject a user registration (admin/developer only).
    
    Note: This is a legacy endpoint. New implementations should use /approval/approve-user
    which supports hierarchical approval with school validation.
    """
    result = auth_service.approve_user(approval_data.uid, approval_data.is_approved, approval_data.role.value if approval_data.role else None)
    
    if result:
        status_text = "승인" if approval_data.is_approved else "거부"
        return {
            "message": f"사용자 {status_text}이 완료되었습니다.",
            "uid": approval_data.uid,
            "is_approved": approval_data.is_approved
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다."
        )

@router.get("/schools-for-signup", response_model=List[dict])
async def get_schools_for_signup():
    """
    Get list of schools for signup dropdown (public endpoint).
    """
    from ..services.school_service import school_service
    
    schools = school_service.get_schools()
    return [
        {
            "id": school.id,
            "name": school.name,
            "address": school.address
        }
        for school in schools
    ]

@router.post("/check-email", response_model=dict)
async def check_email_availability(email_data: dict):
    """
    Check if email is available for registration (public endpoint).
    """
    email = email_data.get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이메일이 필요합니다."
        )
    
    existing_user = auth_service.get_user_by_email_from_firestore(email)
    
    return {
        "email": email,
        "available": existing_user is None,
        "message": "사용 가능한 이메일입니다." if existing_user is None else "이미 사용 중인 이메일입니다."
    }

@router.get("/selectable-roles", response_model=List[dict])
async def get_selectable_roles():
    """
    Get list of roles that can be selected during signup (public endpoint).
    """
    from ..utils.constants import UserRoleGroups, RoleDisplayNames
    
    roles = []
    for role in UserRoleGroups.SELECTABLE_ROLES:
        roles.append({
            "value": role.value,
            "label": RoleDisplayNames.ROLE_NAMES.get(role, role.value),
            "description": RoleDisplayNames.ROLE_DESCRIPTIONS.get(role, "")
        })
    
    return roles

# Note: The /token endpoint is removed.
# The client should get the ID token from Firebase directly after a successful login
# and send it in the Authorization header as a Bearer token for all authenticated requests.
