"""F19-B: anonymous process-local Kakao API and cache counters."""
from collections import Counter
from datetime import datetime
from threading import Lock
from zoneinfo import ZoneInfo

_LOCK = Lock()
_STARTED = datetime.now(ZoneInfo("Asia/Seoul")).isoformat()
_TYPES = ("local", "directions")
_RESULTS = ("success", "timeout", "http_error", "network_error", "invalid_json", "invalid_response")
_api_counts = {kind: Counter() for kind in _TYPES}
_cache_counts = Counter()
_last_failure_at = None


def record_api_result(kind: str, result: str) -> None:
    global _last_failure_at
    if kind not in _TYPES or result not in _RESULTS:
        return
    with _LOCK:
        _api_counts[kind][result] += 1
        if result != "success":
            _last_failure_at = datetime.now(ZoneInfo("Asia/Seoul")).isoformat()


def record_cache_result(result: str) -> None:
    if result not in ("hit", "miss", "failure"):
        return
    with _LOCK:
        _cache_counts[result] += 1


def usage_snapshot() -> dict:
    with _LOCK:
        by_type = {}
        for kind in _TYPES:
            values = _api_counts[kind]
            by_type[kind] = {name: values[name] for name in _RESULTS}
            by_type[kind]["total"] = sum(values.values())
        total = sum(item["total"] for item in by_type.values())
        success = sum(item["success"] for item in by_type.values())
        hit = _cache_counts["hit"]
        miss = _cache_counts["miss"]
        return {
            "measurement_started_at": _STARTED,
            "last_api_failure_at": _last_failure_at,
            "external_requests": {
                "total": total, "success": success,
                "failure": total - success, "by_type": by_type,
            },
            "route_cache": {
                "hit": hit, "miss": miss, "failure": _cache_counts["failure"],
                "hit_rate_percent": round(100 * hit / (hit + miss), 1) if hit + miss else 0.0,
            },
            "scope_notice": "서버 프로세스 시작 이후의 익명 집계입니다. 공식 카카오 쿼터나 과금 정보가 아니며 재시작 시 초기화됩니다.",
        }
