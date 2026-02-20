# modules/onboarding_engine.py
"""
Stateless onboarding state engine.
Determines which question to show next based on current step and answers.
"""

from typing import Dict, Any, Optional
from modules.onboarding_config import get_questions_for_relationship


class OnboardingRequest:
    """Input to the state engine"""
    def __init__(
        self,
        parent_profile_id: str,
        relationship_type: str,
        current_step: int,
        answers_json: Dict[str, Any]
    ):
        self.parent_profile_id = parent_profile_id
        self.relationship_type = relationship_type
        self.current_step = current_step
        self.answers_json = answers_json


class OnboardingResponse:
    """Output from the state engine"""
    def __init__(self, data: Dict[str, Any]):
        self.data = data
    
    def to_dict(self) -> Dict[str, Any]:
        return self.data


def get_next_question(request: OnboardingRequest) -> OnboardingResponse:
    """
    Core state engine logic.
    
    Returns either:
    - Next question metadata (step, total_steps, question)
    - Completion payload (completed=True, parent_profile_id, relationship_type, answers_json)
    
    Args:
        request: OnboardingRequest with current state
        
    Returns:
        OnboardingResponse with either next question or completion status
    """
    # Get question set for this relationship type
    questions = get_questions_for_relationship(request.relationship_type)
    total_steps = len(questions)
    
    # Check if onboarding is complete
    if is_onboarding_complete(request.answers_json, questions):
        return OnboardingResponse({
            "completed": True,
            "parent_profile_id": request.parent_profile_id,
            "relationship_type": request.relationship_type,
            "answers_json": request.answers_json
        })
    
    # Find the next unanswered question
    # current_step is 1-indexed, so we need step-1 for array access
    next_question_index = request.current_step - 1
    
    # Validate step is within bounds
    if next_question_index < 0 or next_question_index >= total_steps:
        # If step is out of bounds, default to first unanswered
        next_question_index = _find_first_unanswered_index(request.answers_json, questions)
    
    question_def = questions[next_question_index]
    
    # Build response
    return OnboardingResponse({
        "step": next_question_index + 1,  # Convert back to 1-indexed
        "total_steps": total_steps,
        "question": {
            "field_name": question_def["field_name"],
            "text": question_def["text"],
            "type": question_def["type"],
            "options": question_def.get("options"),  # May be None for 'number' type
            "allow_not_applicable": question_def["allow_not_applicable"]
        }
    })


def is_onboarding_complete(answers_json: Dict[str, Any], questions: list) -> bool:
    """
    Check if all required questions have been answered.
    
    Args:
        answers_json: Dictionary of current answers
        questions: List of question definitions
        
    Returns:
        True if all required questions are answered, False otherwise
    """
    for question in questions:
        field_name = question["field_name"]
        allow_not_applicable = question.get("allow_not_applicable", False)
        
        # If field is not in answers
        if field_name not in answers_json:
            # If it's not optional, onboarding is incomplete
            if not allow_not_applicable:
                return False
        else:
            # Field exists but could be null (for optional fields)
            value = answers_json[field_name]
            # If required field has null value, incomplete
            if not allow_not_applicable and value is None:
                return False
    
    return True


def _find_first_unanswered_index(answers_json: Dict[str, Any], questions: list) -> int:
    """
    Find the index of the first unanswered question.
    
    Args:
        answers_json: Dictionary of current answers
        questions: List of question definitions
        
    Returns:
        Index (0-based) of first unanswered question, or 0 if all answered
    """
    for i, question in enumerate(questions):
        field_name = question["field_name"]
        
        # Check if this field is unanswered
        if field_name not in answers_json:
            return i
        
        # Check if field exists but is null (and is required)
        value = answers_json[field_name]
        allow_not_applicable = question.get("allow_not_applicable", False)
        if value is None and not allow_not_applicable:
            return i
    
    # All questions answered, return last index
    return len(questions) - 1
