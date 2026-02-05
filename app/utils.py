import datetime as dt
import os

def iso_week_key(d: dt.datetime | None = None) -> str:
    d = d or dt.datetime.utcnow()
    y, w, _ = d.isocalendar()
    return f"{y}-W{w:02d}"

def now_utc() -> dt.datetime:
    return dt.datetime.utcnow()

def ext_lower(filename: str) -> str:
    return (os.path.splitext(filename or "")[1] or "").lower()

def ensure_allowed_ext(filename: str, allowed_exts: set[str]) -> bool:
    return ext_lower(filename) in allowed_exts
