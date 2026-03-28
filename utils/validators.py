"""Input validation helpers."""
import re


def is_valid_email(email: str) -> bool:
    """Return True if email matches a basic RFC-like pattern."""
    pattern = r"^[\w\.\+\-]+@[\w\-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email.strip()))
