import string
import random

def generate_password(length: int = 16, include_uppercase: bool = True,
                     include_lowercase: bool = True, include_numbers: bool = True,
                     include_symbols: bool = True) -> str:
    """Generate a random password."""
    characters = ""

    if include_lowercase:
        characters += string.ascii_lowercase
    if include_uppercase:
        characters += string.ascii_uppercase
    if include_numbers:
        characters += string.digits
    if include_symbols:
        characters += string.punctuation

    if not characters:
        characters = string.ascii_letters + string.digits

    password = ''.join(random.choice(characters) for _ in range(length))
    return password

def validate_password_strength(password: str) -> dict:
    """Validate password strength."""
    strength = {
        'score': 0,
        'feedback': []
    }

    if len(password) >= 8:
        strength['score'] += 1
    else:
        strength['feedback'].append('At least 8 characters')

    if len(password) >= 12:
        strength['score'] += 1

    if any(c.isupper() for c in password):
        strength['score'] += 1
    else:
        strength['feedback'].append('Add uppercase letters')

    if any(c.islower() for c in password):
        strength['score'] += 1
    else:
        strength['feedback'].append('Add lowercase letters')

    if any(c.isdigit() for c in password):
        strength['score'] += 1
    else:
        strength['feedback'].append('Add numbers')

    if any(c in string.punctuation for c in password):
        strength['score'] += 1
    else:
        strength['feedback'].append('Add special characters')

    return strength
