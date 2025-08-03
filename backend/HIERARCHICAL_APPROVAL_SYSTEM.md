# 계층적 승인 시스템 (Hierarchical Approval System)

## 개요

계층적 승인 시스템은 사용자 역할에 따라 차별화된 승인 권한을 제공하는 시스템입니다. 이 시스템은 학교 관리 구조를 반영하여 개발자/관리자가 부장교사를 승인하고, 부장교사가 같은 학교의 담임교사와 일반교사를 승인할 수 있도록 설계되었습니다.

## 승인 구조

### 계층적 승인 흐름

```
개발자/관리자 ──→ 3학년 부장 승인
    ↓
3학년 부장 ──→ 3학년 담임/일반교사 승인 (같은 학교만)
```

### 사용자 역할 체계 (5단계)

| 등급 | 역할                              | 권한      | 승인 가능 대상       | 가입 방식           |
| ---- | --------------------------------- | --------- | -------------------- | ------------------- |
| 1    | 개발자 (developer)                | 최고 권한 | 3학년 부장           | 시스템 생성 시 설정 |
| 2    | 관리자 (admin)                    | 전체 관리 | 3학년 부장           | 개발자가 승격       |
| 3    | 3학년 부장 (third_grade_head)     | 학교 관리 | 3학년 담임, 일반교사 | 가입 시 선택        |
| 4    | 3학년 담임 (third_grade_homeroom) | 반 관리   | 없음                 | 가입 시 선택        |
| 5    | 일반교사 (general_teacher)        | 열람 전용 | 없음                 | 가입 시 선택        |

## 주요 기능

### 1. 계층적 승인 검증

- **권한 기반 승인**: 사용자 역할에 따라 승인 가능한 대상 제한
- **학교 코드 검증**: 3학년 부장은 같은 학교 소속 교사만 승인 가능
- **실시간 권한 확인**: 승인 요청 시 실시간으로 권한 검증

### 2. 승인 상태 관리

- **승인 대기 (pending)**: 회원가입 후 초기 상태
- **승인 완료 (approved)**: 권한자가 승인한 상태
- **승인 거부 (rejected)**: 권한자가 거부한 상태

### 3. 승인 로그 및 알림

- **승인 이력 추적**: 모든 승인/거부 행위 로그 기록
- **알림 시스템**: 승인/거부 시 대상 사용자에게 알림 전송
- **감사 추적**: 승인자, 대상자, 시간, 사유 등 상세 정보 기록

## API 엔드포인트

### 승인 관리 API (`/api/approval`)

#### 1. 승인 대기 사용자 조회

```http
GET /api/approval/pending-users
Authorization: Bearer {token}
```

**응답 예시:**

```json
[
  {
    "uid": "user-123",
    "username": "teacher1",
    "email": "teacher1@school.com",
    "full_name": "김교사",
    "role": "third_grade_homeroom",
    "school_id": "school-1",
    "grade": 3,
    "class_number": 1,
    "is_homeroom_teacher": true,
    "created_at": "2024-01-01T00:00:00",
    "is_approved": false
  }
]
```

#### 2. 사용자 승인/거부

```http
POST /api/approval/approve-user
Authorization: Bearer {token}
Content-Type: application/json

{
  "target_uid": "user-123",
  "is_approved": true,
  "rejection_reason": "자격 요건 미충족" // 거부 시에만
}
```

**응답 예시:**

```json
{
  "success": true,
  "message": "사용자가 승인되었습니다.",
  "target_uid": "user-123",
  "target_email": "teacher1@school.com",
  "is_approved": true,
  "approved_by": "approver-uid",
  "approved_at": "2024-01-01T12:00:00"
}
```

#### 3. 승인 통계 조회

```http
GET /api/approval/statistics
Authorization: Bearer {token}
```

**응답 예시:**

```json
{
  "pending_count": 5,
  "approved_count": 23,
  "rejected_count": 2,
  "total_processed": 25
}
```

#### 4. 승인 이력 조회

```http
GET /api/approval/history
Authorization: Bearer {token}
```

**응답 예시:**

```json
[
  {
    "id": "log-123",
    "approver_uid": "approver-uid",
    "target_uid": "user-123",
    "action": "approved",
    "reason": null,
    "created_at": "2024-01-01T12:00:00"
  }
]
```

#### 5. 승인 규칙 조회 (공개)

```http
GET /api/approval/approval-rules
```

**응답 예시:**

```json
{
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
```

## 데이터베이스 구조

### 사용자 컬렉션 (users)

```json
{
  "uid": "user-123",
  "email": "teacher@school.com",
  "username": "teacher1",
  "full_name": "김교사",
  "role": "third_grade_homeroom",
  "school_id": "school-1",
  "grade": 3,
  "class_number": 1,
  "is_homeroom_teacher": true,
  "is_active": true,
  "is_approved": false,
  "approved_by": "approver-uid",
  "approved_at": "2024-01-01T12:00:00",
  "rejection_reason": "자격 요건 미충족",
  "rejected_at": "2024-01-01T12:00:00",
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T12:00:00"
}
```

### 승인 로그 컬렉션 (approval_logs)

```json
{
  "id": "log-123",
  "approver_uid": "approver-uid",
  "target_uid": "user-123",
  "action": "approved",
  "reason": "자격 요건 미충족",
  "created_at": "2024-01-01T12:00:00"
}
```

### 알림 컬렉션 (notifications)

```json
{
  "id": "notification-123",
  "user_uid": "user-123",
  "user_email": "teacher@school.com",
  "type": "approval_status",
  "is_approved": true,
  "message": "계정이 승인되었습니다.",
  "created_at": "2024-01-01T12:00:00",
  "is_read": false
}
```

## 보안 고려사항

### 1. 권한 검증

- 모든 승인 요청에 대해 실시간 권한 검증
- JWT 토큰을 통한 사용자 인증
- 역할 기반 접근 제어 (RBAC)

### 2. 학교 코드 검증

- 3학년 부장의 경우 같은 학교 소속 교사만 승인 가능
- 학교 ID 일치 여부 실시간 확인
- 크로스 스쿨 승인 방지

### 3. 감사 추적

- 모든 승인/거부 행위 로그 기록
- 승인자, 대상자, 시간, 사유 등 상세 정보 저장
- 변경 불가능한 로그 구조

## 프론트엔드 컴포넌트

### HierarchicalApprovalDashboard

- 계층적 승인 관리 대시보드
- 승인 가능한 사용자만 표시
- 실시간 통계 및 이력 조회
- 승인/거부 처리 및 사유 입력

### 주요 기능

1. **승인 대기 목록**: 권한에 따라 필터링된 사용자 목록
2. **승인 통계**: 대기, 승인, 거부 건수 표시
3. **승인 이력**: 과거 승인/거부 이력 타임라인
4. **권한 표시**: 승인 가능 여부 실시간 표시

## 사용 예시

### 1. 개발자가 3학년 부장 승인

```typescript
const approvalRequest = {
  target_uid: "head-teacher-uid",
  is_approved: true,
};

const result = await approvalApi.approveUser(approvalRequest, token);
console.log(result.message); // "사용자가 승인되었습니다."
```

### 2. 3학년 부장이 담임교사 거부

```typescript
const rejectionRequest = {
  target_uid: "homeroom-teacher-uid",
  is_approved: false,
  rejection_reason: "자격 요건 미충족",
};

const result = await approvalApi.approveUser(rejectionRequest, token);
console.log(result.message); // "사용자가 거부되었습니다."
```

### 3. 승인 통계 조회

```typescript
const stats = await approvalApi.getApprovalStatistics(token);
console.log(`대기: ${stats.pending_count}, 승인: ${stats.approved_count}`);
```

## 테스트

### 단위 테스트

- `test_approval_system.py`: 승인 서비스 로직 테스트
- `test_approval_routes.py`: API 엔드포인트 테스트

### 통합 테스트

- 계층적 승인 플로우 전체 테스트
- 학교 코드 검증 테스트
- 권한 기반 접근 제어 테스트

### 테스트 실행

```bash
# 백엔드 테스트
cd backend
python test_approval_functionality.py

# 단위 테스트 (pytest 설치 필요)
python -m pytest tests/test_approval_system.py -v
python -m pytest tests/test_approval_routes.py -v
```

## 배포 및 운영

### 환경 변수

```env
# Firebase 설정
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_PRIVATE_KEY=your-private-key
FIREBASE_CLIENT_EMAIL=your-client-email

# 개발 모드
DEVELOPMENT_MODE=false
```

### 모니터링

- 승인 처리 시간 모니터링
- 승인 거부율 추적
- 오류 발생률 모니터링

### 백업 및 복구

- 승인 로그 정기 백업
- 사용자 데이터 백업
- 재해 복구 계획

## 향후 개선 사항

1. **이메일 알림**: 승인/거부 시 이메일 자동 발송
2. **일괄 승인**: 여러 사용자 동시 승인 기능
3. **승인 위임**: 부재 시 승인 권한 위임 기능
4. **자동 승인**: 특정 조건 만족 시 자동 승인
5. **승인 만료**: 일정 기간 후 승인 요청 자동 만료

## 문제 해결

### 자주 발생하는 문제

1. **권한 없음 오류**

   - 사용자 역할 확인
   - 학교 ID 일치 여부 확인

2. **승인 처리 실패**

   - 네트워크 연결 확인
   - Firebase 연결 상태 확인

3. **통계 불일치**
   - 캐시 새로고침
   - 데이터베이스 동기화 확인

### 로그 확인

```bash
# 승인 관련 로그 확인
grep "approval" backend/logs/app.log

# 오류 로그 확인
grep "ERROR" backend/logs/app.log | grep "approval"
```

## 연락처

개발팀: dev@school-system.com
시스템 관리자: admin@school-system.com
