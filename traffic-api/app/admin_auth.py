
import os
import secrets

import httpx
from dotenv import load_dotenv
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials


# 환경변수 읽기
load_dotenv()

# Authorization: Bearer 토큰을 확인하는 도구
bearer_scheme = HTTPBearer(auto_error=False)


# 로그인 사용자와 관리자 권한 확인
async def require_admin(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer_scheme
    )
):

    # 1. 로그인 토큰이 없으면 차단
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="관리자 로그인이 필요합니다."
        )

    # 2. 서버 인증 설정 확인
    supabase_url = os.getenv("SUPABASE_URL", "").rstrip("/")
    supabase_api_key = os.getenv("SUPABASE_ANON_KEY", "")
    admin_user_id = os.getenv("ADMIN_USER_ID", "")

    if not supabase_url or not supabase_api_key or not admin_user_id:
        raise HTTPException(
            status_code=503,
            detail="관리자 인증 설정이 완료되지 않았습니다."
        )

    # 3. Supabase Auth에 로그인 토큰 검증 요청
    headers = {
        "apikey": supabase_api_key,
        "Authorization": "Bearer " + credentials.credentials
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:

            response = await client.get(
                supabase_url + "/auth/v1/user",
                headers=headers
            )

    except httpx.RequestError:
        raise HTTPException(
            status_code=503,
            detail="인증 서버에 연결할 수 없습니다."
        )

    # 4. 유효하지 않은 토큰 차단
    if response.status_code in (401, 403):
        raise HTTPException(
            status_code=401,
            detail="로그인이 유효하지 않습니다."
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=503,
            detail="관리자 인증을 확인할 수 없습니다."
        )

    try:
        user_data = response.json()
    except ValueError:
        raise HTTPException(
            status_code=503,
            detail="인증 서버 응답이 올바르지 않습니다."
        )

    # 5. 로그인한 사용자의 UID 확인
    current_user_id = user_data.get("id")

    if not isinstance(current_user_id, str):
        raise HTTPException(
            status_code=401,
            detail="사용자 정보를 확인할 수 없습니다."
        )

    # 6. 미리 허용한 관리자 UID와 비교
    if not secrets.compare_digest(
        current_user_id,
        admin_user_id
    ):
        raise HTTPException(
            status_code=403,
            detail="관리자 권한이 없습니다."
        )

    # 인증과 권한 확인 성공
    return {
        "id": current_user_id,
        "email": user_data.get("email")
    }
