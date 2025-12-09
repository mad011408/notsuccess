"""NEXUS AI Agent - Validators"""

import re
import os
import json
from typing import Any, Optional
from urllib.parse import urlparse


def validate_url(url: str) -> bool:
    """Validate URL format"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_json(json_string: str) -> bool:
    """Validate JSON string"""
    try:
        json.loads(json_string)
        return True
    except (json.JSONDecodeError, TypeError):
        return False


def validate_path(path: str) -> bool:
    """Validate file path exists"""
    return os.path.exists(path)


def validate_directory(path: str) -> bool:
    """Validate directory exists"""
    return os.path.isdir(path)


def validate_file(path: str) -> bool:
    """Validate file exists"""
    return os.path.isfile(path)


def validate_ip_address(ip: str) -> bool:
    """Validate IP address"""
    parts = ip.split('.')
    if len(parts) != 4:
        return False
    try:
        return all(0 <= int(part) <= 255 for part in parts)
    except ValueError:
        return False


def validate_port(port: int) -> bool:
    """Validate port number"""
    return 0 <= port <= 65535


def validate_uuid(uuid_string: str) -> bool:
    """Validate UUID format"""
    pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    return bool(re.match(pattern, uuid_string, re.IGNORECASE))


def validate_phone(phone: str) -> bool:
    """Validate phone number"""
    pattern = r'^\+?[\d\s\-\(\)]{10,}$'
    return bool(re.match(pattern, phone))


def validate_date(date_string: str, format: str = "%Y-%m-%d") -> bool:
    """Validate date string"""
    from datetime import datetime
    try:
        datetime.strptime(date_string, format)
        return True
    except ValueError:
        return False


def validate_hex_color(color: str) -> bool:
    """Validate hex color"""
    pattern = r'^#(?:[0-9a-fA-F]{3}){1,2}$'
    return bool(re.match(pattern, color))


def validate_credit_card(number: str) -> bool:
    """Validate credit card number using Luhn algorithm"""
    # Remove spaces and dashes
    number = number.replace(' ', '').replace('-', '')

    if not number.isdigit() or len(number) < 13 or len(number) > 19:
        return False

    # Luhn algorithm
    total = 0
    reverse_digits = number[::-1]

    for i, digit in enumerate(reverse_digits):
        d = int(digit)
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d

    return total % 10 == 0


def validate_password_strength(password: str) -> dict:
    """Validate password strength"""
    result = {
        "valid": True,
        "length": len(password) >= 8,
        "uppercase": bool(re.search(r'[A-Z]', password)),
        "lowercase": bool(re.search(r'[a-z]', password)),
        "digit": bool(re.search(r'\d', password)),
        "special": bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password)),
    }

    # Must meet minimum requirements
    result["valid"] = (
        result["length"] and
        result["uppercase"] and
        result["lowercase"] and
        result["digit"]
    )

    # Calculate strength score
    result["score"] = sum([
        result["length"],
        result["uppercase"],
        result["lowercase"],
        result["digit"],
        result["special"]
    ])

    return result


def validate_slug(slug: str) -> bool:
    """Validate URL slug"""
    pattern = r'^[a-z0-9]+(?:-[a-z0-9]+)*$'
    return bool(re.match(pattern, slug))


def validate_api_key(key: str, prefix: Optional[str] = None) -> bool:
    """Validate API key format"""
    if not key or len(key) < 20:
        return False

    if prefix and not key.startswith(prefix):
        return False

    # Check for basic structure
    return bool(re.match(r'^[a-zA-Z0-9_-]+$', key))


def validate_model_name(model: str) -> bool:
    """Validate model name"""
    valid_models = [
        "gpt-4", "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo",
        "claude-3-opus", "claude-3-sonnet", "claude-3-haiku",
        "gemini-pro", "gemini-ultra",
        "mistral-large", "mistral-medium",
    ]

    # Check exact match or prefix match
    return any(model.startswith(m) for m in valid_models)

