import React, { useState, useEffect } from "react";
import {
  Table,
  Button,
  Tag,
  Space,
  Modal,
  Input,
  message,
  Card,
  Typography,
  Tooltip,
  Badge,
  Statistic,
  Row,
  Col,
  Alert,
  Divider,
  Timeline,
} from "antd";
import {
  CheckOutlined,
  CloseOutlined,
  UserOutlined,
  BankOutlined,
  ClockCircleOutlined,
  InfoCircleOutlined,
  HistoryOutlined,
  TeamOutlined,
  ExclamationCircleOutlined,
} from "@ant-design/icons";
import type { ColumnsType } from "antd/es/table";

const { Title, Text } = Typography;
const { TextArea } = Input;

interface PendingUser {
  uid: string;
  username: string;
  email: string;
  full_name: string;
  role: string;
  school_id?: string;
  grade?: number;
  class_number?: number;
  created_at: string;
  is_homeroom_teacher?: boolean;
}

interface ApprovalStatistics {
  pending_count: number;
  approved_count: number;
  rejected_count: number;
  total_processed: number;
}

interface ApprovalHistory {
  id: string;
  approver_uid: string;
  target_uid: string;
  action: string;
  reason?: string;
  created_at: string;
}

interface ApprovalRules {
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

interface HierarchicalApprovalDashboardProps {
  token: string;
  currentUser: {
    role: string;
    school_id?: string;
    full_name: string;
  };
}

const HierarchicalApprovalDashboard: React.FC<
  HierarchicalApprovalDashboardProps
> = ({ token, currentUser }) => {
  const [pendingUsers, setPendingUsers] = useState<PendingUser[]>([]);
  const [statistics, setStatistics] = useState<ApprovalStatistics | null>(null);
  const [history, setHistory] = useState<ApprovalHistory[]>([]);
  const [approvalRules, setApprovalRules] = useState<ApprovalRules | null>(
    null
  );
  const [loading, setLoading] = useState(true);
  const [approvalLoading, setApprovalLoading] = useState<string | null>(null);
  const [modalVisible, setModalVisible] = useState(false);
  const [historyModalVisible, setHistoryModalVisible] = useState(false);
  const [selectedUser, setSelectedUser] = useState<PendingUser | null>(null);
  const [rejectionReason, setRejectionReason] = useState("");
  const [activeTab, setActiveTab] = useState("pending");

  // 승인 규칙 조회 (공개 엔드포인트)
  const fetchApprovalRules = async () => {
    try {
      const response = await fetch("/api/approval/approval-rules");
      if (response.ok) {
        const rules = await response.json();
        setApprovalRules(rules);
      }
    } catch (error) {
      console.error("Failed to fetch approval rules:", error);
    }
  };

  // 승인 대기 사용자 목록 조회 (계층적)
  const fetchPendingUsers = async () => {
    setLoading(true);
    try {
      const response = await fetch("/api/approval/pending-users", {
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      });

      if (response.ok) {
        const users = await response.json();
        setPendingUsers(users);
      } else if (response.status === 403) {
        message.warning("승인 권한이 없습니다.");
        setPendingUsers([]);
      } else {
        message.error("승인 대기 사용자 목록을 불러오는데 실패했습니다.");
      }
    } catch (error) {
      console.error("Failed to fetch pending users:", error);
      message.error("승인 대기 사용자 목록을 불러오는데 실패했습니다.");
    } finally {
      setLoading(false);
    }
  };

  // 승인 통계 조회
  const fetchStatistics = async () => {
    try {
      const response = await fetch("/api/approval/statistics", {
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      });

      if (response.ok) {
        const stats = await response.json();
        setStatistics(stats);
      }
    } catch (error) {
      console.error("Failed to fetch statistics:", error);
    }
  };

  // 승인 이력 조회
  const fetchHistory = async () => {
    try {
      const response = await fetch("/api/approval/history", {
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      });

      if (response.ok) {
        const historyData = await response.json();
        setHistory(historyData);
      }
    } catch (error) {
      console.error("Failed to fetch history:", error);
    }
  };

  useEffect(() => {
    fetchApprovalRules();
    fetchPendingUsers();
    fetchStatistics();
    fetchHistory();
  }, [token]);

  // 계층적 사용자 승인/거부 처리
  const handleHierarchicalApproval = async (
    uid: string,
    isApproved: boolean,
    rejectionReason?: string
  ) => {
    setApprovalLoading(uid);

    try {
      const response = await fetch("/api/approval/approve-user", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          target_uid: uid,
          is_approved: isApproved,
          rejection_reason: rejectionReason || undefined,
        }),
      });

      if (response.ok) {
        const result = await response.json();
        message.success(result.message);

        // 목록에서 해당 사용자 제거 및 통계 업데이트
        setPendingUsers((prev) => prev.filter((user) => user.uid !== uid));
        fetchStatistics();
        fetchHistory();
        setModalVisible(false);
        setSelectedUser(null);
        setRejectionReason("");
      } else {
        const errorData = await response.json();
        message.error(errorData.detail || "처리 중 오류가 발생했습니다.");
      }
    } catch (error) {
      console.error("Approval error:", error);
      message.error("처리 중 오류가 발생했습니다.");
    } finally {
      setApprovalLoading(null);
    }
  };

  // 승인 모달 열기
  const openApprovalModal = (user: PendingUser, isApproval: boolean) => {
    setSelectedUser(user);
    setModalVisible(true);
    if (!isApproval) {
      setRejectionReason("");
    }
  };

  // 역할 표시 함수 (새로운 역할 체계 반영)
  const getRoleTag = (role: string) => {
    const roleMap = {
      developer: { color: "purple", text: "개발자" },
      admin: { color: "red", text: "관리자" },
      third_grade_head: { color: "blue", text: "3학년 부장" },
      third_grade_homeroom: { color: "green", text: "3학년 담임" },
      general_teacher: { color: "orange", text: "일반교사" },
      // 레거시 호환성
      head_teacher: { color: "blue", text: "부장교사" },
      homeroom_teacher: { color: "green", text: "담임교사" },
    };

    const roleInfo = roleMap[role as keyof typeof roleMap] || {
      color: "default",
      text: role,
    };
    return <Tag color={roleInfo.color}>{roleInfo.text}</Tag>;
  };

  // 승인 가능 여부 확인
  const canApproveUser = (user: PendingUser): boolean => {
    if (!approvalRules) return false;

    const { hierarchy } = approvalRules;

    // Level 1: Developer/Admin can approve 3학년 부장
    if (
      hierarchy.level_1.roles.includes(currentUser.role) &&
      hierarchy.level_1.can_approve.includes(user.role)
    ) {
      return true;
    }

    // Level 2: 3학년 부장 can approve 3학년 담임/일반교사 (same school only)
    if (
      hierarchy.level_2.roles.includes(currentUser.role) &&
      hierarchy.level_2.can_approve.includes(user.role)
    ) {
      // Check same school restriction
      return currentUser.school_id === user.school_id;
    }

    return false;
  };

  // 테이블 컬럼 정의
  const columns: ColumnsType<PendingUser> = [
    {
      title: "사용자 정보",
      key: "userInfo",
      render: (_, record) => (
        <Space direction="vertical" size="small">
          <div>
            <UserOutlined /> <strong>{record.full_name}</strong> (
            {record.username})
          </div>
          <div style={{ color: "#666", fontSize: "12px" }}>{record.email}</div>
        </Space>
      ),
    },
    {
      title: "역할",
      dataIndex: "role",
      key: "role",
      render: (role) => getRoleTag(role),
    },
    {
      title: "학교/학급 정보",
      key: "schoolInfo",
      render: (_, record) => (
        <Space direction="vertical" size="small">
          {record.school_id && (
            <div>
              <BankOutlined /> 학교 ID: {record.school_id}
            </div>
          )}
          {record.grade && record.class_number && (
            <div style={{ fontSize: "12px", color: "#666" }}>
              {record.grade}학년 {record.class_number}반
              {record.is_homeroom_teacher && " (담임)"}
            </div>
          )}
        </Space>
      ),
    },
    {
      title: "신청일",
      dataIndex: "created_at",
      key: "created_at",
      render: (date) => (
        <Tooltip title={new Date(date).toLocaleString()}>
          <div>
            <ClockCircleOutlined /> {new Date(date).toLocaleDateString()}
          </div>
        </Tooltip>
      ),
    },
    {
      title: "승인 가능",
      key: "canApprove",
      render: (_, record) => {
        const canApprove = canApproveUser(record);
        return canApprove ? (
          <Tag color="green">승인 가능</Tag>
        ) : (
          <Tooltip title="승인 권한이 없거나 다른 학교 소속입니다">
            <Tag color="red">승인 불가</Tag>
          </Tooltip>
        );
      },
    },
    {
      title: "작업",
      key: "actions",
      render: (_, record) => {
        const canApprove = canApproveUser(record);
        return (
          <Space>
            <Button
              type="primary"
              icon={<CheckOutlined />}
              size="small"
              loading={approvalLoading === record.uid}
              disabled={!canApprove}
              onClick={() => openApprovalModal(record, true)}
            >
              승인
            </Button>
            <Button
              danger
              icon={<CloseOutlined />}
              size="small"
              loading={approvalLoading === record.uid}
              disabled={!canApprove}
              onClick={() => openApprovalModal(record, false)}
            >
              거부
            </Button>
          </Space>
        );
      },
    },
  ];

  return (
    <div className="p-6">
      {/* 통계 카드 */}
      {statistics && (
        <Row gutter={16} className="mb-6">
          <Col span={6}>
            <Card>
              <Statistic
                title="승인 대기"
                value={statistics.pending_count}
                prefix={<ClockCircleOutlined />}
                valueStyle={{ color: "#faad14" }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="승인 완료"
                value={statistics.approved_count}
                prefix={<CheckOutlined />}
                valueStyle={{ color: "#52c41a" }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="승인 거부"
                value={statistics.rejected_count}
                prefix={<CloseOutlined />}
                valueStyle={{ color: "#ff4d4f" }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="총 처리"
                value={statistics.total_processed}
                prefix={<TeamOutlined />}
                valueStyle={{ color: "#1890ff" }}
              />
            </Card>
          </Col>
        </Row>
      )}

      {/* 승인 규칙 안내 */}
      {approvalRules && (
        <Alert
          message="계층적 승인 규칙"
          description={
            <div>
              <p>현재 승인 구조:</p>
              <ul>
                {approvalRules.approval_flow.map((flow, index) => (
                  <li key={index}>{flow}</li>
                ))}
              </ul>
              <p className="mt-2">
                <ExclamationCircleOutlined /> 3학년 부장은 같은 학교 소속 교사만
                승인할 수 있습니다.
              </p>
            </div>
          }
          type="info"
          showIcon
          className="mb-6"
        />
      )}

      {/* 메인 테이블 */}
      <Card>
        <div className="flex justify-between items-center mb-6">
          <div>
            <Title level={3}>
              <Badge count={pendingUsers.length} offset={[10, 0]}>
                계층적 승인 관리
              </Badge>
            </Title>
            <p className="text-gray-600">
              권한에 따라 승인 가능한 사용자들을 관리합니다.
            </p>
          </div>
          <Space>
            <Button
              icon={<HistoryOutlined />}
              onClick={() => setHistoryModalVisible(true)}
            >
              승인 이력
            </Button>
            <Button onClick={fetchPendingUsers} loading={loading}>
              새로고침
            </Button>
          </Space>
        </div>

        <Table
          columns={columns}
          dataSource={pendingUsers}
          rowKey="uid"
          loading={loading}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `총 ${total}명의 승인 대기 사용자`,
          }}
          locale={{
            emptyText: "승인 대기 중인 사용자가 없습니다.",
          }}
        />
      </Card>

      {/* 승인/거부 모달 */}
      <Modal
        title={selectedUser ? "사용자 승인/거부" : ""}
        open={modalVisible}
        onCancel={() => {
          setModalVisible(false);
          setSelectedUser(null);
          setRejectionReason("");
        }}
        footer={[
          <Button
            key="cancel"
            onClick={() => {
              setModalVisible(false);
              setSelectedUser(null);
              setRejectionReason("");
            }}
          >
            취소
          </Button>,
          <Button
            key="reject"
            danger
            loading={approvalLoading === selectedUser?.uid}
            onClick={() => {
              if (selectedUser) {
                handleHierarchicalApproval(
                  selectedUser.uid,
                  false,
                  rejectionReason
                );
              }
            }}
          >
            거부
          </Button>,
          <Button
            key="approve"
            type="primary"
            loading={approvalLoading === selectedUser?.uid}
            onClick={() => {
              if (selectedUser) {
                handleHierarchicalApproval(selectedUser.uid, true);
              }
            }}
          >
            승인
          </Button>,
        ]}
      >
        {selectedUser && (
          <div className="space-y-4">
            <div>
              <strong>사용자:</strong> {selectedUser.full_name} (
              {selectedUser.username})
            </div>
            <div>
              <strong>이메일:</strong> {selectedUser.email}
            </div>
            <div>
              <strong>신청 역할:</strong> {getRoleTag(selectedUser.role)}
            </div>
            <div>
              <strong>학교 ID:</strong> {selectedUser.school_id || "없음"}
            </div>

            {selectedUser.grade && selectedUser.class_number && (
              <div>
                <strong>담당 학급:</strong> {selectedUser.grade}학년{" "}
                {selectedUser.class_number}반
                {selectedUser.is_homeroom_teacher && " (담임)"}
              </div>
            )}

            <Divider />

            <div>
              <Text strong>거부 사유 (선택사항):</Text>
              <TextArea
                rows={3}
                value={rejectionReason}
                onChange={(e) => setRejectionReason(e.target.value)}
                placeholder="거부 시 사유를 입력하세요..."
                className="mt-2"
              />
            </div>

            <Alert
              message={
                canApproveUser(selectedUser)
                  ? "이 사용자를 승인할 권한이 있습니다."
                  : "이 사용자를 승인할 권한이 없습니다."
              }
              type={canApproveUser(selectedUser) ? "success" : "warning"}
              showIcon
            />
          </div>
        )}
      </Modal>

      {/* 승인 이력 모달 */}
      <Modal
        title="승인 이력"
        open={historyModalVisible}
        onCancel={() => setHistoryModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setHistoryModalVisible(false)}>
            닫기
          </Button>,
        ]}
        width={800}
      >
        <Timeline>
          {history.map((item) => (
            <Timeline.Item
              key={item.id}
              color={item.action === "approved" ? "green" : "red"}
              dot={
                item.action === "approved" ? (
                  <CheckOutlined />
                ) : (
                  <CloseOutlined />
                )
              }
            >
              <div>
                <strong>{item.action === "approved" ? "승인" : "거부"}</strong>{" "}
                - {new Date(item.created_at).toLocaleString()}
              </div>
              <div className="text-gray-600">대상: {item.target_uid}</div>
              {item.reason && (
                <div className="text-gray-600">사유: {item.reason}</div>
              )}
            </Timeline.Item>
          ))}
        </Timeline>
        {history.length === 0 && (
          <div className="text-center text-gray-500 py-8">
            승인 이력이 없습니다.
          </div>
        )}
      </Modal>
    </div>
  );
};

export default HierarchicalApprovalDashboard;
