# backend/tests/test_approval_system.py
# Tests for hierarchical approval system

import pytest
from unittest.mock import Mock, patch
from fastapi import HTTPException
from datetime import datetime

from src.services.approval_service import approval_service
from src.database import schemas
from src.utils.constants import UserRole

class TestApprovalService:
    """Test cases for ApprovalService"""
    
    def setup_method(self):
        """Setup test data"""
        self.developer_user = schemas.UserInDB(
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
        
        self.admin_user = schemas.UserInDB(
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
        
        self.head_teacher_user = schemas.UserInDB(
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
        
        self.homeroom_teacher_user = schemas.UserInDB(
            uid="homeroom-uid",
            email="homeroom@test.com",
            username="homeroom_teacher",
            full_name="Homeroom Teacher",
            role=UserRole.THIRD_GRADE_HOMEROOM,
            is_active=True,
            is_approved=False,  # Pending approval
            school_id="school-1",
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00"
        )
        
        self.general_teacher_user = schemas.UserInDB(
            uid="general-uid",
            email="general@test.com",
            username="general_teacher",
            full_name="General Teacher",
            role=UserRole.GENERAL_TEACHER,
            is_active=True,
            is_approved=False,  # Pending approval
            school_id="school-1",
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00"
        )
        
        self.different_school_teacher = schemas.UserInDB(
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
    
    def test_can_approve_user_developer_to_head_teacher(self):
        """Test that developer can approve head teacher"""
        result = approval_service._can_approve_user(
            self.developer_user, 
            self.head_teacher_user
        )
        assert result is True
    
    def test_can_approve_user_admin_to_head_teacher(self):
        """Test that admin can approve head teacher"""
        result = approval_service._can_approve_user(
            self.admin_user, 
            self.head_teacher_user
        )
        assert result is True
    
    def test_can_approve_user_head_teacher_to_homeroom_teacher(self):
        """Test that head teacher can approve homeroom teacher from same school"""
        result = approval_service._can_approve_user(
            self.head_teacher_user, 
            self.homeroom_teacher_user
        )
        assert result is True
    
    def test_can_approve_user_head_teacher_to_general_teacher(self):
        """Test that head teacher can approve general teacher from same school"""
        result = approval_service._can_approve_user(
            self.head_teacher_user, 
            self.general_teacher_user
        )
        assert result is True
    
    def test_cannot_approve_user_different_school(self):
        """Test that head teacher cannot approve teacher from different school"""
        result = approval_service._can_approve_user(
            self.head_teacher_user, 
            self.different_school_teacher
        )
        assert result is False
    
    def test_cannot_approve_user_homeroom_teacher_no_permission(self):
        """Test that homeroom teacher cannot approve other users"""
        result = approval_service._can_approve_user(
            self.homeroom_teacher_user, 
            self.general_teacher_user
        )
        assert result is False
    
    def test_cannot_approve_user_general_teacher_no_permission(self):
        """Test that general teacher cannot approve other users"""
        result = approval_service._can_approve_user(
            self.general_teacher_user, 
            self.homeroom_teacher_user
        )
        assert result is False
    
    def test_validate_same_school_success(self):
        """Test same school validation success"""
        result = approval_service._validate_same_school(
            self.head_teacher_user, 
            self.homeroom_teacher_user
        )
        assert result is True
    
    def test_validate_same_school_failure(self):
        """Test same school validation failure"""
        result = approval_service._validate_same_school(
            self.head_teacher_user, 
            self.different_school_teacher
        )
        assert result is False
    
    def test_validate_same_school_missing_school_id(self):
        """Test same school validation with missing school ID"""
        user_no_school = schemas.UserInDB(
            uid="no-school-uid",
            email="no-school@test.com",
            username="no_school",
            full_name="No School User",
            role=UserRole.THIRD_GRADE_HOMEROOM,
            is_active=True,
            is_approved=False,
            school_id=None,  # No school ID
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00"
        )
        
        result = approval_service._validate_same_school(
            self.head_teacher_user, 
            user_no_school
        )
        assert result is False
    
    def test_has_approval_permission_developer(self):
        """Test approval permission for developer"""
        result = approval_service._has_approval_permission(self.developer_user)
        assert result is True
    
    def test_has_approval_permission_admin(self):
        """Test approval permission for admin"""
        result = approval_service._has_approval_permission(self.admin_user)
        assert result is True
    
    def test_has_approval_permission_head_teacher(self):
        """Test approval permission for head teacher"""
        result = approval_service._has_approval_permission(self.head_teacher_user)
        assert result is True
    
    def test_no_approval_permission_homeroom_teacher(self):
        """Test no approval permission for homeroom teacher"""
        result = approval_service._has_approval_permission(self.homeroom_teacher_user)
        assert result is False
    
    def test_no_approval_permission_general_teacher(self):
        """Test no approval permission for general teacher"""
        result = approval_service._has_approval_permission(self.general_teacher_user)
        assert result is False
    
    @patch('src.services.approval_service.db')
    def test_get_pending_users_for_approver_developer(self, mock_db):
        """Test getting pending users for developer"""
        # Mock Firestore response
        mock_doc = Mock()
        mock_doc.to_dict.return_value = {
            "uid": "pending-head-uid",
            "email": "pending-head@test.com",
            "username": "pending_head",
            "full_name": "Pending Head Teacher",
            "role": UserRole.THIRD_GRADE_HEAD.value,
            "is_active": True,
            "is_approved": False,
            "school_id": "school-1",
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00"
        }
        
        mock_db.collection.return_value.where.return_value.stream.return_value = [mock_doc]
        
        result = approval_service.get_pending_users_for_approver(self.developer_user)
        
        assert len(result) == 1
        assert result[0].role == UserRole.THIRD_GRADE_HEAD
        assert result[0].is_approved is False
    
    @patch('src.services.approval_service.db')
    def test_get_pending_users_for_approver_head_teacher(self, mock_db):
        """Test getting pending users for head teacher (same school only)"""
        # Mock Firestore response with users from same and different schools
        mock_doc_same_school = Mock()
        mock_doc_same_school.to_dict.return_value = {
            "uid": "pending-homeroom-uid",
            "email": "pending-homeroom@test.com",
            "username": "pending_homeroom",
            "full_name": "Pending Homeroom Teacher",
            "role": UserRole.THIRD_GRADE_HOMEROOM.value,
            "is_active": True,
            "is_approved": False,
            "school_id": "school-1",  # Same school
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00"
        }
        
        mock_doc_diff_school = Mock()
        mock_doc_diff_school.to_dict.return_value = {
            "uid": "pending-diff-uid",
            "email": "pending-diff@test.com",
            "username": "pending_diff",
            "full_name": "Pending Different School Teacher",
            "role": UserRole.THIRD_GRADE_HOMEROOM.value,
            "is_active": True,
            "is_approved": False,
            "school_id": "school-2",  # Different school
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00"
        }
        
        mock_db.collection.return_value.where.return_value.stream.return_value = [
            mock_doc_same_school, mock_doc_diff_school
        ]
        
        result = approval_service.get_pending_users_for_approver(self.head_teacher_user)
        
        # Should only return user from same school
        assert len(result) == 1
        assert result[0].school_id == "school-1"
    
    @patch('src.services.approval_service.db')
    def test_approve_user_hierarchical_success(self, mock_db):
        """Test successful hierarchical user approval"""
        # Mock Firestore document
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            "uid": "homeroom-uid",
            "email": "homeroom@test.com",
            "username": "homeroom_teacher",
            "full_name": "Homeroom Teacher",
            "role": UserRole.THIRD_GRADE_HOMEROOM.value,
            "is_active": True,
            "is_approved": False,
            "school_id": "school-1",
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00"
        }
        
        mock_user_ref = Mock()
        mock_user_ref.get.return_value = mock_doc
        mock_db.collection.return_value.document.return_value = mock_user_ref
        
        # Mock approval logs collection
        mock_db.collection.return_value.add.return_value = None
        
        result = approval_service.approve_user_hierarchical(
            approver=self.head_teacher_user,
            target_uid="homeroom-uid",
            is_approved=True
        )
        
        assert result["success"] is True
        assert result["is_approved"] is True
        assert result["target_uid"] == "homeroom-uid"
        
        # Verify update was called
        mock_user_ref.update.assert_called_once()
        update_data = mock_user_ref.update.call_args[0][0]
        assert update_data["is_approved"] is True
        assert "approved_by" in update_data
        assert "approved_at" in update_data
    
    @patch('src.services.approval_service.db')
    def test_approve_user_hierarchical_rejection(self, mock_db):
        """Test hierarchical user rejection"""
        # Mock Firestore document
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            "uid": "homeroom-uid",
            "email": "homeroom@test.com",
            "username": "homeroom_teacher",
            "full_name": "Homeroom Teacher",
            "role": UserRole.THIRD_GRADE_HOMEROOM.value,
            "is_active": True,
            "is_approved": False,
            "school_id": "school-1",
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00"
        }
        
        mock_user_ref = Mock()
        mock_user_ref.get.return_value = mock_doc
        mock_db.collection.return_value.document.return_value = mock_user_ref
        
        # Mock approval logs collection
        mock_db.collection.return_value.add.return_value = None
        
        rejection_reason = "부적절한 자격 요건"
        result = approval_service.approve_user_hierarchical(
            approver=self.head_teacher_user,
            target_uid="homeroom-uid",
            is_approved=False,
            rejection_reason=rejection_reason
        )
        
        assert result["success"] is True
        assert result["is_approved"] is False
        assert result["target_uid"] == "homeroom-uid"
        
        # Verify update was called with rejection data
        mock_user_ref.update.assert_called_once()
        update_data = mock_user_ref.update.call_args[0][0]
        assert update_data["is_approved"] is False
        assert update_data["is_active"] is False
        assert update_data["rejection_reason"] == rejection_reason
        assert "rejected_at" in update_data
    
    @patch('src.services.approval_service.db')
    def test_approve_user_hierarchical_permission_denied(self, mock_db):
        """Test approval permission denied"""
        # Mock Firestore document
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            "uid": "head-uid-2",
            "email": "head2@test.com",
            "username": "head_teacher_2",
            "full_name": "Head Teacher 2",
            "role": UserRole.THIRD_GRADE_HEAD.value,
            "is_active": True,
            "is_approved": False,
            "school_id": "school-1",
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00"
        }
        
        mock_user_ref = Mock()
        mock_user_ref.get.return_value = mock_doc
        mock_db.collection.return_value.document.return_value = mock_user_ref
        
        # Head teacher trying to approve another head teacher (not allowed)
        with pytest.raises(HTTPException) as exc_info:
            approval_service.approve_user_hierarchical(
                approver=self.head_teacher_user,
                target_uid="head-uid-2",
                is_approved=True
            )
        
        assert exc_info.value.status_code == 403
        assert "승인할 권한이 없습니다" in str(exc_info.value.detail)
    
    @patch('src.services.approval_service.db')
    def test_approve_user_hierarchical_different_school_denied(self, mock_db):
        """Test approval denied for different school"""
        # Mock Firestore document
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            "uid": "diff-school-uid",
            "email": "diff@test.com",
            "username": "diff_teacher",
            "full_name": "Different School Teacher",
            "role": UserRole.THIRD_GRADE_HOMEROOM.value,
            "is_active": True,
            "is_approved": False,
            "school_id": "school-2",  # Different school
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00"
        }
        
        mock_user_ref = Mock()
        mock_user_ref.get.return_value = mock_doc
        mock_db.collection.return_value.document.return_value = mock_user_ref
        
        # Head teacher trying to approve teacher from different school
        with pytest.raises(HTTPException) as exc_info:
            approval_service.approve_user_hierarchical(
                approver=self.head_teacher_user,
                target_uid="diff-school-uid",
                is_approved=True
            )
        
        assert exc_info.value.status_code == 403
        assert "같은 학교 소속 교사만 승인할 수 있습니다" in str(exc_info.value.detail)
    
    @patch('src.services.approval_service.db')
    def test_approve_user_hierarchical_user_not_found(self, mock_db):
        """Test approval with non-existent user"""
        # Mock Firestore document not found
        mock_doc = Mock()
        mock_doc.exists = False
        
        mock_user_ref = Mock()
        mock_user_ref.get.return_value = mock_doc
        mock_db.collection.return_value.document.return_value = mock_user_ref
        
        with pytest.raises(HTTPException) as exc_info:
            approval_service.approve_user_hierarchical(
                approver=self.head_teacher_user,
                target_uid="non-existent-uid",
                is_approved=True
            )
        
        assert exc_info.value.status_code == 404
        assert "승인 대상 사용자를 찾을 수 없습니다" in str(exc_info.value.detail)

if __name__ == "__main__":
    pytest.main([__file__])