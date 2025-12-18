# modules/onboarding_config.py
"""
Canonical question sets for onboarding flow.
Each relationship type has a fixed set of questions.
DO NOT modify question text or options - frontend depends on exact matching.
"""

from typing import List, Dict, Any

# Question set for 'herself' - 7 steps
QUESTIONS_HERSELF = [
    {
        "field_name": "age",
        "text": "What is your age?",
        "type": "number",
        "allow_not_applicable": False
    },
    {
        "field_name": "tryingDuration",
        "text": "How long have you been actively trying to conceive?",
        "type": "radio",
        "options": ["Less than 6 months", "6–12 months", "1–2 years", "More than 2 years"],
        "allow_not_applicable": False
    },
    {
        "field_name": "previousTreatments",
        "text": "Have you had any previous fertility treatments?",
        "type": "radio",
        "options": ["No / first time", "Medications only", "IUI", "IVF"],
        "allow_not_applicable": False
    },
    {
        "field_name": "diagnosis",
        "text": "Have you or your partner been diagnosed with any conditions?",
        "type": "radio",
        "options": ["Condition related to me", "Partner condition", "Both", "Unexplained", "Not diagnosed yet"],
        "allow_not_applicable": False
    },
    {
        "field_name": "partnerAge",
        "text": "What is your partner's age?",
        "type": "number",
        "allow_not_applicable": True
    },
    {
        "field_name": "previousPregnancy",
        "text": "Have you ever been pregnant before?",
        "type": "radio",
        "options": ["Never", "Had a child", "Loss / miscarriage"],
        "allow_not_applicable": False
    },
    {
        "field_name": "priority",
        "text": "What is your biggest priority right now?",
        "type": "radio",
        "options": ["Medical process", "Emotional stress", "Financial planning", "Lifestyle / diet"],
        "allow_not_applicable": False
    }
]

# Question set for 'himself' - 5 steps
QUESTIONS_HIMSELF = [
    {
        "field_name": "tryingForBaby",
        "text": "Are you and your partner trying to have a baby?",
        "type": "radio",
        "options": ["Actively trying", "Planning soon", "Exploring options"],
        "allow_not_applicable": False
    },
    {
        "field_name": "smokingDrinking",
        "text": "Do you have smoking and drinking habits?",
        "type": "radio",
        "options": ["No", "Smoke occasionally", "Drink occasionally", "Regularly"],
        "allow_not_applicable": False
    },
    {
        "field_name": "fertilityTests",
        "text": "Have you or your partner done fertility tests?",
        "type": "radio",
        "options": ["No tests", "Partner tested", "Semen analysis", "Both tested"],
        "allow_not_applicable": False
    },
    {
        "field_name": "healthProblems",
        "text": "Do you or your partner have health problems?",
        "type": "radio",
        "options": ["No problems", "I have condition", "Partner has condition", "Both"],
        "allow_not_applicable": False
    },
    {
        "field_name": "previousIVF",
        "text": "Has your partner had IVF treatments in the past?",
        "type": "radio",
        "options": ["First time", "One cycle", "Multiple cycles", "Not sure"],
        "allow_not_applicable": False
    }
]

# Question set for 'father' - 5 steps
QUESTIONS_FATHER = [
    {
        "field_name": "duration",
        "text": "How long is your daughter trying to have a baby?",
        "type": "radio",
        "options": ["About a year", "Few years", "Long time", "Not sure"],
        "allow_not_applicable": False
    },
    {
        "field_name": "treatment",
        "text": "Is she seeing a doctor or taking treatment?",
        "type": "radio",
        "options": ["Yes under care", "No, not started", "Not aware"],
        "allow_not_applicable": False
    },
    {
        "field_name": "healthIssues",
        "text": "Does she have health problems?",
        "type": "radio",
        "options": ["Yes mentioned", "Not that I know", "Not sure"],
        "allow_not_applicable": False
    },
    {
        "field_name": "emotionalState",
        "text": "How is she feeling emotionally?",
        "type": "radio",
        "options": ["Quiet / worried", "Tries positive", "Very concerned"],
        "allow_not_applicable": False
    },
    {
        "field_name": "previousIVF",
        "text": "Did she have IVF treatments in the past?",
        "type": "radio",
        "options": ["First time", "Tried before", "Not sure"],
        "allow_not_applicable": False
    }
]

# Question set for 'mother' - 5 steps
QUESTIONS_MOTHER = [
    {
        "field_name": "duration",
        "text": "How long is your daughter trying?",
        "type": "radio",
        "options": ["Less than a year", "1–2 years", "More than 2 years"],
        "allow_not_applicable": False
    },
    {
        "field_name": "medicalCare",
        "text": "Has she seen a doctor or done tests?",
        "type": "radio",
        "options": ["Seeing specialist", "Done tests", "Encouraging her", "Not sure"],
        "allow_not_applicable": False
    },
    {
        "field_name": "healthIssues",
        "text": "Does she have health problems?",
        "type": "radio",
        "options": ["Yes told me", "Healthy", "Suspect issue"],
        "allow_not_applicable": False
    },
    {
        "field_name": "emotionalState",
        "text": "How is she feeling about trying?",
        "type": "radio",
        "options": ["Stressed / disheartened", "Hopeful but difficult", "Confides in me"],
        "allow_not_applicable": False
    },
    {
        "field_name": "previousIVF",
        "text": "Did she have IVF treatments?",
        "type": "radio",
        "options": ["First attempt", "One cycle", "Multiple attempts"],
        "allow_not_applicable": False
    }
]

# Question set for 'father_in_law' - 5 steps
QUESTIONS_FATHER_IN_LAW = [
    {
        "field_name": "duration",
        "text": "How long is your daughter-in-law trying?",
        "type": "radio",
        "options": ["Over a year", "Few years", "Not sure"],
        "allow_not_applicable": False
    },
    {
        "field_name": "treatment",
        "text": "Is she seeing a doctor?",
        "type": "radio",
        "options": ["Yes, seeing someone", "Don't believe so", "Private matter"],
        "allow_not_applicable": False
    },
    {
        "field_name": "healthIssues",
        "text": "Does she have health problems?",
        "type": "radio",
        "options": ["Not told", "Not aware of details"],
        "allow_not_applicable": False
    },
    {
        "field_name": "emotionalState",
        "text": "How is she feeling?",
        "type": "radio",
        "options": ["Manages well", "Quiet / worried", "Don't discuss openly"],
        "allow_not_applicable": False
    },
    {
        "field_name": "previousIVF",
        "text": "Did she have IVF treatments?",
        "type": "radio",
        "options": ["Don't think so", "Tried before", "Not sure"],
        "allow_not_applicable": False
    }
]

# Question set for 'mother_in_law' - 5 steps
QUESTIONS_MOTHER_IN_LAW = [
    {
        "field_name": "duration",
        "text": "How long is your daughter-in-law trying?",
        "type": "radio",
        "options": ["About a year", "Few years", "Long time"],
        "allow_not_applicable": False
    },
    {
        "field_name": "treatment",
        "text": "Is she taking treatment?",
        "type": "radio",
        "options": ["Yes, good doctor", "Suggested doctors", "Not fully aware"],
        "allow_not_applicable": False
    },
    {
        "field_name": "emotionalState",
        "text": "Do you see her stressed or worried?",
        "type": "radio",
        "options": ["Clearly worried", "Tries to hide it", "Handling well"],
        "allow_not_applicable": False
    },
    {
        "field_name": "support",
        "text": "How do you help or talk to her?",
        "type": "radio",
        "options": ["Give advice", "Listen and comfort", "Avoid talking to reduce pressure"],
        "allow_not_applicable": False
    },
    {
        "field_name": "previousIVF",
        "text": "Did she have IVF treatments?",
        "type": "radio",
        "options": ["First time", "Once before", "Few times"],
        "allow_not_applicable": False
    }
]

# Question set for 'sibling' - 5 steps
QUESTIONS_SIBLING = [
    {
        "field_name": "duration",
        "text": "How long is your sibling trying?",
        "type": "radio",
        "options": ["About a year", "Couple years", "Long time"],
        "allow_not_applicable": False
    },
    {
        "field_name": "treatment",
        "text": "Are they seeing a doctor?",
        "type": "radio",
        "options": ["Yes specialist", "Yes but private", "Not sure"],
        "allow_not_applicable": False
    },
    {
        "field_name": "healthIssues",
        "text": "Do they have health problems?",
        "type": "radio",
        "options": ["Yes mentioned", "Not that I know", "Not shared"],
        "allow_not_applicable": False
    },
    {
        "field_name": "emotionalState",
        "text": "How are they feeling?",
        "type": "radio",
        "options": ["Stressed / frustrated", "Trying to be positive", "Don't open up"],
        "allow_not_applicable": False
    },
    {
        "field_name": "previousIVF",
        "text": "Have they gone through IVF?",
        "type": "radio",
        "options": ["First time", "Been through it", "Don't know details"],
        "allow_not_applicable": False
    }
]

# Mapping of relationship types to their question sets
RELATIONSHIP_QUESTIONS: Dict[str, List[Dict[str, Any]]] = {
    "herself": QUESTIONS_HERSELF,
    "himself": QUESTIONS_HIMSELF,
    "father": QUESTIONS_FATHER,
    "mother": QUESTIONS_MOTHER,
    "father_in_law": QUESTIONS_FATHER_IN_LAW,
    "mother_in_law": QUESTIONS_MOTHER_IN_LAW,
    "sibling": QUESTIONS_SIBLING,
}

def get_questions_for_relationship(relationship_type: str) -> List[Dict[str, Any]]:
    """
    Retrieve the question set for a given relationship type.
    
    Args:
        relationship_type: One of the supported relationship types
        
    Returns:
        List of question dictionaries
        
    Raises:
        ValueError: If relationship_type is not recognized
    """
    if relationship_type not in RELATIONSHIP_QUESTIONS:
        valid_types = ", ".join(RELATIONSHIP_QUESTIONS.keys())
        raise ValueError(
            f"Invalid relationship_type: '{relationship_type}'. "
            f"Must be one of: {valid_types}"
        )
    
    return RELATIONSHIP_QUESTIONS[relationship_type]
