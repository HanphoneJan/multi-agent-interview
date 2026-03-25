"""Utility functions"""
import hashlib
import random
import string
from datetime import datetime
from typing import Any


def generate_random_string(length: int = 32) -> str:
    """Generate a random string"""
    letters = string.ascii_letters + string.digits
    return ''.join(random.choice(letters) for _ in range(length))


def generate_verification_code(length: int = 6) -> str:
    """Generate a numeric verification code"""
    return ''.join(random.choices(string.digits, k=length))


def compute_md5(text: str) -> str:
    """Compute MD5 hash of a string"""
    return hashlib.md5(text.encode()).hexdigest()


def format_datetime(dt: datetime | None, format_str: str = "%Y-%m-%d %H:%M:%S") -> str | None:
    """Format datetime to string"""
    if dt is None:
        return None
    return dt.strftime(format_str)


def parse_datetime(dt_str: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> datetime:
    """Parse datetime from string"""
    return datetime.strptime(dt_str, format_str)


def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate a string to max_length"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def safe_json_dumps(obj: Any, default: Any = str) -> str:
    """Safely dump object to JSON string"""
    import json
    return json.dumps(obj, default=default, ensure_ascii=False)


def is_valid_email(email: str) -> bool:
    """Validate email format"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def is_valid_phone(phone: str) -> bool:
    """Validate Chinese phone number"""
    import re
    pattern = r'^1[3-9]\d{9}$'
    return bool(re.match(pattern, phone))


def sanitize_string(text: str) -> str:
    """Sanitize string for security"""
    import html
    return html.escape(text)
