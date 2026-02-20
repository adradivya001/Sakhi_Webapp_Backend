import os
import re
import logging
import asyncio
from typing import Dict, Any, Optional, Tuple, List
from openai import AsyncOpenAI
from supabase_client import supabase  # Use the client directly

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def constrain_summary(value: Optional[str]) -> Optional[str]:
    """
    Force the short summary to be a micro-summary:
    6–12 words, no final period, subtitle style.
    """
    if not value:
        return None
    
    text = value.strip()
    if not text:
        return None

    # Remove trailing sentence punctuation
    text = re.sub(r'[.?!]+$', '', text).strip()

    words = text.split()
    if len(words) > 12:
        text = ' '.join(words[:12])

    return text

def build_narrative_prompt(story: Dict[str, Any]) -> str:
    """
    Build the narrative prompt sent as the user message.
    We pass clean bullet-point data; the LLM turns it into first-person narrative.
    """
    is_anon = story.get("share_type") == "anonymous" or story.get("isAnonymous") == "true"
    name = "Anonymous" if is_anon else (story.get("name") or "Anonymous")

    emotions = story.get("emotions", [])
    if isinstance(emotions, list):
        emotions_str = ", ".join([str(e) for e in emotions])
    else:
        emotions_str = str(emotions)

    treatments = story.get("treatments", [])
    if isinstance(treatments, list):
        treatments_str = ", ".join([str(t) for t in treatments])
    else:
        treatments_str = str(treatments)

    parts = [
        "Use the details below to write a first-person IVF journey story.",
        "Rewrite the content into smooth, natural first-person language.",
        "",
        "Details:",
        f"- Name: {name}",
        f"- City: {story.get('city') or 'Unknown'}",
        f"- Duration of journey: {story.get('journey_duration') or 'Not provided'}",
        f"- Challenges: {story.get('challenges') or 'Not provided'}",
        f"- Emotions: {emotions_str or 'Not provided'}",
        f"- Emotion details: {story.get('emotion_description') or 'Not provided'}",
        f"- Treatments: {treatments_str or 'Not provided'}",
        f"- Outcome: {story.get('journey_outcome') or 'Not provided'}",
        f"- Outcome details: {story.get('more_details') or 'Not provided'}",
        f"- Message to others: {story.get('hope_message') or 'Not provided'}",
    ]
    return "\n".join(parts)

def fallback_narrative(story: Dict[str, Any]) -> Dict[str, str]:
    """
    Simple human fallback narrative when the LLM fails or story too short.
    """
    is_anon = story.get("share_type") == "anonymous"
    name_for_intro = "I" if is_anon else (story.get("name") or "I")
    city = story.get("city") or "my city"
    duration = story.get("journey_duration") or "some time"
    
    challenges = story.get("challenges")
    if not isinstance(challenges, str) or not challenges.strip():
        challenges = "I have faced many emotional challenges and fears along the way."
    
    outcome = story.get("journey_outcome") or "still on my journey"
    message = story.get("hope_message") or "I want to share hope with anyone going through something similar and remind you that you are not alone."

    short = "Fertility journey with fear, hope, and resilience"

    long_paragraphs = [
        f"I’m {name_for_intro} from {city}, and I’ve been on this fertility journey for {duration}. It has been a deeply emotional path filled with questions, expectations, and moments of doubt.",
        str(challenges),
        "Through all of this, I have learned how heavy the mental and emotional side of this journey can be. There were times when it felt overwhelming, but I kept moving forward one step at a time.",
        f"Right now, I am {outcome}. Whatever the stage, I am trying to stay hopeful and gentle with myself as I continue this path.",
        f"My message of hope to anyone reading this is: {message}",
    ]

    long_text = "\n\n".join(long_paragraphs)

    return {"short": short, "long": long_text}

async def generate_narrative(story: Dict[str, Any]) -> Dict[str, Optional[str]]:
    """
    Call OpenAI to generate a first-person narrative.
    """
    if not os.getenv("OPENAI_API_KEY"):
        logger.warning("OPENAI_API_KEY not set, skipping generation")
        return {"short": None, "long": None}

    user_prompt = build_narrative_prompt(story)
    
    system_prompt = """
You are a compassionate medical copywriter for an IVF healthcare platform.

Write ENTIRELY in FIRST PERSON ("I", "we", "my") as if the parent is personally sharing their journey.
Do NOT use third person ("she", "they", "the patient") anywhere.

OUTPUT FORMAT:
- First line: a short micro-summary in first person (6–12 words maximum).
- Then a blank line.
- Then the full story in 6–8 paragraphs.
- Each paragraph must be 4–6 sentences.
- Separate paragraphs with a blank line (two newlines).

MICRO-SUMMARY RULES (first line):
- It should feel like a subtitle, not a full sentence.
- Examples: "Hope after confusion", "Mixed emotions, simple plans", "Finding calm in IVF".
- No full stop at the end.
- Maximum 12 words.
- Keep it emotional, simple, and punchy.

STORY RULES:
- Turn the bullet-point data into a smooth, emotional, human story.
- Do NOT copy the user's sentences word-for-word; paraphrase into natural language.
- Do NOT add medical advice or new facts not provided.
- Keep tone warm, gentle, respectful, and hopeful.
""".strip()

    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=1100,
            temperature=0.7,
        )

        content = response.choices[0].message.content
        if not content:
            return {"short": None, "long": None}

        text = content.strip()
        if not text:
            return {"short": None, "long": None}

        # First block (before blank line) = short summary; rest = long story
        # Split by double newline to separate title from body
        blocks = re.split(r'\n\s*\n', text)
        
        first_block = blocks[0].strip() if blocks else ""
        rest = "\n\n".join(blocks[1:]).strip() if len(blocks) > 1 else ""

        short = constrain_summary(first_block)
        long_text = rest or None

        logger.info(f"LLM generated short len: {len(short) if short else 0}, long len: {len(long_text) if long_text else 0}")

        return {"short": short, "long": long_text}

    except Exception as e:
        logger.error(f"LLM generation error: {e}")
        return {"short": None, "long": None}

def ensure_narrative(result: Dict[str, Optional[str]], fallback: Dict[str, str]) -> Dict[str, str]:
    """
    Prefer LLM output; if missing/too short, fall back.
    """
    short = result.get("short")
    if short and 0 < len(short.strip()) <= 120:
        final_short = short.strip()
    else:
        final_short = fallback["short"]

    long_text = result.get("long")
    if not long_text or len(long_text.strip()) < 400 or long_text.strip() == final_short:
         final_long = fallback["long"]
    else:
         final_long = long_text.strip()

    return {"short": final_short, "long": final_long}


async def process_new_story(story_id: str, story_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main entry point to generate narrative and update database.
    """
    logger.info(f"Processing story generation for ID: {story_id}")
    
    # Generate narrative
    llm_result = await generate_narrative(story_data)
    fallback_result = fallback_narrative(story_data)
    
    final_narrative = ensure_narrative(llm_result, fallback_result)
    
    logger.info("Updating story with generated narrative...")
    
    # Update Supabase
    try:
        response = supabase.table("sakhi_success_stories").update({
            "summary": final_narrative["short"],
            "generated_story": final_narrative["long"]
        }).eq("id", story_id).execute()
        
        if response.data and len(response.data) > 0:
            logger.info("Story updated successfully.")
            return response.data[0]
        else:
            logger.error("Failed to update story in database (no data returned).")
            # Return original data with generated fields manually added so response is correct
            story_data_copy = story_data.copy()
            story_data_copy["summary"] = final_narrative["short"]
            story_data_copy["generated_story"] = final_narrative["long"]
            return story_data_copy
            
    except Exception as e:
        logger.error(f"Database update failed: {e}")
        # Return original data if update fails
        return story_data
