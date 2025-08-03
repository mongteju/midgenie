# backend/src/routes/approval.py
# API routes for hierarchical approval system

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any, Optional
from ..services.approval_service import approval_service
from ..services.auth_service import auth_service
from ..database import schemas
from ..utils.auth_decorators import has_role
from ..utils.constants import UserRole, UserRoleGroups

router = APIRouter(prefix="/approval", tags=["Approval"])

class ApprovalRequest(schemas.BaseModel):
    """승인/거부 요청 스키마"""
    target_uid: str
    is_approved: bool
    rejection_reason: Optional[str] = None

@router.get("/pending-users", response_model=List[schemas.UserInDB])
async def get_pending_users_for_approval(
    current_user: schemas.UserInDB = Depends(auth_service.get_current_user)
):
    """
    Get users pending approval that the current user can approve.
    
    Hierarchical rules:
    - Developer/Admin: Can approve 3학년 부장
    - 3학년 부장: Can approve 3학년 담임/일반교사 from same school
    """
    # Check if user has approval permissions
    if current_user.role not in UserRoleGroups.APPROVAL_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="승인 권한이 없습니다."
        )
    
    return approval_service.get_pending_users_for_approver(current_user)

@router.post("/approve-user", response_model=Dict[str, Any])
async def approve_user_hierarchical(
    approval_request: ApprovalRequest,
    current_user: schemas.UserInDB = Depends(auth_service.get_current_user)
):
    """
    Approve or reject a user registration with hierarchical validation.
    
    Validates:
    - User has approval permissions
    - Hierarchical approval rules are followed
    - School matching for 3학년 부장 approvals
    """
    # Check if user has approval permissions
    if current_user.role not in UserRoleGroups.APPROVAL_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="승인 권한이 없습니다."
        )
    
    return approval_service.approve_user_hierarchical(
        approver=current_user,
        target_uid=approval_request.target_uid,
        is_approved=approval_request.is_approved,
        rejection_reason=approval_request.rejection_reason
    )

@router.get("/history", response_model=List[Dict[str, Any]])
async def get_approval_history(
    current_user: schemas.UserInDB = Depends(auth_service.get_current_user)
):
    """
    Get approval history for the current user.
    Shows all approval/rejection actions performed by the user.
    """
    return approval_service.get_approval_history(current_user)

@router.get("/statistics", response_model=Dict[str, Any])
async def get_approval_statistics(
    current_user: schemas.UserInDB = Depends(auth_service.get_current_user)
):
    """
    Get approval statistics for the current user.
    
    Returns:
    - pending_count: Number of users waiting for approval
    - approved_count: Number of users approved by this user
    - rejected_count: Number of users rejected by this user
    - total_processed: Total number of approval actions
    """
    return approval_service.get_approval_statistics(current_user)

@router.get("/my-approval-status", response_model=Dict[str, Any])
async def get_my_approval_status(
    current_user: schemas.UserInDB = Depends(auth_service.get_current_user)
):
    """
    Get the current user's own approval status and information.
    """
    return {
        "uid": current_user.uid,
        "email": current_user.email,
        "username": current_user.username,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "is_approved": current_user.is_approved,
        "is_active": current_user.is_active,
        "school_id": current_user.school_id,
        "created_at": current_user.created_at,
        "updated_at": current_user.updated_at
    }

@router.get("/approval-rules", response_model=Dict[str, Any])
async def get_approval_rules():
    """
    Get hierarchical approval rules for frontend display.
    Public endpoint to show approval structure.
    """
    return {
        "hierarchy": {
            "level_1": {
                "roles": ["developer", "admin"],
                "display_names": ["개발자", "관리자"],
                "can_approve": ["third_grade_head"],
                "can_approve_display": ["3학년 부장"]
            },
            "level_2": {
                "roles": ["third_grade_head"],
                "display_names": ["3학년 부장"],
                "can_approve": ["third_grade_homeroom", "general_teacher"],
                "can_approve_display": ["3학년 담임", "일반교사"],
                "restrictions": ["same_school_only"]
            }
        },
        "restrictions": {
            "same_school_only": "같은 학교 소속 교사만 승인 가능"
        },
        "approval_flow": [
            "개발자/관리자 → 3학년 부장 승인",
            "3학년 부장 → 3학년 담임/일반교사 승인 (같은 학교만)"
        ]
    }

# Legacy compatibility endpoints
@router.get("/pending-users-legacy", response_model=List[schemas.UserInDB])
async def get_pending_users_legacy(
    current_user: schemas.UserInDB = Depends(has_role([UserRole.ADMIN, UserRole.DEVELOPER]))
):
    """
    Legacy endpoint for admin-only pending user approval.
    Maintained for backward compatibility.
    """
    from ..services.auth_service import auth_service as legacy_auth_service
    return legacy_auth_service.get_pending_users()

@router.post("/approve-user-legacy", response_model=dict)
async def approve_user_legacy(
    approval_data: schemas.UserApproval,
    current_user: schemas.UserInDB = Depends(has_role([UserRole.ADMIN, UserRole.DEVELOPER]))
):
    """
    Legacy endpoint for admin-only user approval.
    Maintained for backward compatibility.
    """
    from ..services.auth_service import auth_service as legacy_auth_service
    
    result = legacy_auth_service.approve_user(
        approval_data.uid, 
        approval_data.is_approved, 
        approval_data.role.value if approval_data.role else None
    )
    
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