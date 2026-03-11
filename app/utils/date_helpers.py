"""
Date and time utility functions.
Used by leaderboard_service (ISO week boundaries) and scheduler tasks.
"""
from datetime import date, timedelta


def get_iso_week_start(d: date | None = None) -> date:
    """Return the Monday of the ISO week containing `d` (defaults to today)."""
    if d is None:
        d = date.today()
    return d - timedelta(days=d.weekday())


def get_iso_week_end(d: date | None = None) -> date:
    """Return the Sunday of the ISO week containing `d` (defaults to today)."""
    return get_iso_week_start(d) + timedelta(days=6)


def is_monday(d: date | None = None) -> bool:
    """Return True if `d` (defaults to today) is a Monday."""
    if d is None:
        d = date.today()
    return d.weekday() == 0


def days_until(target: date) -> int:
    """Return number of days from today until `target`. Negative if past."""
    return (target - date.today()).days
