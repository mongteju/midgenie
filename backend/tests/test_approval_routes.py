# backend/tests/test_approval_routes.py
# Integration tests for hierarchical approval API routes

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from src.app import app
from src.database import schemas
from src.utils.constants import UserRole

client = TestClient(app)

class TestApprovalRoutes:
    """Test cases for approval API routes"""
    
    def setup_method(self):
        """Setup test data"""
        self.developer_token = "fake-admin-token"  # Uses fake token for testing
        
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
            is_approved=False,
            school_id="school-1",
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00"
        )
    
    def test_get_approval_rules_public(self):
        """Test getting approval rules (public endpoint)"""
        response = client.get("/approval/approval-rules")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "hierarchy" in data
        assert "level_1" in data["hierarchy"]
        assert "level_2" in data["hierarchy"]
        assert "restrictions" in data
        assert "approval_flow" in data
        
        # Check level 1 (Developer/Admin)
        level_1 = data["hierarchy"]["level_1"]
        assert "developer" in level_1["roles"]
        assert "admin" in level_1["roles"]
        assert "third_grade_head" in level_1["can_approve"]
        
        # Check level 2 (Head Teacher)
        level_2 = data["hierarchy"]["level_2"]
        assert "third_grade_head" in level_2["roles"]
        assert "third_grade_homeroom" in level_2["can_approve"]
        assert "general_teacher" in level_2["can_approve"]
        assert "same_school_only" in level_2["restrictions"]
    
    def test_get_pending_users_unauthorized(self):
        """Test getting pending users without authorization"""
        response = client.get("/approval/pending-users")
        
        assert response.status_code == 401
    
    def test_get_pending_users_no_permission(self):
        """Test getting pending users without approval permission"""
        # Mock a general teacher (no approval permission)
        with patch('src.services.auth_service.get_current_user') as mock_get_user:
            general_teacher = schemas.UserInDB(
                uid="general-uid",
                email="general@test.com",
                username="general_teacher",
                full_name="General Teacher",
                role=UserRole.GENERAL_TEACHER,
                is_active=True,
                is_approved=True,
                school_id="school-1",
                created_at="2024-01-01T00:00:00",
                updated_at="2024-01-01T00:00:00"
            )
            mock_get_user.return_value = general_teacher
            
            response = client.get(
                "/approval/pending-users",
                headers={"Authorization": "Bearer test-token"}
            )
            
            assert response.status_code == 403
            assert "승인 권한이 없습니다" in response.json()["detail"]
    
    @patch('src.services.approval_service.approval_service.get_pending_users_for_approver')
    def test_get_pending_users_success(self, mock_get_pending):
        """Test getting pending users successfully"""
        # Mock pending users
        mock_get_pending.return_value = [self.homeroom_teacher_user]
        
        response = client.get(
            "/approval/pending-users",
            headers={"Authorization": f"Bearer {self.developer_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 1
        assert data[0]["uid"] == "homeroom-uid"
        assert data[0]["role"] == UserRole.THIRD_GRADE_HOMEROOM.value
        assert data[0]["is_approved"] is False
    
    def test_approve_user_unauthorized(self):
        """Test approving user without authorization"""
        approval_data = {
            "target_uid": "homeroom-uid",
            "is_approved": True
        }
        
        response = client.post("/approval/approve-user", json=approval_data)
        
        assert response.status_code == 401
    
    def test_approve_user_no_permission(self):
        """Test approving user without approval permission"""
        with patch('src.services.auth_service.get_current_user') as mock_get_user:
            general_teacher = schemas.UserInDB(
                uid="general-uid",
                email="general@test.com",
                username="general_teacher",
                full_name="General Teacher",
                role=UserRole.GENERAL_TEACHER,
                is_active=True,
                is_approved=True,
                school_id="school-1",
                created_at="2024-01-01T00:00:00",
                updated_at="2024-01-01T00:00:00"
            )
            mock_get_user.return_value = general_teacher
            
            approval_data = {
                "target_uid": "homeroom-uid",
                "is_approved": True
            }
            
            response = client.post(
                "/approval/approve-user",
                json=approval_data,
                headers={"Authorization": "Bearer test-token"}
            )
            
            assert response.status_code == 403
            assert "승인 권한이 없습니다" in response.json()["detail"]
    
    @patch('src.services.approval_service.approval_service.approve_user_hierarchical')
    def test_approve_user_success(self, mock_approve):
        """Test approving user successfully"""
        # Mock approval result
        mock_approve.return_value = {
            "success": True,
            "message": "사용자가 승인되었습니다.",
            "target_uid": "homeroom-uid",
            "target_email": "homeroom@test.com",
            "is_approved": True,
            "approved_by": "admin-test-uid",
            "approved_at": "2024-01-01T12:00:00"
        }
        
        approval_data = {
            "target_uid": "homeroom-uid",
            "is_approved": True
        }
        
        response = client.post(
            "/approval/approve-user",
            json=approval_data,
            headers={"Authorization": f"Bearer {self.developer_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["is_approved"] is True
        assert data["target_uid"] == "homeroom-uid"
        assert "승인되었습니다" in data["message"]
    
    @patch('src.services.approval_service.approval_service.approve_user_hierarchical')
    def test_reject_user_with_reason(self, mock_approve):
        """Test rejecting user with reason"""
        # Mock rejection result
        mock_approve.return_value = {
            "success": True,
            "message": "사용자가 거부되었습니다.",
            "target_uid": "homeroom-uid",
            "target_email": "homeroom@test.com",
            "is_approved": False,
            "approved_by": "admin-test-uid",
            "approved_at": None
        }
        
        approval_data = {
            "target_uid": "homeroom-uid",
            "is_approved": False,
            "rejection_reason": "자격 요건 미충족"
        }
        
        response = client.post(
            "/approval/approve-user",
            json=approval_data,
            headers={"Authorization": f"Bearer {self.developer_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["is_approved"] is False
        assert data["target_uid"] == "homeroom-uid"
        
        # Verify rejection reason was passed to service
        mock_approve.assert_called_once()
        call_args = mock_approve.call_args
        assert call_args[1]["rejection_reason"] == "자격 요건 미충족"
    
    @patch('src.services.approval_service.approval_service.get_approval_history')
    def test_get_approval_history_success(self, mock_get_history):
        """Test getting approval history successfully"""
        # Mock approval history
        mock_history = [
            {
                "id": "log-1",
                "approver_uid": "admin-test-uid",
                "target_uid": "homeroom-uid",
                "action": "approved",
                "reason": None,
                "created_at": "2024-01-01T12:00:00"
            },
            {
                "id": "log-2",
                "approver_uid": "admin-test-uid",
                "target_uid": "general-uid",
                "action": "rejected",
                "reason": "자격 요건 미충족",
                "created_at": "2024-01-01T11:00:00"
            }
        ]
        mock_get_history.return_value = mock_history
        
        response = client.get(
            "/approval/history",
            headers={"Authorization": f"Bearer {self.developer_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 2
        assert data[0]["action"] == "approved"
        assert data[1]["action"] == "rejected"
        assert data[1]["reason"] == "자격 요건 미충족"
    
    @patch('src.services.approval_service.approval_service.get_approval_statistics')
    def test_get_approval_statistics_success(self, mock_get_stats):
        """Test getting approval statistics successfully"""
        # Mock approval statistics
        mock_stats = {
            "pending_count": 3,
            "approved_count": 15,
            "rejected_count": 2,
            "total_processed": 17
        }
        mock_get_stats.return_value = mock_stats
        
        response = client.get(
            "/approval/statistics",
            headers={"Authorization": f"Bearer {self.developer_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["pending_count"] == 3
        assert data["approved_count"] == 15
        assert data["rejected_count"] == 2
        assert data["total_processed"] == 17
    
    def test_get_my_approval_status_success(self):
        """Test getting own approval status"""
        response = client.get(
            "/approval/my-approval-status",
            headers={"Authorization": f"Bearer {self.developer_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "uid" in data
        assert "email" in data
        assert "role" in data
        assert "is_approved" in data
        assert "is_active" in data
    
    def test_invalid_approval_request_missing_fields(self):
        """Test approval request with missing required fields"""
        approval_data = {
            "is_approved": True
            # Missing target_uid
        }
        
        response = client.post(
            "/approval/approve-user",
            json=approval_data,
            headers={"Authorization": f"Bearer {self.developer_token}"}
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_invalid_approval_request_invalid_data_types(self):
        """Test approval request with invalid data types"""
        approval_data = {
            "target_uid": 123,  # Should be string
            "is_approved": "yes"  # Should be boolean
        }
        
        response = client.post(
            "/approval/approve-user",
            json=approval_data,
            headers={"Authorization": f"Bearer {self.developer_token}"}
        )
        
        assert response.status_code == 422  # Validation error

if __name__ == "__main__":
    pytest.main([__file__])