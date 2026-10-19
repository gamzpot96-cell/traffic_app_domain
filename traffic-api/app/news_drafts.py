"""관리자 기사 초안에 대한 서명 및 검증.

서명 토큰은 암호화된 데이터가 아니므로 비밀정보를 넣지 않습니다.
"""
import base64
import binascii
import hashlib
import hmac
import json
import os
import secrets
import time
from uuid import uuid4


DRAFT_TTL_SECONDS = 20 * 60
MAX_TOKEN_LENGTH = 24000


def _signing_key():
    value = os.getenv("NEWS_DRAFT_SIGNING_KEY", "")
    if len(value.encode("utf-8")) < 32 or value.startswith("your_"):
        raise RuntimeError("NEWS_DRAFT_SIGNING_KEY를 32바이트 이상으로 설정하세요.")
    return value.encode("utf-8")


def _encode(raw_bytes):
    return base64.urlsafe_b64encode(raw_bytes).decode("ascii").rstrip("=")


def _decode(encoded):
    return base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4))


def create_draft_token(news_data, admin_user_id):
    """서버에서 생성된 뉴스와 관리자 ID를 서명한 저장용 증표로 반환."""
    now = int(time.time())
    generation_id = str(uuid4())
    payload = {
        "version": 1,
        "generation_id": generation_id,
        "admin_user_id": admin_user_id,
        "issued_at": now,
        "expires_at": now + DRAFT_TTL_SECONDS,
        "news": news_data
    }
    raw = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    signature = hmac.new(_signing_key(), raw, hashlib.sha256).digest()
    token = _encode(raw) + "." + _encode(signature)
    if len(token) > MAX_TOKEN_LENGTH:
        raise ValueError("생성한 기사 초안이 너무 깁니다.")
    return token, generation_id


def verify_draft_token(token, admin_user_id):
    """서명·만료 시각·관리자 소유권이 일치하는 경우에만 초안을 반환."""
    if not isinstance(token, str) or len(token) > MAX_TOKEN_LENGTH:
        raise ValueError("기사 증표 형식이 올바르지 않습니다.")
    try:
        payload_part, signature_part = token.split(".")
        raw = _decode(payload_part)
        supplied_signature = _decode(signature_part)
        expected_signature = hmac.new(
            _signing_key(), raw, hashlib.sha256
        ).digest()
        if not hmac.compare_digest(supplied_signature, expected_signature):
            raise ValueError("기사 증표의 서명이 올바르지 않습니다.")
        payload = json.loads(raw)
        if (
            not isinstance(payload, dict)
            or payload.get("version") != 1
            or not isinstance(payload.get("expires_at"), int)
            or int(time.time()) > payload["expires_at"]
            or not isinstance(payload.get("admin_user_id"), str)
            or not secrets.compare_digest(payload["admin_user_id"], admin_user_id)
            or not isinstance(payload.get("news"), dict)
        ):
            raise ValueError("기사 증표가 만료됐거나 사용할 수 없습니다.")
        from uuid import UUID
        generation_id = str(UUID(payload["generation_id"]))
        news = payload["news"]
        if not isinstance(news.get("routes"), list) or len(news["routes"]) != 3:
            raise ValueError("기사에 연결된 경로 정보가 올바르지 않습니다.")
        return generation_id, news
    except (ValueError, TypeError, KeyError, UnicodeDecodeError, binascii.Error) as error:
        raise ValueError("기사 증표가 만료됐거나 유효하지 않습니다.") from error
