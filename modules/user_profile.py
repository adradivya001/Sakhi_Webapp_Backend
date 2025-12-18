# modules/user_profile.py
import re

from supabase_client import (
    generate_user_id,
    supabase_insert,
    supabase_select,
    supabase_update,
)


def _normalize_phone(phone: str | None) -> str | None:
    """
    Strip non-digits, remove leading +91/91 for consistency, keep remaining digits.
    """
    if not phone:
        return None
    digits = re.sub(r"\D", "", phone)
    if len(digits) > 10 and digits.startswith("91"):
        digits = digits[2:]
    return digits or None


def create_user(
    name: str,
    email: str,
    password: str,
    phone_number: str | None = None,
    role: str | None = "USER",
    preferred_language: str | None = None,
    relation: str | None = None,
):
    """
    Insert a user into the 'sakhi_users' table and return the inserted row.
    """
    user_id = generate_user_id()

    norm_phone = _normalize_phone(phone_number)

    data = {
        "user_id": user_id,
        "name": name,
        "email": email,
        "phone_number": norm_phone,
        # Store as password_hash column expected by Supabase schema.
        # (Consider hashing before storing in production.)
        "password_hash": password,
        "role": role,
        "preferred_language": preferred_language,
        "relation_to_patient": relation,
    }

    inserted = supabase_insert("sakhi_users", data)
    if isinstance(inserted, list) and inserted:
        return inserted[0]
    if isinstance(inserted, dict):
        return inserted
    raise Exception("Unexpected response while creating user")


def update_relation(user_id: str, relation: str):
    if not user_id:
        raise ValueError("user_id is required")
    if not relation:
        raise ValueError("relation is required")
    match = f"user_id=eq.{user_id}"
    return supabase_update("sakhi_users", match, {"relation_to_patient": relation})


def update_preferred_language(user_id: str, preferred_language: str):
    if not user_id:
        raise ValueError("user_id is required")
    if not preferred_language:
        raise ValueError("preferred_language is required")
    match = f"user_id=eq.{user_id}"
    return supabase_update("sakhi_users", match, {"preferred_language": preferred_language})


def get_user_profile(user_id: str):
    """
    Fetch complete user profile.
    """
    rows = supabase_select("sakhi_users", select="*", filters=f"user_id=eq.{user_id}")

    if not rows or not isinstance(rows, list):
        return None

    return rows[0]


def get_user_by_phone(phone_number: str):
    """
    Fetch user by phone_number (or phone).
    """
    if not phone_number:
        return None
    norm = _normalize_phone(phone_number)
    if not norm:
        return None
    # try phone_number first
    rows = supabase_select("sakhi_users", select="*", filters=f"phone_number=eq.{norm}")
    if rows and isinstance(rows, list) and rows:
        return rows[0]
    return None


def resolve_user_id_by_phone(phone_number: str) -> str | None:
    user = get_user_by_phone(phone_number)
    if user:
        return user.get("user_id")
    return None


def create_partial_user(phone_number: str):
    """
    Create a minimal user record with just phone number to start onboarding.
    """
    user_id = generate_user_id()
    norm_phone = _normalize_phone(phone_number)
    
    data = {
        "user_id": user_id,
        "phone_number": norm_phone,
        "role": "USER",
    }
    
    # insert
    inserted = supabase_insert("sakhi_users", data)
    if isinstance(inserted, list) and inserted:
        return inserted[0]
    if isinstance(inserted, dict):
        return inserted
    return data

def update_user_profile(user_id: str, updates: dict):
    """
    Update specific fields in user profile.
    """
    if not user_id:
        raise ValueError("user_id is required")
    
    match = f"user_id=eq.{user_id}"
    return supabase_update("sakhi_users", match, updates)


def login_user(email: str, password: str):
    """
    Authenticate user by email and password.
    Returns user profile if credentials are valid, None otherwise.
    
    Args:
        email: User's email address
        password: User's password
        
    Returns:
        User profile dict if successful, None if authentication fails
        
    Raises:
        ValueError: If email or password is missing
    """
    if not email:
        raise ValueError("email is required")
    if not password:
        raise ValueError("password is required")
    
    # Fetch user by email
    rows = supabase_select("sakhi_users", select="*", filters=f"email=eq.{email}")
    
    if not rows or not isinstance(rows, list) or len(rows) == 0:
        return None
    
    user = rows[0]
    
    # Check password (in production, use proper password hashing like bcrypt)
    # Currently storing as plain text in password_hash column
    stored_password = user.get("password_hash")
    
    if stored_password != password:
        return None
    
    # Authentication successful
    return user
