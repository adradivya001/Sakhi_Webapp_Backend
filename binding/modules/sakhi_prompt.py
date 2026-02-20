# modules/sakhi_prompt.py

def build_sakhi_prompt(
    user_message: str,
    user_profile: dict,
    conversation_history: list,
    rag_context: str,
    language: str = "en"
):
    """
    Builds the complete prompt for the LLM including:
    - Persona
    - Safety rules
    - RAG context
    - Conversation history
    """
    # --------- 1. Persona ----------
    relation = user_profile.get("relation_to_patient", "self")
    name = user_profile.get("name", "dear")
    pref_lang = user_profile.get("preferred_language", "en")

    if relation == "husband":
        persona = f"You are Sakhi, a warm emotional guide for a husband supporting his wife through fertility or pregnancy."
    elif relation == "mother":
        persona = f"You are Sakhi, a patient, caring guide for a mother helping her daughter through fertility or pregnancy."
    else:
        persona = f"You are Sakhi, a compassionate fertility and pregnancy support companion."

    # --------- 2. Medical Safety Layer ----------
    safety = """
    SAFETY RULES:
    - Do NOT give exact medications, dosages, or prescriptions.
    - Do NOT diagnose medical conditions.
    - Give general, supportive guidance only.
    - Recommend consulting a doctor for ANY medical decisions.
    - If the user expresses danger signs (bleeding, severe pain, fainting),
      advise immediate medical attention.
    """

    # --------- 3. Conversation History ----------
    history_text = ""
    for msg in conversation_history[-10:]:  # last 10 messages
        speaker = "User" if msg["message_type"] == "user" else "Sakhi"
        history_text += f"{speaker}: {msg['message_text']}\n"

    # --------- 4. Final Prompt ----------
    prompt = f"""
    {persona}

    {safety}

    USER PROFILE:
    Name: {name}
    Relation: {relation}
    Preferred Language: {pref_lang}

    CONTEXT FROM KNOWLEDGE (RAG):
    {rag_context}

    PREVIOUS CONVERSATION:
    {history_text}

    USER MESSAGE:
    {user_message}

    Your Task:
    - Reply with empathy, warmth, and emotional intelligence.
    - Keep the explanation simple, human, and supportive.
    - If user’s preferred language is not English, output in that language.
    """

    return prompt
