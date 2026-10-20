"""Approved F19/F20/F21 policy primitives (no DB writes or scheduled jobs)."""
from datetime import date, datetime, time, timezone
from zoneinfo import ZoneInfo

KOREA = ZoneInfo("Asia/Seoul")
PUBLICATION_STATES = frozenset({"review", "published", "held"})
_ALLOWED = {
    "review": frozenset({"published", "held"}),
    "published": frozenset({"held"}),
    "held": frozenset({"review", "published"}),
}
SAFE_ERROR_CODES = frozenset({
    "timeout", "http_error", "network_error", "invalid_json",
    "invalid_response", "database_error", "unexpected_error",
})


def scheduled_slot_utc(day: date) -> datetime:
    """One scheduled slot per Korean calendar day, at 09:00 KST."""
    if not isinstance(day, date) or isinstance(day, datetime):
        raise ValueError("A calendar date is required")
    return datetime.combine(day, time(9), tzinfo=KOREA).astimezone(timezone.utc)


def publication_transition_allowed(previous: str, target: str) -> bool:
    """Same-state changes are not new history events."""
    return target in _ALLOWED.get(previous, ())


def visible_to_anonymous(status: str | None) -> bool:
    """Missing status is a legacy article and remains public."""
    return status is None or status == "published"


def safe_error_code(value: str) -> str:
    """Discard arbitrary API error text, secrets and response bodies."""
    return value if value in SAFE_ERROR_CODES else "unexpected_error"
