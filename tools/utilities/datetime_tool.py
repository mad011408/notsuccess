"""NEXUS AI Agent - DateTime Tool"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
import re


class DateTimeTool:
    """Date and time utilities"""

    def __init__(self, default_timezone: str = "UTC"):
        self.default_timezone = default_timezone

    def now(self, tz: Optional[str] = None) -> datetime:
        """Get current datetime"""
        if tz and tz.upper() == "UTC":
            return datetime.now(timezone.utc)
        return datetime.now()

    def today(self) -> str:
        """Get today's date as string"""
        return datetime.now().strftime("%Y-%m-%d")

    def timestamp(self) -> float:
        """Get current Unix timestamp"""
        return datetime.now().timestamp()

    def from_timestamp(self, ts: float) -> datetime:
        """Convert Unix timestamp to datetime"""
        return datetime.fromtimestamp(ts)

    def parse(self, date_string: str, format: Optional[str] = None) -> Optional[datetime]:
        """
        Parse date string to datetime

        Args:
            date_string: Date string to parse
            format: Optional format string

        Returns:
            Parsed datetime or None
        """
        if format:
            try:
                return datetime.strptime(date_string, format)
            except ValueError:
                return None

        # Try common formats
        formats = [
            "%Y-%m-%d",
            "%Y/%m/%d",
            "%d-%m-%Y",
            "%d/%m/%Y",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%d %b %Y",
            "%d %B %Y",
            "%B %d, %Y",
            "%b %d, %Y",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_string, fmt)
            except ValueError:
                continue

        return None

    def format(self, dt: datetime, format: str = "%Y-%m-%d %H:%M:%S") -> str:
        """Format datetime to string"""
        return dt.strftime(format)

    def format_relative(self, dt: datetime) -> str:
        """
        Format datetime as relative string

        Args:
            dt: Datetime to format

        Returns:
            Relative time string (e.g., "2 hours ago")
        """
        now = datetime.now()
        diff = now - dt

        seconds = diff.total_seconds()

        if seconds < 0:
            # Future
            seconds = abs(seconds)
            suffix = "from now"
        else:
            suffix = "ago"

        if seconds < 60:
            return f"{int(seconds)} seconds {suffix}"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            return f"{minutes} minute{'s' if minutes != 1 else ''} {suffix}"
        elif seconds < 86400:
            hours = int(seconds / 3600)
            return f"{hours} hour{'s' if hours != 1 else ''} {suffix}"
        elif seconds < 604800:
            days = int(seconds / 86400)
            return f"{days} day{'s' if days != 1 else ''} {suffix}"
        elif seconds < 2592000:
            weeks = int(seconds / 604800)
            return f"{weeks} week{'s' if weeks != 1 else ''} {suffix}"
        elif seconds < 31536000:
            months = int(seconds / 2592000)
            return f"{months} month{'s' if months != 1 else ''} {suffix}"
        else:
            years = int(seconds / 31536000)
            return f"{years} year{'s' if years != 1 else ''} {suffix}"

    def add(
        self,
        dt: datetime,
        days: int = 0,
        hours: int = 0,
        minutes: int = 0,
        seconds: int = 0,
        weeks: int = 0
    ) -> datetime:
        """Add time to datetime"""
        return dt + timedelta(
            days=days,
            hours=hours,
            minutes=minutes,
            seconds=seconds,
            weeks=weeks
        )

    def subtract(
        self,
        dt: datetime,
        days: int = 0,
        hours: int = 0,
        minutes: int = 0,
        seconds: int = 0,
        weeks: int = 0
    ) -> datetime:
        """Subtract time from datetime"""
        return dt - timedelta(
            days=days,
            hours=hours,
            minutes=minutes,
            seconds=seconds,
            weeks=weeks
        )

    def diff(self, dt1: datetime, dt2: datetime) -> Dict[str, Any]:
        """
        Get difference between two datetimes

        Args:
            dt1: First datetime
            dt2: Second datetime

        Returns:
            Dict with difference components
        """
        diff = abs(dt2 - dt1)

        total_seconds = diff.total_seconds()

        return {
            "total_seconds": total_seconds,
            "total_minutes": total_seconds / 60,
            "total_hours": total_seconds / 3600,
            "total_days": diff.days,
            "days": diff.days,
            "hours": int((total_seconds % 86400) / 3600),
            "minutes": int((total_seconds % 3600) / 60),
            "seconds": int(total_seconds % 60),
        }

    def is_between(self, dt: datetime, start: datetime, end: datetime) -> bool:
        """Check if datetime is between two dates"""
        return start <= dt <= end

    def is_weekend(self, dt: datetime) -> bool:
        """Check if datetime is weekend"""
        return dt.weekday() >= 5

    def is_weekday(self, dt: datetime) -> bool:
        """Check if datetime is weekday"""
        return dt.weekday() < 5

    def start_of_day(self, dt: datetime) -> datetime:
        """Get start of day"""
        return dt.replace(hour=0, minute=0, second=0, microsecond=0)

    def end_of_day(self, dt: datetime) -> datetime:
        """Get end of day"""
        return dt.replace(hour=23, minute=59, second=59, microsecond=999999)

    def start_of_week(self, dt: datetime) -> datetime:
        """Get start of week (Monday)"""
        days_since_monday = dt.weekday()
        return self.start_of_day(dt - timedelta(days=days_since_monday))

    def end_of_week(self, dt: datetime) -> datetime:
        """Get end of week (Sunday)"""
        days_until_sunday = 6 - dt.weekday()
        return self.end_of_day(dt + timedelta(days=days_until_sunday))

    def start_of_month(self, dt: datetime) -> datetime:
        """Get start of month"""
        return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    def end_of_month(self, dt: datetime) -> datetime:
        """Get end of month"""
        if dt.month == 12:
            next_month = dt.replace(year=dt.year + 1, month=1, day=1)
        else:
            next_month = dt.replace(month=dt.month + 1, day=1)
        return next_month - timedelta(seconds=1)

    def get_calendar(self, year: int, month: int) -> List[List[int]]:
        """
        Get calendar for month

        Args:
            year: Year
            month: Month (1-12)

        Returns:
            List of weeks, each week is list of day numbers (0 for empty)
        """
        import calendar
        cal = calendar.Calendar(firstweekday=0)
        weeks = []

        for week in cal.monthdayscalendar(year, month):
            weeks.append(week)

        return weeks

    def days_in_month(self, year: int, month: int) -> int:
        """Get number of days in month"""
        import calendar
        return calendar.monthrange(year, month)[1]

    def is_leap_year(self, year: int) -> bool:
        """Check if year is leap year"""
        return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)

    def get_age(self, birthdate: datetime) -> int:
        """Calculate age from birthdate"""
        today = datetime.now()
        age = today.year - birthdate.year

        if (today.month, today.day) < (birthdate.month, birthdate.day):
            age -= 1

        return age

