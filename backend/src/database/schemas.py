# backend/src/database/schemas.py
# Data validation and serialization/deserialization schemas (Pydantic models)

from pydantic import BaseModel, EmailStr, validator, model_validator
from typing import Optional, List
from .models import UserRole
from ..utils.constants import UserRoleGroups

# --- User Schemas ---

class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    school_id: Optional[str] = None  # 소속 학교 ID
    grade: Optional[int] = None  # 담당 학년 (담임교사의 경우)
    class_number: Optional[int] = None  # 담당 반 (담임교사의 경우)
    is_homeroom_teacher: Optional[bool] = None  # 3학년 부장이 담임도 겸하는지 여부

class UserCreate(UserBase):
    password: str # Password is used for Firebase Auth creation, not stored in Firestore
    role: UserRole = UserRole.THIRD_GRADE_HOMEROOM # Default role for new users (3학년 담임)
    school_name: Optional[str] = None  # 회원가입 시 학교명으로 선택
    is_homeroom_teacher: Optional[bool] = None  # 3학년 부장이 담임도 겸하는지 여부
    
    @validator('role')
    def validate_selectable_role(cls, v):
        """가입 시 선택 가능한 역할인지 검증"""
        if v not in UserRoleGroups.SELECTABLE_ROLES:
            raise ValueError(f'가입 시 선택할 수 없는 역할입니다: {v}')
        return v
    
    @model_validator(mode='after')
    def validate_role_based_fields(self):
        """역할별 차별화된 필드 검증"""
        role = self.role
        is_homeroom_teacher = self.is_homeroom_teacher
        grade = self.grade
        class_number = self.class_number
        
        if role == UserRole.THIRD_GRADE_HEAD:
            # 3학년 부장: 담임 여부 선택 필수
            if is_homeroom_teacher is None:
                raise ValueError('3학년 부장은 담임 겸임 여부를 선택해야 합니다')
            
            # 담임을 겸하는 경우 학년/반 정보 필수
            if is_homeroom_teacher:
                if grade is None:
                    raise ValueError('담임을 겸하는 3학년 부장은 담당 학년을 입력해야 합니다')
                if grade != 3:
                    raise ValueError('현재는 3학년만 지원합니다')
                if class_number is None:
                    raise ValueError('담임을 겸하는 3학년 부장은 담당 반을 입력해야 합니다')
                if class_number < 1 or class_number > 20:
                    raise ValueError('반 번호는 1-20 사이여야 합니다')
            else:
                # 담임을 겸하지 않는 경우 학급 정보는 None이어야 함
                if grade is not None or class_number is not None:
                    raise ValueError('담임을 겸하지 않는 3학년 부장은 학급 정보를 입력하지 않아야 합니다')
        
        elif role == UserRole.THIRD_GRADE_HOMEROOM:
            # 3학년 담임: 필수 학년/반 입력
            if grade is None:
                raise ValueError('3학년 담임은 담당 학년을 입력해야 합니다')
            if grade != 3:
                raise ValueError('현재는 3학년만 지원합니다')
            if class_number is None:
                raise ValueError('3학년 담임은 담당 반을 입력해야 합니다')
            if class_number < 1 or class_number > 20:
                raise ValueError('반 번호는 1-20 사이여야 합니다')
            # 3학년 담임은 항상 담임교사
            self.is_homeroom_teacher = True
        
        elif role == UserRole.GENERAL_TEACHER:
            # 일반교사: 학급 정보 입력 없음
            if grade is not None or class_number is not None or is_homeroom_teacher is not None:
                raise ValueError('일반교사는 학급 정보나 담임 여부를 입력하지 않아야 합니다')
            # 일반교사는 학급 정보 모두 None으로 설정
            self.grade = None
            self.class_number = None
            self.is_homeroom_teacher = None
        
        return self

class UserUpdateRole(BaseModel):
    role: UserRole

class UserInDB(UserBase):
    uid: str      # Firebase Authentication User ID
    is_active: bool
    role: UserRole
    is_approved: bool = False  # 관리자 승인 여부
    created_at: str
    updated_at: str

class UserApproval(BaseModel):
    """사용자 승인 관련 스키마 (레거시)"""
    uid: str
    is_approved: bool
    role: Optional[UserRole] = None

class HierarchicalApprovalRequest(BaseModel):
    """계층적 승인 요청 스키마"""
    target_uid: str
    is_approved: bool
    rejection_reason: Optional[str] = None

class ApprovalLog(BaseModel):
    """승인 로그 스키마"""
    id: str
    approver_uid: str
    target_uid: str
    action: str  # "approved" | "rejected"
    reason: Optional[str] = None
    created_at: str
    
    class Config:
        from_attributes = True

class ApprovalStatistics(BaseModel):
    """승인 통계 스키마"""
    pending_count: int
    approved_count: int
    rejected_count: int
    total_processed: int

class ApprovalNotification(BaseModel):
    """승인 알림 스키마"""
    id: str
    user_uid: str
    user_email: str
    type: str  # "approval_status"
    is_approved: bool
    message: str
    created_at: str
    is_read: bool = False
    
    class Config:
        from_attributes = True

# --- Invitation Link Schemas ---

class InvitationLinkBase(BaseModel):
    """초대 링크 기본 스키마"""
    school_id: str
    invited_role: UserRole
    expires_at: str  # ISO 형식 날짜
    is_active: bool = True

class InvitationLinkCreate(InvitationLinkBase):
    """초대 링크 생성 스키마"""
    pass

class InvitationLink(InvitationLinkBase):
    """초대 링크 응답 스키마"""
    id: str  # Firestore document ID
    code: str  # 고유 초대 코드
    created_by: str  # 생성자 UID
    created_at: str  # ISO 형식 날짜
    used_count: int = 0  # 사용된 횟수
    max_uses: Optional[int] = None  # 최대 사용 횟수 (None이면 무제한)
    
    class Config:
        from_attributes = True

class InvitationLinkValidation(BaseModel):
    """초대 링크 유효성 검증 응답"""
    is_valid: bool
    school_id: Optional[str] = None
    school_name: Optional[str] = None
    invited_role: Optional[UserRole] = None
    expires_at: Optional[str] = None
    error_message: Optional[str] = None

class UserCreateWithInvitation(UserCreate):
    """초대 링크를 통한 회원가입 스키마"""
    invitation_code: str  # 초대 코드
    
    # 초대 링크 사용 시 학교 정보는 자동 매핑되므로 school_name 제거
    school_name: Optional[str] = None
    
    @model_validator(mode='after')
    def validate_invitation_signup(self):
        """초대 링크 회원가입 시 검증"""
        # 초대 코드가 있으면 학교명은 무시 (자동 매핑)
        if self.invitation_code:
            self.school_name = None
        
        # 부모 클래스의 역할별 검증도 수행
        return super().validate_role_based_fields()

# --- Other Schemas ---

class StudentBase(BaseModel):
    name: str  # 암호화된 학생 이름
    student_id_number: str
    homeroom_teacher_id: Optional[str] = None # Should be teacher's UID (string)

class StudentCreate(StudentBase):
    # 엑셀 파일에서 읽어온 원본 데이터
    grade: int  # A열: 학년
    class_number: int  # B열: 반
    number: int  # C열: 번호
    name_encrypted: str  # D열: 성명 (암호화됨)
    gender_encrypted: str  # E열: 성별 (암호화됨)
    percentile_rank_encrypted: str  # O열: 내신석차백분율 (암호화됨)
    school_id: str  # 소속 중학교 ID (부장교사의 학교와 매칭)

class StudentFromExcel(BaseModel):
    """엑셀 파일에서 읽어온 학생 데이터"""
    grade: int  # A열: 학년
    class_number: int  # B열: 반
    number: int  # C열: 번호
    name: str  # D열: 성명 (원본)
    gender: str  # E열: 성별 (원본)
    percentile_rank: float  # O열: 내신석차백분율 (원본)

class Student(StudentBase):
    id: str # Firestore document ID
    grade: int
    class_number: int
    number: int
    gender_encrypted: str  # 암호화된 성별
    percentile_rank_encrypted: str  # 암호화된 내신석차백분율
    school_id: str  # 소속 중학교 ID
    created_at: str  # ISO 형식 날짜
    updated_at: str  # ISO 형식 날짜
    
    class Config:
        from_attributes = True # Updated from orm_mode for Pydantic V2

class StudentDecrypted(BaseModel):
    """복호화된 학생 정보 (권한이 있는 교사만 볼 수 있음)"""
    id: str
    name: str  # 복호화된 이름
    grade: int
    class_number: int
    number: int
    gender: str  # 복호화된 성별
    percentile_rank: float  # 복호화된 내신석차백분율
    school_id: str
    homeroom_teacher_id: Optional[str] = None

class SchoolBase(BaseModel):
    name: str
    address: Optional[str] = None
    departments: Optional[List[str]] = None  # 학과 목록 (문자열 배열)

class SchoolCreate(SchoolBase):
    # 학교 생성 시 필요한 추가 정보
    total_quota: int = 0  # 전체 정원
    gender_type: str = "COED"  # COED, BOYS, GIRLS
    is_levelized: bool = False  # 평준화 일반고 여부

class School(SchoolBase):
    id: str # Firestore document ID
    
    # 정원 관리
    total_quota: int  # 전체 정원 (관리자가 실시간 수정 가능)
    priority_within_quota: int = 0  # 정원내 우선선발 인원
    priority_outside_quota: int = 0  # 정원외 우선선발 인원
    actual_competition_quota: int  # 실제 경쟁 정원 (계산됨)
    
    # 학교 유형
    gender_type: str  # COED(남녀공학), BOYS(남학교), GIRLS(여학교)
    is_levelized: bool  # 평준화 일반고 여부
    
    # 메타데이터
    created_at: str  # ISO 형식 날짜
    updated_at: str  # ISO 형식 날짜
    
    class Config:
        from_attributes = True

class SchoolQuotaUpdate(BaseModel):
    """학교 정원 정보 업데이트 (관리자 전용)"""
    total_quota: Optional[int] = None
    priority_within_quota: Optional[int] = None
    priority_outside_quota: Optional[int] = None

class GradeBase(BaseModel):
    subject: str
    score: int

class GradeCreate(GradeBase):
    student_id: str # Firestore document ID of the student

class Grade(GradeBase):
    id: str # Firestore document ID
    student_id: str
    class Config:
        from_attributes = True

class StudentApplicationBase(BaseModel):
    student_id: str # Firestore document ID of the student
    school_id: Optional[str] = None # Firestore document ID of the school
    department_name: Optional[str] = None # 지원 학과명
    is_accepted: bool = False

class StudentApplicationCreate(StudentApplicationBase):
    # 우선선발 정보
    is_priority_selection: bool = False
    priority_type: Optional[str] = None  # "WITHIN_QUOTA" | "OUTSIDE_QUOTA"
    priority_category: Optional[str] = None  # 체육특기자, 농어촌 등

class StudentApplication(StudentApplicationBase):
    id: str # Firestore document ID
    
    # 우선선발 정보
    is_priority_selection: bool = False
    priority_type: Optional[str] = None
    priority_category: Optional[str] = None
    
    # 순위 정보
    rank_in_school: Optional[int] = None
    percentile_rank: Optional[float] = None
    
    # 메타데이터
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True

class StudentPercentileGrade(BaseModel):
    name: str
    percentile: float

class SchoolApplication(BaseModel):
    student_name: str
    school_name: str
    percentile: float

class SchoolApplicationCreate(SchoolApplication):
    pass

class SchoolApplicationResponse(SchoolApplication):
    id: str
    created_at: str

class SchoolStatistics(BaseModel):
    school_name: str
    application_count: int
    students: list[str]

# 지원 현황 대시보드 관련 스키마
class StudentRanking(BaseModel):
    """학생 순위 정보"""
    student_id: str
    student_name: str  # 암호화된 상태 (클라이언트에서 복호화)
    rank: int
    percentile_rank: float
    is_priority_selection: bool
    priority_type: Optional[str] = None
    priority_category: Optional[str] = None
    school_name: str  # 소속 중학교명
    grade: int
    class_number: int
    number: int

class CompetitionStatistics(BaseModel):
    """경쟁 통계 정보"""
    total_applicants: int
    general_applicants: int
    priority_within_applicants: int
    priority_outside_applicants: int
    competition_ratio: float

class CompetitionStatus(BaseModel):
    """학교별 지원 현황 요약"""
    school_id: str
    school_name: str
    total_quota: int
    priority_within_quota: int
    priority_outside_quota: int
    actual_competition_quota: int
    statistics: CompetitionStatistics

class CompetitionStatusDetail(BaseModel):
    """특정 학교의 상세 지원 현황"""
    school: School
    statistics: CompetitionStatistics
    rankings: List[StudentRanking]
    last_updated: str

