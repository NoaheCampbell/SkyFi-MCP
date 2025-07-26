"""Natural language date parsing for user-friendly date inputs."""
import re
from datetime import datetime, timedelta, timezone
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


def parse_natural_date(date_str: str, base_date: Optional[datetime] = None) -> datetime:
    """
    Parse natural language dates into datetime objects.
    
    Examples:
        - "yesterday" → yesterday at 00:00
        - "last week" → 7 days ago
        - "2 weeks ago" → 14 days ago
        - "last month" → 30 days ago
        - "january 15" → January 15 of current year
        - "2024-01-15" → ISO date (passthrough)
    
    Args:
        date_str: Natural language date string
        base_date: Base date for relative calculations (defaults to now)
        
    Returns:
        datetime object in UTC
    """
    if base_date is None:
        base_date = datetime.now(timezone.utc)
    
    # Normalize input
    date_str = date_str.lower().strip()
    
    # If already in ISO format, parse and return
    iso_pattern = r'^\d{4}-\d{2}-\d{2}'
    if re.match(iso_pattern, date_str):
        try:
            # Handle with or without time
            if 'T' in date_str or ' ' in date_str:
                return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            else:
                # Add time component for date-only strings
                return datetime.fromisoformat(f"{date_str}T00:00:00+00:00")
        except:
            pass  # Fall through to natural language parsing
    
    # Common relative dates
    if date_str in ['today', 'now']:
        return base_date.replace(hour=0, minute=0, second=0, microsecond=0)
    
    if date_str == 'yesterday':
        return (base_date - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    
    if date_str == 'tomorrow':
        return (base_date + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    
    # "X days/weeks/months ago" patterns
    ago_pattern = r'(\d+)\s*(day|week|month)s?\s*ago'
    match = re.match(ago_pattern, date_str)
    if match:
        amount = int(match.group(1))
        unit = match.group(2)
        
        if unit == 'day':
            return (base_date - timedelta(days=amount)).replace(hour=0, minute=0, second=0, microsecond=0)
        elif unit == 'week':
            return (base_date - timedelta(weeks=amount)).replace(hour=0, minute=0, second=0, microsecond=0)
        elif unit == 'month':
            # Approximate month as 30 days
            return (base_date - timedelta(days=amount * 30)).replace(hour=0, minute=0, second=0, microsecond=0)
    
    # "last week/month/year" patterns
    if date_str == 'last week':
        return (base_date - timedelta(weeks=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    
    if date_str == 'last month' or date_str == 'past month':
        return (base_date - timedelta(days=30)).replace(hour=0, minute=0, second=0, microsecond=0)
    
    if date_str == 'last year' or date_str == 'past year':
        return (base_date - timedelta(days=365)).replace(hour=0, minute=0, second=0, microsecond=0)
    
    # "past X days/weeks/months" patterns
    past_pattern = r'past\s*(\d+)\s*(day|week|month)s?'
    match = re.match(past_pattern, date_str)
    if match:
        amount = int(match.group(1))
        unit = match.group(2)
        
        if unit == 'day':
            return (base_date - timedelta(days=amount)).replace(hour=0, minute=0, second=0, microsecond=0)
        elif unit == 'week':
            return (base_date - timedelta(weeks=amount)).replace(hour=0, minute=0, second=0, microsecond=0)
        elif unit == 'month':
            return (base_date - timedelta(days=amount * 30)).replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Month names
    months = {
        'january': 1, 'jan': 1,
        'february': 2, 'feb': 2,
        'march': 3, 'mar': 3,
        'april': 4, 'apr': 4,
        'may': 5,
        'june': 6, 'jun': 6,
        'july': 7, 'jul': 7,
        'august': 8, 'aug': 8,
        'september': 9, 'sep': 9, 'sept': 9,
        'october': 10, 'oct': 10,
        'november': 11, 'nov': 11,
        'december': 12, 'dec': 12
    }
    
    # "January 15" or "15 January" patterns
    for month_name, month_num in months.items():
        # "Month Day" pattern
        pattern1 = rf'{month_name}\s+(\d{{1,2}})'
        match = re.match(pattern1, date_str)
        if match:
            day = int(match.group(1))
            year = base_date.year
            try:
                return datetime(year, month_num, day, tzinfo=timezone.utc)
            except ValueError:
                pass
        
        # "Day Month" pattern
        pattern2 = rf'(\d{{1,2}})\s+{month_name}'
        match = re.match(pattern2, date_str)
        if match:
            day = int(match.group(1))
            year = base_date.year
            try:
                return datetime(year, month_num, day, tzinfo=timezone.utc)
            except ValueError:
                pass
    
    # If we can't parse it, raise an error
    raise ValueError(f"Could not parse date: '{date_str}'")


def parse_date_range(from_str: str, to_str: str) -> Tuple[datetime, datetime]:
    """
    Parse a date range with natural language support.
    
    Special cases:
        - If from_str is "recent" or similar, default to last 3 months
        - If to_str is "now" or missing, use current date
        
    Returns:
        Tuple of (from_date, to_date) in UTC
    """
    # Handle special cases
    if from_str.lower() in ['recent', 'recently']:
        from_date = datetime.now(timezone.utc) - timedelta(days=90)
        from_date = from_date.replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        from_date = parse_natural_date(from_str)
    
    if to_str.lower() in ['now', 'today', 'current']:
        to_date = datetime.now(timezone.utc)
    else:
        to_date = parse_natural_date(to_str)
    
    # Ensure from_date is before to_date
    if from_date > to_date:
        from_date, to_date = to_date, from_date
        logger.warning(f"Swapped date range: {from_date} to {to_date}")
    
    return from_date, to_date


def format_date_for_api(dt: datetime) -> str:
    """Format datetime for SkyFi API (ISO 8601)."""
    # Ensure UTC timezone
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()