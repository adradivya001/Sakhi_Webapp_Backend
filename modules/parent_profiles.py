# modules/parent_profiles.py
"""
Database operations for parent_profiles table.
"""

from typing import Dict, Any, Optional
from supabase_client import supabase_insert, supabase_select, supabase_update, generate_user_id


def create_parent_profile(
    user_id: str,
    target_user_id: Optional[str],
    relationship_type: str,
    answers_json: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Create a new parent profile record.
    
    Args:
        user_id: ID of the user creating this profile
        target_user_id: ID of the target user (woman trying to conceive)
        relationship_type: Relationship to the target user
        answers_json: Collected onboarding answers
        
    Returns:
        Created parent profile record
    """
    parent_profile_id = generate_user_id()  # Generate UUID
    
    data = {
        "parent_profile": parent_profile_id,
        "user_id": user_id,
        "target_user_id": target_user_id,
        "relationship_type": relationship_type,
        "answers_json": answers_json,
    }
    
    result = supabase_insert("sakhi_parent_profiles", data)
    return result[0] if isinstance(result, list) and len(result) > 0 else result


def update_parent_profile_answers(
    parent_profile_id: str,
    answers_json: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Update answers for an existing parent profile.
    
    Args:
        parent_profile_id: ID of the parent profile to update
        answers_json: Updated answers
        
    Returns:
        Updated parent profile record
    """
    match_filter = f"parent_profile=eq.{parent_profile_id}"
    data = {"answers_json": answers_json}
    
    result = supabase_update("sakhi_parent_profiles", match_filter, data)
    return result[0] if isinstance(result, list) and len(result) > 0 else result


def get_parent_profile(parent_profile_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve a parent profile by ID.
    
    Args:
        parent_profile_id: ID of the parent profile
        
    Returns:
        Parent profile record or None if not found
    """
    filters = f"parent_profile=eq.{parent_profile_id}"
    result = supabase_select("sakhi_parent_profiles", select="*", filters=filters)
    
    if isinstance(result, list) and len(result) > 0:
        return result[0]
    return None

