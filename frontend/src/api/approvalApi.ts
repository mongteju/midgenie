// frontend/src/api/approvalApi.ts
// API client for hierarchical approval system

export interface PendingUser {
  uid: string;
  username: string;
  email: string;
  full_name: string;
  role: string;
  school_id?: string;
  grade?: number;
  class_number?: number;
  is_homeroom_teacher?: boolean;
  created_at: string;
  updated_at: string;
  is_approved: boolean;
  is_active: boolean;
}

export interface ApprovalRequest {
  target_uid: string;
  is_approved: boolean;
  rejection_reason?: string;
}

export interface ApprovalResponse {
  success: boolean;
  message: string;
  target_uid: string;
  target_email: string;
  is_approved: boolean;
  approved_by: string;
  approved_at?: string;
}

export interface ApprovalStatistics {
  pending_count: number;
  approved_count: number;
  rejected_count: number;
  total_processed: number;
}

export interface ApprovalHistory {
  id: string;
  approver_uid: string;
  target_uid: string;
  action: "approved" | "rejected";
  reason?: string;
  created_at: string;
}

export interface ApprovalRules {
  hierarchy: {
    level_1: {
      roles: string[];
      display_names: string[];
      can_approve: string[];
      can_approve_display: string[];
    };
    level_2: {
      roles: string[];
      display_names: string[];
      can_approve: string[];
      can_approve_display: string[];
      restrictions: string[];
    };
  };
  restrictions: {
    same_school_only: string;
  };
  approval_flow: string[];
}

export interface UserApprovalStatus {
  uid: string;
  email: string;
  username: string;
  full_name: string;
  role: string;
  is_approved: boolean;
  is_active: boolean;
  school_id?: string;
  created_at: string;
  updated_at: string;
}

class ApprovalApi {
  private baseUrl: string;

  constructor(baseUrl: string = "/api") {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
    token?: string
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const headers: HeadersInit = {
      "Content-Type": "application/json",
      ...options.headers,
    };

    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }

    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(
        errorData.detail || `HTTP ${response.status}: ${response.statusText}`
      );
    }

    return response.json();
  }

  // Get users pending approval that the current user can approve
  async getPendingUsers(token: string): Promise<PendingUser[]> {
    return this.request<PendingUser[]>("/approval/pending-users", {}, token);
  }

  // Approve or reject a user with hierarchical validation
  async approveUser(
    request: ApprovalRequest,
    token: string
  ): Promise<ApprovalResponse> {
    return this.request<ApprovalResponse>(
      "/approval/approve-user",
      {
        method: "POST",
        body: JSON.stringify(request),
      },
      token
    );
  }

  // Get approval history for the current user
  async getApprovalHistory(token: string): Promise<ApprovalHistory[]> {
    return this.request<ApprovalHistory[]>("/approval/history", {}, token);
  }

  // Get approval statistics for the current user
  async getApprovalStatistics(token: string): Promise<ApprovalStatistics> {
    return this.request<ApprovalStatistics>("/approval/statistics", {}, token);
  }

  // Get current user's approval status
  async getMyApprovalStatus(token: string): Promise<UserApprovalStatus> {
    return this.request<UserApprovalStatus>(
      "/approval/my-approval-status",
      {},
      token
    );
  }

  // Get hierarchical approval rules (public endpoint)
  async getApprovalRules(): Promise<ApprovalRules> {
    return this.request<ApprovalRules>("/approval/approval-rules");
  }

  // Legacy endpoints for backward compatibility
  async getPendingUsersLegacy(token: string): Promise<PendingUser[]> {
    return this.request<PendingUser[]>(
      "/approval/pending-users-legacy",
      {},
      token
    );
  }

  async approveUserLegacy(
    request: { uid: string; is_approved: boolean; role?: string },
    token: string
  ): Promise<{ message: string; uid: string; is_approved: boolean }> {
    return this.request(
      "/approval/approve-user-legacy",
      {
        method: "POST",
        body: JSON.stringify(request),
      },
      token
    );
  }
}

// Create and export a singleton instance
export const approvalApi = new ApprovalApi();

// Utility functions for role management
export const RoleUtils = {
  // Get display name for role
  getRoleDisplayName(role: string): string {
    const roleMap: Record<string, string> = {
      developer: "개발자",
      admin: "관리자",
      third_grade_head: "3학년 부장",
      third_grade_homeroom: "3학년 담임",
      general_teacher: "일반교사",
      // Legacy compatibility
      head_teacher: "부장교사",
      homeroom_teacher: "담임교사",
    };
    return roleMap[role] || role;
  },

  // Get role color for UI
  getRoleColor(role: string): string {
    const colorMap: Record<string, string> = {
      developer: "purple",
      admin: "red",
      third_grade_head: "blue",
      third_grade_homeroom: "green",
      general_teacher: "orange",
      // Legacy compatibility
      head_teacher: "blue",
      homeroom_teacher: "green",
    };
    return colorMap[role] || "default";
  },

  // Check if role can approve other roles
  canApproveRole(approverRole: string, targetRole: string): boolean {
    // Developer and Admin can approve 3학년 부장
    if (["developer", "admin"].includes(approverRole)) {
      return ["third_grade_head", "head_teacher"].includes(targetRole);
    }

    // 3학년 부장 can approve 3학년 담임 and 일반교사
    if (["third_grade_head", "head_teacher"].includes(approverRole)) {
      return [
        "third_grade_homeroom",
        "general_teacher",
        "homeroom_teacher",
      ].includes(targetRole);
    }

    return false;
  },

  // Get approval level for role
  getApprovalLevel(role: string): number {
    if (["developer", "admin"].includes(role)) return 1;
    if (["third_grade_head", "head_teacher"].includes(role)) return 2;
    if (
      ["third_grade_homeroom", "general_teacher", "homeroom_teacher"].includes(
        role
      )
    )
      return 3;
    return 4; // No approval permission
  },
};

// Error handling utilities
export class ApprovalError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public errorType?: string
  ) {
    super(message);
    this.name = "ApprovalError";
  }
}

// Hook for React components
export const useApprovalApi = () => {
  return {
    approvalApi,
    RoleUtils,
    ApprovalError,
  };
};
