# backend/src/app.py
# Main application entry point
# Example: FastAPI app instance

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from .routes import auth, schools, students, grades, applications, test, permissions, encryption, websocket, dashboard, invitations, approval
from .config import settings
from .utils.encryption import security_validator, security_audit_logger
from .exceptions.exception_handlers import register_exception_handlers
from .dto.base_dto import APIResponse
import logging
import time

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Jeju High School Admission API",
    description="보안이 강화된 제주도 고등학교 입학 관리 시스템",
    version="1.0.0"
)

# 보안 미들웨어 설정
if not settings.DEVELOPMENT_MODE:
    app.add_middleware(
        TrustedHostMiddleware, 
        allowed_hosts=settings.ALLOWED_HOSTS
    )

# CORS 설정 (보안 강화)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# 보안 헤더 미들웨어
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    
    # 보안 헤더 추가
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    # HTTPS 강제 (프로덕션 환경)
    if settings.FORCE_HTTPS:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    return response

# HTTPS 강제 미들웨어
@app.middleware("http")
async def enforce_https(request: Request, call_next):
    if settings.FORCE_HTTPS and not settings.DEVELOPMENT_MODE:
        # 민감한 데이터가 포함된 엔드포인트에서 HTTPS 강제
        sensitive_paths = ["/students", "/grades", "/applications", "/auth"]
        
        if any(request.url.path.startswith(path) for path in sensitive_paths):
            is_valid, errors = security_validator.validate_data_transmission_security(dict(request.headers))
            if not is_valid:
                security_audit_logger.log_security_violation(
                    user_id="unknown",
                    violation_type="HTTPS_REQUIRED",
                    details="; ".join(errors),
                    ip_address=request.client.host if request.client else ""
                )
                raise HTTPException(
                    status_code=status.HTTP_426_UPGRADE_REQUIRED,
                    detail="HTTPS required for sensitive data transmission"
                )
    
    return await call_next(request)

# 요청 로깅 미들웨어
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # 요청 로깅
    logger.info(f"Request: {request.method} {request.url.path} from {request.client.host if request.client else 'unknown'}")
    
    response = await call_next(request)
    
    # 응답 시간 로깅
    process_time = time.time() - start_time
    logger.info(f"Response: {response.status_code} in {process_time:.4f}s")
    
    return response

# 전역 예외 핸들러 등록
register_exception_handlers(app)

app.include_router(auth.router)
app.include_router(invitations.router)
app.include_router(approval.router)
app.include_router(permissions.router)
app.include_router(dashboard.router)
app.include_router(schools.router)
app.include_router(students.router)
app.include_router(grades.router)
app.include_router(applications.router)
app.include_router(encryption.router)
app.include_router(websocket.router)
app.include_router(test.router)

@app.get("/")
async def read_root():
    return {"message": "Welcome to the Jeju High School Admission API"}

# WebSocket 백그라운드 태스크 시작
@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 시 백그라운드 태스크 시작"""
    from .services.websocket_service import websocket_background_tasks
    import asyncio
    
    # WebSocket 백그라운드 태스크 시작
    asyncio.create_task(websocket_background_tasks())
    logger.info("WebSocket background tasks started")
