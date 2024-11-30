import re
from typing import Tuple

def validate_password(password: str) -> Tuple[bool, str]:
    """
    Validates a password against security standards.
    
    Requirements:
    - Minimum length of 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one number
    - At least one special character
    - No common patterns (e.g., '123456', 'password')
    
    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character"
    
    # Check for common patterns
    common_patterns = [
        'password', '123456', '123456789', 'qwerty', 'abc123',
        'football', 'letmein', 'monkey', 'admin', '12345'
    ]
    
    if password.lower() in common_patterns:
        return False, "Password is too common. Please choose a stronger password"
    
    return True, "Password meets all requirements"

def calculate_password_strength(password: str) -> int:
    """
    Calculates password strength on a scale of 0-100.
    
    Returns:
        int: Password strength score
    """
    score = 0
    
    # Length contribution (up to 25 points)
    length_score = min(len(password) * 2, 25)
    score += length_score
    
    # Character variety (up to 25 points each)
    if re.search(r'[A-Z]', password):
        score += 25
    if re.search(r'[a-z]', password):
        score += 25
    if re.search(r'\d', password):
        score += 15
    if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        score += 10
    
    return min(score, 100)
