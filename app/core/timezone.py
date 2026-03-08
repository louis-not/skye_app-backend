from datetime import datetime, timezone, timedelta


# Bangkok timezone (UTC+7)
BANGKOK_TZ = timezone(timedelta(hours=7))


def utc_now() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


def bangkok_now() -> datetime:
    """Get current Bangkok datetime."""
    return datetime.now(BANGKOK_TZ)


def to_bangkok(dt: datetime) -> datetime:
    """Convert datetime to Bangkok timezone."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(BANGKOK_TZ)


def to_utc(dt: datetime) -> datetime:
    """Convert datetime to UTC."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=BANGKOK_TZ)
    return dt.astimezone(timezone.utc)
