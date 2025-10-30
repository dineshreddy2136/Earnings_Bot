"""Date and time utilities"""
from datetime import date, timedelta


def get_week_dates(week_offset=0):
    """Get start and end dates for a specific week"""
    today = date.today()
    current_week_start = today - timedelta(days=today.weekday())
    target_week_start = current_week_start + timedelta(weeks=week_offset)
    target_week_end = target_week_start + timedelta(days=6)
    return target_week_start, target_week_end


def get_week_label(week_offset):
    """Get a human-readable label for a week offset"""
    if week_offset == 0:
        return "Current Week"
    elif week_offset > 0:
        return f"{week_offset} Week{'s' if week_offset > 1 else ''} Ahead"
    else:
        return f"{abs(week_offset)} Week{'s' if abs(week_offset) > 1 else ''} Ago"
