# backend/src/services/approval_service.py
# Service for handling hierarchical approval system

from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import HTTPException, status
from ..database import schemas
from ..database.firebase_config import db
from ..utils.constants import UserRole, UserRoleGroups
from .auth_service import auth_service
from .school_service import school_service

class ApprovalService:
    """
    Service class for handling hierarchical approval system.
    
    Approval hierarchy:
    - Developer/Admin → 3학년 부장 (Third Grade Head)
    - 3학년 부장 → 3학년 담임/일반교사 (same school only)
    """
    
    def __init__(self):
        pass
    
    def get_pending_users_for_approver(self, current_user: schemas.UserInDB) -> List[schemas.UserInDB]:
        """
        Get users pending approval that the current user can approve.
        
        Args:
            current_user: The user requesting pending approvals
            
        Returns:
            List of users that can be approved by the current user
        """
        try:
            # Get all pending users
            users_ref = db.collection('users').where('is_approved', '==', False)
            docs = users_ref.stream()
            
            pending_users = []
            for doc in docs:
                user_data = doc.to_dict()
                pending_user = schemas.UserInDB(**user_data)
                
                # Check if current user can approve this pending user
                if self._can_approve_user(current_user, pending_user):
                    pending_users.append(pending_user)
            
            return pending_users
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get pending users: {e}"
            )
    
    def approve_user_hierarchical(
        self, 
        approver: schemas.UserInDB, 
        target_uid: str, 
        is_approved: bool, 
        rejection_reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Approve or reject a user registration with hierarchical validation.
        
        Args:
            approver: The user performing the approval
            target_uid: UID of the user to approve/reject
            is_approved: Whether to approve (True) or reject (False)
            rejection_reason: Reason for rejection (optional)
            
        Returns:
            Dictionary with approval result
        """
        try:
            # Get target user
            target_user_ref = db.collection('users').document(target_uid)
            target_user_doc = target_user_ref.get()
            
            if not target_user_doc.exists:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="승인 대상 사용자를 찾을 수 없습니다."
                )
            
            target_user_data = target_user_doc.to_dict()
            target_user = schemas.UserInDB(**target_user_data)
            
            # Validate approval permission
            if not self._can_approve_user(approver, target_user):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="해당 사용자를 승인할 권한이 없습니다."
                )
            
            # Validate school matching for 3학년 부장 approving teachers
            if approver.role == UserRole.THIRD_GRADE_HEAD:
                if not self._validate_same_school(approver, target_user):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="같은 학교 소속 교사만 승인할 수 있습니다."
                    )
            
            # Update user approval status
            now = datetime.utcnow().isoformat()
            update_data = {
                "is_approved": is_approved,
                "updated_at": now,
                "approved_by": approver.uid,
                "approved_at": now if is_approved else None
            }
            
            if not is_approved:
                update_data["is_active"] = False
                if rejection_reason:
                    update_data["rejection_reason"] = rejection_reason
                update_data["rejected_at"] = now
            
            target_user_ref.update(update_data)
            
            # Log approval action
            self._log_approval_action(
                approver_uid=approver.uid,
                target_uid=target_uid,
                action="approved" if is_approved else "rejected",
                reason=rejection_reason
            )
            
            # Send notification (placeholder for future implementation)
            self._send_approval_notification(target_user, is_approved, rejection_reason)
            
            return {
                "success": True,
                "message": f"사용자가 {'승인' if is_approved else '거부'}되었습니다.",
                "target_uid": target_uid,
                "target_email": target_user.email,
                "is_approved": is_approved,
                "approved_by": approver.uid,
                "approved_at": now if is_approved else None
            }
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"승인 처리 중 오류가 발생했습니다: {e}"
            )
    
    def get_approval_history(self, current_user: schemas.UserInDB) -> List[Dict[str, Any]]:
        """
        Get approval history for the current user.
        
        Args:
            current_user: The user requesting approval history
            
        Returns:
            List of approval actions performed by the user
        """
        try:
            # Only users with approval permissions can view history
            if not self._has_approval_permission(current_user):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="승인 이력을 조회할 권한이 없습니다."
                )
            
            approval_logs_ref = db.collection('approval_logs').where('approver_uid', '==', current_user.uid)
            docs = approval_logs_ref.order_by('created_at', direction='DESCENDING').stream()
            
            history = []
            for doc in docs:
                log_data = doc.to_dict()
                history.append(log_data)
            
            return history
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"승인 이력 조회 중 오류가 발생했습니다: {e}"
            )
    
    def get_approval_statistics(self, current_user: schemas.UserInDB) -> Dict[str, Any]:
        """
        Get approval statistics for the current user.
        
        Args:
            current_user: The user requesting statistics
            
        Returns:
            Dictionary with approval statistics
        """
        try:
            if not self._has_approval_permission(current_user):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="승인 통계를 조회할 권한이 없습니다."
                )
            
            # Get pending users count
            pending_users = self.get_pending_users_for_approver(current_user)
            pending_count = len(pending_users)
            
            # Get approval history count
            approval_logs_ref = db.collection('approval_logs').where('approver_uid', '==', current_user.uid)
            approval_docs = list(approval_logs_ref.stream())
            
            approved_count = len([doc for doc in approval_docs if doc.to_dict().get('action') == 'approved'])
            rejected_count = len([doc for doc in approval_docs if doc.to_dict().get('action') == 'rejected'])
            
            return {
                "pending_count": pending_count,
                "approved_count": approved_count,
                "rejected_count": rejected_count,
                "total_processed": approved_count + rejected_count
            }
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"승인 통계 조회 중 오류가 발생했습니다: {e}"
            )
    
    def _can_approve_user(self, approver: schemas.UserInDB, target_user: schemas.UserInDB) -> bool:
        """
        Check if approver can approve the target user based on hierarchical rules.
        
        Args:
            approver: The user attempting to approve
            target_user: The user to be approved
            
        Returns:
            True if approval is allowed, False otherwise
        """
        # Developer and Admin can approve 3학년 부장
        if approver.role in [UserRole.DEVELOPER, UserRole.ADMIN]:
            return target_user.role in [
                UserRole.THIRD_GRADE_HEAD,
                UserRole.HEAD_TEACHER  # Legacy compatibility
            ]
        
        # 3학년 부장 can approve 3학년 담임 and 일반교사 from same school
        elif approver.role in [UserRole.THIRD_GRADE_HEAD, UserRole.HEAD_TEACHER]:
            if target_user.role in [UserRole.THIRD_GRADE_HOMEROOM, UserRole.GENERAL_TEACHER, UserRole.HOMEROOM_TEACHER]:
                return self._validate_same_school(approver, target_user)
        
        return False
    
    def _validate_same_school(self, approver: schemas.UserInDB, target_user: schemas.UserInDB) -> bool:
        """
        Validate that both users belong to the same school.
        
        Args:
            approver: The approving user
            target_user: The target user
            
        Returns:
            True if both users are from the same school, False otherwise
        """
        if not approver.school_id or not target_user.school_id:
            return False
        
        return approver.school_id == target_user.school_id
    
    def _has_approval_permission(self, user: schemas.UserInDB) -> bool:
        """
        Check if user has approval permissions.
        
        Args:
            user: The user to check
            
        Returns:
            True if user has approval permissions, False otherwise
        """
        return user.role in UserRoleGroups.APPROVAL_ROLES
    
    def _log_approval_action(
        self, 
        approver_uid: str, 
        target_uid: str, 
        action: str, 
        reason: Optional[str] = None
    ) -> None:
        """
        Log approval action to Firestore.
        
        Args:
            approver_uid: UID of the approver
            target_uid: UID of the target user
            action: Action performed (approved/rejected)
            reason: Reason for the action (optional)
        """
        try:
            now = datetime.utcnow().isoformat()
            log_data = {
                "approver_uid": approver_uid,
                "target_uid": target_uid,
                "action": action,
                "reason": reason,
                "created_at": now
            }
            
            db.collection('approval_logs').add(log_data)
            
        except Exception as e:
            # Log error but don't fail the approval process
            print(f"Failed to log approval action: {e}")
    
    def _send_approval_notification(
        self, 
        target_user: schemas.UserInDB, 
        is_approved: bool, 
        rejection_reason: Optional[str] = None
    ) -> None:
        """
        Send notification to user about approval status.
        
        Args:
            target_user: The user who was approved/rejected
            is_approved: Whether the user was approved
            rejection_reason: Reason for rejection (if applicable)
        """
        # Placeholder for notification system
        # This could be implemented with email, push notifications, etc.
        try:
            notification_data = {
                "user_uid": target_user.uid,
                "user_email": target_user.email,
                "type": "approval_status",
                "is_approved": is_approved,
                "message": "계정이 승인되었습니다." if is_approved else f"계정이 거부되었습니다. 사유: {rejection_reason or '사유 없음'}",
                "created_at": datetime.utcnow().isoformat()
            }
            
            # Store notification in Firestore for now
            db.collection('notifications').add(notification_data)
            
            # TODO: Implement actual email/push notification sending
            
        except Exception as e:
            # Log error but don't fail the approval process
            print(f"Failed to send approval notification: {e}")

# Create service instance
approval_service = ApprovalService()