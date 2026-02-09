# main.py
from fastapi import FastAPI, HTTPException, UploadFile, File, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, model_validator
from uuid import UUID
from enum import Enum
from datetime import datetime
import uuid as uuid_module

from modules.user_profile import (
    create_user,
    update_preferred_language,
    update_relation, 
    get_user_profile,
    resolve_user_id_by_phone,
    get_user_by_phone,
    create_partial_user,
    update_user_profile,
    login_user,
)
from modules.response_builder import (
    classify_message,
    generate_medical_response,
    generate_smalltalk_response,
    generate_intent,
)
from modules.conversation import save_user_message, save_sakhi_message, get_last_messages
from modules.user_answers import save_bulk_answers
from modules.model_gateway import get_model_gateway, Route
from modules.slm_client import get_slm_client
from modules.onboarding_engine import OnboardingRequest, get_next_question
from modules.parent_profiles import create_parent_profile, update_parent_profile_answers
from modules.onboarding_engine import OnboardingRequest, get_next_question
from modules.parent_profiles import create_parent_profile, update_parent_profile_answers
from search_hierarchical import hierarchical_rag_query, format_hierarchical_context
from modules.tools import router as tools_router

app = FastAPI()

# Include Tools Router
app.include_router(tools_router)

# CORS Configuration - Allow Replit frontend to call this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize model gateway and SLM client (singleton instances)
model_gateway = get_model_gateway()
slm_client = get_slm_client()

class RegisterRequest(BaseModel):
    name: str  # full name
    email: str
    password: str
    phone_number: str | None = None
    role: str | None = "USER"
    preferred_language: str | None = None
    user_relation: str | None = None


class ChatRequest(BaseModel):
    user_id: str | None = None
    phone_number: str | None = None
    message: str
    language: str = "en"


class AnswerItem(BaseModel):
    question_key: str
    selected_options: list[str]


class UserAnswersRequest(BaseModel):
    user_id: str
    answers: list[AnswerItem]


class UpdateRelationRequest(BaseModel):
    user_id: str
    relation: str


class UpdatePreferredLanguageRequest(BaseModel):
    user_id: str
    preferred_language: str


# Onboarding models
class OnboardingStepRequest(BaseModel):
    parent_profile_id: str
    relationship_type: str
    current_step: int
    answers_json: dict


class OnboardingCompleteRequest(BaseModel):
    parent_profile_id: str | None = None
    user_id: str
    target_user_id: str | None = None
    relationship_type: str
    answers_json: dict


class JourneyUpdateRequest(BaseModel):
    user_id: str
    stage: str
    date: str | None = None
    date_type: str | None = None


# Login model
class LoginRequest(BaseModel):
    email: str
    password: str


# ================== KNOWLEDGE HUB MODELS ==================
class KnowledgeHubResponse(BaseModel):
    id: int
    slug: str
    title: str
    content: str
    summary: str | None = None
    life_stage_id: int | None = None
    perspective_id: int | None = None
    author_name: str | None = None
    read_time_minutes: int = 5
    is_featured: bool = False
    published_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


# ================== SUCCESS STORIES MODELS ==================
class ShareType(str, Enum):
    NAMED = "named"
    ANONYMOUS = "anonymous"
    PUBLIC = "public"


class StoryStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    PUBLISHED = "published"


class StoryBase(BaseModel):
    share_type: ShareType | None = None
    name: str | None = None
    city: str | None = None
    journey_duration: str | None = None
    challenges: str | None = None
    emotions: list[str] | None = None
    treatments: list[str] | None = None
    emotion_description: str | None = None
    journey_outcome: str | None = None
    more_details: str | None = None
    hope_message: str | None = None
    photo_url: str | None = None
    summary: str | None = None
    generated_story: str | None = None
    slug: str | None = None
    title: str | None = None
    stage: str | None = None
    language: str = "en"

    @model_validator(mode='after')
    def check_name_if_named(self):
        # Validation relaxed for fetching existing data
        return self


class StoryCreate(StoryBase):
    model_config = {"extra": "allow"}
    pass


class StoryUpdateStatus(BaseModel):
    status: StoryStatus


class StoryConsent(BaseModel):
    id: UUID


class StoryResponse(StoryBase):
    id: UUID
    status: str
    consent: bool
    created_at: str

    class Config:
        from_attributes = True


@app.get("/")
def home():
    return {"message": "Sakhi API working!"}


@app.post("/user/register")
def register_user(req: RegisterRequest):
    try:
        user_row = create_user(
            name=req.name,
            email=req.email,
            phone_number=req.phone_number,
            password=req.password,
            role=req.role,
            preferred_language=req.preferred_language,
            relation=req.user_relation,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    user_id = user_row.get("user_id")

    return {"status": "success", "user_id": user_id, "user": user_row}


@app.post("/user/login")
def login(req: LoginRequest):
    """
    Authenticate user with email and password.
    Returns user profile if credentials are valid.
    """
    if not req.email or not req.password:
        raise HTTPException(status_code=400, detail="email and password are required")
    
    try:
        user = login_user(req.email, req.password)
        
        if user is None:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        return {
            "status": "success",
            "user_id": user.get("user_id"),
            "user": user
        }
        
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/sakhi/chat")
async def sakhi_chat(req: ChatRequest):
    # 1. Resolve or Create User
    user = None
    if req.user_id:
        user = get_user_profile(req.user_id)
    elif req.phone_number:
        user = get_user_by_phone(req.phone_number)

    # If new user (by phone), create them
    if not user:
        if req.phone_number:
            try:
                user = create_partial_user(req.phone_number)
                # Return Welcome Message
                return {
                    "reply": "Welcome to Sakhi! I'm here to support you on your health journey. ❤️ \n Let's get started! What should I call you? (Please type just your name, e.g., Deepthi)",
                    "mode": "onboarding"
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to register user: {e}")
        else:
             raise HTTPException(status_code=400, detail="user_id or phone_number is required")

    user_id = user.get("user_id")

    # 2. Check Onboarding Status (NULL checks)
    current_name = user.get("name")
    current_gender = user.get("gender")
    # Handle possible case variants for location
    current_location = user.get("location") or user.get("Location")

    msg = req.message.strip()

    # STATE 1: WAITING FOR NAME (User sent Name)
    if not current_name:
        update_user_profile(user_id, {"name": msg})
        return {
            "reply": f"Nice to meet you, {msg}! Can you let me know your gender ? (Please reply with 'Male' or 'Female')",
            "mode": "onboarding"
        }

    # STATE 2: WAITING FOR GENDER (User sent Gender)
    elif not current_gender:
        update_user_profile(user_id, {"gender": msg})
        return {
            "reply": "Got it. And finally, what's your location (City/Town)? (e.g., Vizag)",
            "mode": "onboarding"
        }

    # STATE 3: WAITING FOR LOCATION (User sent Location)
    elif not current_location:
        # Update both keys to be safe
        update_user_profile(user_id, {"location": msg}) 
        
        long_intro = (
            "Thank you! Your profile is all set.\n"
            "Welcome to JanmaSethu. I know that the journey to parenthood is filled with ups and downs, endless questions, and moments where you just need someone to listen.\n\n"
            "That is why I am here.\n\n"
            "I am Sakhi, and I want you to think of me not just as a tool, but as your trusted companion. I am your judgment-free friend, here to hold your hand through it all—from pre-parenthood to pregnancy and beyond.\n\n"
            "How can I help you today?\n\n"
            "💛 I am a Safe Space: Pour your heart out, ask me the \"silly\" questions, or just vent. I am here to listen without judgment.\n\n"
            "👩‍⚕️ I offer Doctor-Approved Trust: While I speak to you like a friend, my wisdom comes from validated medical professionals, so you can trust the guidance I give.\n\n"
            "🧠 I bring Visual Clarity: Confused by medical terms? I use simple infographics to make complex topics clear and easy to understand.\n\n"
            "My goal is to restore your faith and give you strength when you need it most. I am ready to listen whenever you are ready to talk.\n\n"
            "Visit the Website below for more information"
        )
        
        return {
            "reply": long_intro, 
            "mode": "onboarding_complete",
            "image": "Sakhi_intro.png"
        }

    # 3. Normal Flow
    try:
        save_user_message(user_id, req.message, req.language)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save user message: {e}")

    # STEP 0: Decide routing using Model Gateway
    route = model_gateway.decide_route(req.message)

    # Step 1: classify message
    try:
        classification = classify_message(req.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to classify message: {e}")

    detected_lang = classification.get("language", req.language)
    signal = classification.get("signal", "NO")

    # Fetch user name for personalization
    user_name = None
    try:
        profile = get_user_profile(user_id)
        if profile:
            user_name = profile.get("name")
    except Exception:
        user_name = None

    # Conversation history for both modes
    history = get_last_messages(user_id, limit=5)

    # ===== ROUTE 1: SLM_DIRECT (Small talk, no RAG) =====
    if route == Route.SLM_DIRECT:
        try:
            final_ans = await slm_client.generate_chat(
                message=req.message,
                language=detected_lang,
                user_name=user_name,
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to generate SLM chat response: {e}")
        
        try:
            save_sakhi_message(user_id, final_ans, detected_lang)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save Sakhi message: {e}")
        
        # Generate intent description dynamically
        intent = generate_intent(req.message)
        
        return {
            "intent": intent,
            "reply": final_ans,
            "mode": "general",
            "language": detected_lang,
            "route": "slm_direct"
        }
    
    # ===== ROUTE 2: SLM_RAG (Simple medical, RAG + SLM) =====
    elif route == Route.SLM_RAG:
        # Perform RAG search
        try:
            kb_results = hierarchical_rag_query(req.message)
            context_text = format_hierarchical_context(kb_results)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to perform RAG search: {e}")
        
        # Generate response using SLM with context
        try:
            final_ans = await slm_client.generate_rag_response(
                context=context_text,
                message=req.message,
                language=detected_lang,
                user_name=user_name,
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to generate SLM RAG response: {e}")
        
        try:
            save_sakhi_message(user_id, final_ans, detected_lang)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save Sakhi message: {e}")
        
        # Extract metadata from KB results
        infographic_url = None
        youtube_link = None
        if kb_results:
            for item in kb_results:
                if item.get("source_type") == "FAQ":
                    if item.get("infographic_url"):
                        infographic_url = item["infographic_url"]
                    if item.get("youtube_link"):
                        youtube_link = item["youtube_link"]
                    if infographic_url or youtube_link:
                        break
        
        # Generate intent description dynamically
        intent = generate_intent(req.message)
        
        response_payload = {
            "intent": intent,
            "reply": final_ans,
            "mode": "medical",
            "language": detected_lang,
            "youtube_link": youtube_link,
            "infographic_url": infographic_url,
            "route": "slm_rag"
        }
        print(f"Response Payload: {response_payload}")
        return response_payload

    # Keep existing small talk logic as fallback (though routing should handle this)
    if signal != "YES":
        # Small-talk mode: no RAG
        try:
            final_ans = generate_smalltalk_response(
                req.message,
                detected_lang,
                history,
                user_name=user_name,
                store_to_kb=False,
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to generate small-talk response: {e}")

        try:
            save_sakhi_message(user_id, final_ans, detected_lang)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save Sakhi message: {e}")

        return {"reply": final_ans, "mode": "general", "language": detected_lang}

    # ===== ROUTE 3: OPENAI_RAG (Complex medical or default, RAG + GPT-4) =====
    # Medical mode: RAG
    try:
        final_ans, _kb = generate_medical_response(
            prompt=req.message,
            target_lang=detected_lang,
            history=history,
            user_name=user_name,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate medical response: {e}")

    try:
        save_sakhi_message(user_id, final_ans, detected_lang)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save Sakhi message: {e}")

    # Extract infographic_url and youtube_link if available in kb_results
    infographic_url = None
    youtube_link = None

    if _kb:
        for item in _kb:
            if item.get("source_type") == "FAQ":
                if item.get("infographic_url"):
                    infographic_url = item["infographic_url"]
                if item.get("youtube_link"):
                    youtube_link = item["youtube_link"]
                # If we found an FAQ match, we likely want to use its metadata
                if infographic_url or youtube_link:
                    break

    # Generate intent description dynamically
    intent = generate_intent(req.message)
    
    response_payload = {
        "intent": intent,
        "reply": final_ans, 
        "mode": "medical", 
        "language": detected_lang,
        "youtube_link": youtube_link,
        "infographic_url": infographic_url,
        "route": "openai_rag"
    }
    print(f"Response Payload: {response_payload}")
    return response_payload


@app.post("/user/answers")
def save_user_answers(req: UserAnswersRequest):
    if not req.user_id:
        raise HTTPException(status_code=400, detail="user_id is required")
    if not req.answers:
        raise HTTPException(status_code=400, detail="answers cannot be empty")

    for ans in req.answers:
        if not ans.question_key:
            raise HTTPException(status_code=400, detail="question_key is required for each answer")
        if not ans.selected_options:
            raise HTTPException(status_code=400, detail="selected_options must be non-empty for each answer")

    try:
        saved_count, _ = save_bulk_answers(
            user_id=req.user_id,
            answers=[a.dict() for a in req.answers],
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"status": "success", "saved": saved_count}


@app.post("/user/relation")
def set_user_relation(req: UpdateRelationRequest):
    if not req.user_id or not req.relation:
        raise HTTPException(status_code=400, detail="user_id and relation are required")

    try:
        update_relation(req.user_id, req.relation)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"status": "success"}


@app.post("/user/preferred-language")
def set_user_preferred_language(req: UpdatePreferredLanguageRequest):
    if not req.user_id or not req.preferred_language:
        raise HTTPException(status_code=400, detail="user_id and preferred_language are required")

    try:
        update_preferred_language(req.user_id, req.preferred_language)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"status": "success"}


@app.post("/api/user/journey")
def update_user_journey(req: JourneyUpdateRequest):
    if not req.user_id:
        raise HTTPException(status_code=400, detail="user_id is required")
    if not req.stage:
        raise HTTPException(status_code=400, detail="stage is required")

    # Validate stage enum (optional, but good for data integrity)
    valid_stages = ["TTC", "PREGNANT", "PARENT"]
    if req.stage not in valid_stages:
        raise HTTPException(status_code=400, detail=f"Invalid stage. Must be one of {valid_stages}")

    updates = {
        "sakhi_journey_stage": req.stage,
        "sakhi_journey_date": req.date,
        "sakhi_journey_date_type": req.date_type
    }

    try:
        # Remove None values to avoid overwriting with null if that's desired, 
        # or keep them to allow clearing values. 
        # Requirement implies updating user profile with these values.
        # Clean up None values just in case we don't want to unset date if not provided?
        # Re-reading: Payload: { stage: string, date: string }
        # logic: update user profile.
        
        update_user_profile(req.user_id, updates)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"status": "success", "updates": updates}


@app.get("/api/user/me")
def get_current_user_profile(user_id: str):
    """
    Fetch current user profile including journey details.
    """
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id parameter is required")

    try:
        user = get_user_profile(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Ensure we return the new fields. 
        # get_user_profile does select="*" so it should be there automatically 
        # once the DB is updated.
        return user
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/onboarding/step")
def onboarding_step(req: OnboardingStepRequest):
    """
    Get next question in onboarding flow.
    Returns either next question metadata or completion payload.
    """
    if not req.parent_profile_id or not req.relationship_type:
        raise HTTPException(
            status_code=400,
            detail="parent_profile_id and relationship_type are required"
        )
    
    try:
        # Create OnboardingRequest object
        onboarding_request = OnboardingRequest(
            parent_profile_id=req.parent_profile_id,
            relationship_type=req.relationship_type,
            current_step=req.current_step,
            answers_json=req.answers_json or {}
        )
        
        # Get next question or completion status
        response = get_next_question(onboarding_request)
        
        return response.to_dict()
        
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/onboarding/complete")
def onboarding_complete(req: OnboardingCompleteRequest):
    """
    Store completed onboarding answers to parent_profiles table.
    """
    # Log incoming request for debugging
    print(f"[onboarding/complete] Received request:")
    print(f"  user_id: {req.user_id}")
    print(f"  parent_profile_id: {req.parent_profile_id}")
    print(f"  target_user_id: {req.target_user_id}")
    print(f"  relationship_type: {req.relationship_type}")
    print(f"  answers_json: {req.answers_json}")
    
    if not req.user_id or not req.relationship_type:
        raise HTTPException(
            status_code=400,
            detail="user_id and relationship_type are required"
        )
    
    try:
        profile = None
        
        # Try to update existing profile if parent_profile_id is provided
        if req.parent_profile_id:
            print(f"[onboarding/complete] Attempting to update existing profile: {req.parent_profile_id}")
            result = update_parent_profile_answers(
                parent_profile_id=req.parent_profile_id,
                answers_json=req.answers_json
            )
            # Extract dict from result
            if isinstance(result, list) and len(result) > 0:
                profile = result[0]
            elif isinstance(result, dict):
                profile = result
            
            if profile:
                print(f"[onboarding/complete] Updated existing profile successfully")
            else:
                print(f"[onboarding/complete] Profile not found, will create new one")
        
        # Create new profile if update failed or no parent_profile_id provided
        if not profile:
            print(f"[onboarding/complete] Creating new profile for user: {req.user_id}")
            result = create_parent_profile(
                user_id=req.user_id,
                target_user_id=req.target_user_id,
                relationship_type=req.relationship_type,
                answers_json=req.answers_json
            )
            # Extract dict from result
            if isinstance(result, list) and len(result) > 0:
                profile = result[0]
            elif isinstance(result, dict):
                profile = result
            else:
                raise Exception(f"Unexpected response from create_parent_profile: {result}")
        
        print(f"[onboarding/complete] Success! Profile: {profile}")
        
        # Safely get the parent_profile_id
        parent_profile_id = profile.get("parent_profile_id") if isinstance(profile, dict) else None
        
        return {
            "status": "success",
            "parent_profile_id": parent_profile_id,
            "profile": profile
        }
        
    except Exception as e:
        import traceback
        print(f"[onboarding/complete] ERROR: {str(e)}")
        print(f"[onboarding/complete] Traceback:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


# ================== KNOWLEDGE HUB ROUTES ==================
@app.get("/api/knowledge-hub/", response_model=list[KnowledgeHubResponse], tags=["knowledge-hub"])
def get_knowledge_hub_items(
    lang: str = "en",
    life_stage_id: int | None = None,
    perspective_id: int | None = None,
    life_stage: int | None = None,
    perspective: int | None = None,
    lifeStage: int | None = None,
    is_featured: bool | None = None,
    perPage: int = 100,
    search: str | None = None
):
    """Get all knowledge hub items with language support and filtering"""
    from supabase_client import supabase
    query = supabase.table("sakhi_knowledge_hub").select("*")
    
    if search:
        query = query.ilike("title", f"%{search}%")
    
    ls_id = life_stage_id if life_stage_id is not None else (life_stage if life_stage is not None else lifeStage)
    p_id = perspective_id if perspective_id is not None else perspective
    
    if ls_id is not None:
        query = query.eq("life_stage_id", ls_id)
    if p_id is not None:
        query = query.eq("perspective_id", p_id)
    if is_featured is not None:
        query = query.eq("is_featured", is_featured)
        
    import time
    import httpx
    
    response = None
    retries = 3
    for i in range(retries):
        try:
            response = query.order("published_at", desc=True).limit(perPage).execute()
            break
        except Exception as e:
            if i == retries - 1:
                print(f"Failed to fetch knowledge hub items after {retries} attempts: {e}")
                raise e
            print(f"Attempt {i+1} failed: {e}. Retrying...")
            time.sleep(0.5 * (i + 1))
    
    items = []
    for item in response.data:
        if lang == "te":
            item["title"] = item.get("title_te") or item.get("title")
            item["summary"] = item.get("summary_te") or item.get("summary")
            item["content"] = item.get("content_te") or item.get("content")
        items.append(KnowledgeHubResponse.model_validate(item))
        
    return items


@app.get("/api/knowledge-hub/recommendations", response_model=list[KnowledgeHubResponse], tags=["knowledge-hub"])
def get_knowledge_hub_recommendations(
    stage: str | None = None,
    lens: str | None = None,
    userId: str | None = None,
    lang: str = "en",
    limit: int = 3
):
    """
    Get recommended knowledge hub items.
    Priority:
    1. Featured items matching stage and lens
    2. Featured items matching stage only
    3. Recent items matching stage
    4. Any featured items
    """
    from supabase_client import supabase
    import time
    
    # Map string stage/lens to IDs if necessary (assuming frontend sends names like 'ttc', 'medical')
    # Or frontend can send IDs. Let's assume frontend sends IDs or we handle strings.
    # For now, let's map common strings to IDs if the DB uses IDs.
    # Based on previous context, DB uses IDs (1, 2, 3...)
    
    stage_map = {
        'ttc': 1, 'pregnancy': 2, 'postpartum': 3, 'newborn': 4, 'early-years': 5,
        'trying-to-conceive': 1, 'pregnant': 2, 'parent': 5 # simplified mapping
    }
    lens_map = {
        'medical': 1, 'social': 2, 'nutrition': 3, 'financial': 4
    }
    
    ls_id = None
    if stage:
        ls_id = stage_map.get(stage.lower(), None)
        # If not in map, maybe it's already an ID (int)
        if ls_id is None and stage.isdigit():
            ls_id = int(stage)

    p_id = None
    if lens:
        p_id = lens_map.get(lens.lower(), None)
        if p_id is None and lens.isdigit():
            p_id = int(lens)

    items = []
    seen_ids = set()

    def fetch_and_add(query_base, limit_needed):
        if limit_needed <= 0:
            return
        
        # Add retry logic here as well
        resp = None
        for i in range(3):
            try:
                resp = query_base.limit(limit_needed).execute()
                break
            except Exception as e:
                if i == 2: print(f"Rec fetch failed: {e}")
                time.sleep(0.5)
        
        if resp and resp.data:
            for item in resp.data:
                if item['id'] not in seen_ids:
                    if lang == "te":
                        item["title"] = item.get("title_te") or item.get("title")
                        item["summary"] = item.get("summary_te") or item.get("summary")
                        item["content"] = item.get("content_te") or item.get("content")
                    
                    items.append(KnowledgeHubResponse.model_validate(item))
                    seen_ids.add(item['id'])

    # Strategy 1: Featured + Stage + Lens
    if len(items) < limit and ls_id and p_id:
        q = supabase.table("sakhi_knowledge_hub").select("*").eq("is_featured", True).eq("life_stage_id", ls_id).eq("perspective_id", p_id)
        fetch_and_add(q, limit - len(items))

    # Strategy 2: Featured + Stage
    if len(items) < limit and ls_id:
        q = supabase.table("sakhi_knowledge_hub").select("*").eq("is_featured", True).eq("life_stage_id", ls_id)
        if p_id: q = q.neq("perspective_id", p_id) # Avoid dups if possible, though seen_ids handles it
        fetch_and_add(q, limit - len(items))

    # Strategy 3: Any Stage Match (Recent)
    if len(items) < limit and ls_id:
        q = supabase.table("sakhi_knowledge_hub").select("*").eq("life_stage_id", ls_id).order("published_at", desc=True)
        fetch_and_add(q, limit - len(items))

    # Strategy 4: Any Featured
    if len(items) < limit:
        q = supabase.table("sakhi_knowledge_hub").select("*").eq("is_featured", True).order("published_at", desc=True)
        fetch_and_add(q, limit - len(items))
        
    # Strategy 5: Fallback to any recent
    if len(items) < limit:
        q = supabase.table("sakhi_knowledge_hub").select("*").order("published_at", desc=True)
        fetch_and_add(q, limit - len(items))

    return items


@app.get("/api/knowledge-hub/{slug}", response_model=KnowledgeHubResponse, tags=["knowledge-hub"])
def get_knowledge_hub_item_by_slug(slug: str, lang: str = "en"):
    """Get a single knowledge hub item by slug with language support"""
    from supabase_client import supabase
    
    import time
    response = None
    for i in range(3):
        try:
            response = supabase.table("sakhi_knowledge_hub").select("*").eq("slug", slug).limit(1).execute()
            break
        except Exception:
            time.sleep(0.5)
            
    if not response or not response.data:
        raise HTTPException(status_code=404, detail="Knowledge Hub item not found")
    
    item = response.data[0]
    if lang == "te":
        item["title"] = item.get("title_te") or item.get("title")
        item["summary"] = item.get("summary_te") or item.get("summary")
        item["content"] = item.get("content_te") or item.get("content")
        
    return KnowledgeHubResponse.model_validate(item)


# ================== SUCCESS STORIES ROUTES ==================
STORIES_TABLE = "sakhi_success_stories"


@app.post("/stories/draft", status_code=status.HTTP_201_CREATED, tags=["stories"])
@app.post("/stories/", status_code=status.HTTP_201_CREATED, tags=["stories"])
async def create_story_draft(story_in: StoryCreate):
    """Create a new story draft"""
    from supabase_client import supabase
    from modules.story_generator import process_new_story

    data = story_in.model_dump()
    
    # ==================== FIELD MAPPING ====================
    # Frontend Field → DB Column
    
    # 1. share_type → always public
    data["share_type"] = ShareType.PUBLIC

    # 2. emotionDetails → emotion_description
    if not data.get("emotion_description") and data.get("emotionDetails"):
        data["emotion_description"] = data.get("emotionDetails")

    # 3. outcome → journey_outcome
    if not data.get("journey_outcome") and data.get("outcome"):
        data["journey_outcome"] = data.get("outcome")

    # 4. outcomeDetails → more_details
    if not data.get("more_details") and data.get("outcomeDetails"):
        data["more_details"] = data.get("outcomeDetails")

    # 5. messageToOthers → hope_message
    if not data.get("hope_message") and data.get("messageToOthers"):
        data["hope_message"] = data.get("messageToOthers")

    # 6. uploadedImage → photo_url
    if not data.get("photo_url") and data.get("uploadedImage"):
        data["photo_url"] = data.get("uploadedImage")

    # 7. consent_accepted → consent
    if "consent_accepted" in data:
        data["consent"] = bool(data.get("consent_accepted")) or str(data.get("consent_accepted")).lower() == "true"
    elif "consent" not in data:
        data["consent"] = False

    # 8. language normalization ("English" → "en")
    lang = data.get("language", "en")
    lang_map = {"english": "en", "hindi": "hi", "telugu": "te", "tamil": "ta", "malayalam": "ml", "marathi": "mr", "kannada": "kn", "bengali": "bn"}
    data["language"] = lang_map.get(str(lang).lower(), lang if len(str(lang)) == 2 else "en")

    # Set defaults
    data["status"] = "published"

    # ==================== CLEANUP NON-DB FIELDS ====================
    non_db_fields = [
        "isAnonymous",
        "emotionDetails",
        "outcome",
        "outcomeDetails",
        "messageToOthers",
        "uploadedImage",
        "consent_accepted",
        "duration",  # Sometimes sent as alias for journey_duration
    ]
    for key in non_db_fields:
        if key in data:
            del data[key]
    
    response = supabase.table(STORIES_TABLE).insert(data).execute()
    
    if response.data:
        # Generate narrative immediately
        updated_story = await process_new_story(response.data[0]['id'], response.data[0])
        story_response = StoryResponse.model_validate(updated_story)
        return {"message": "Story saved", "data": story_response.model_dump()}
        
    story_response = StoryResponse.model_validate(response.data[0])
    return {"message": "Story saved", "data": story_response.model_dump()}


@app.post("/stories/consent", response_model=StoryResponse, tags=["stories"])
async def record_consent(consent_in: StoryConsent):
    """Record user consent for a story"""
    from supabase_client import supabase
    response = supabase.table(STORIES_TABLE).update({"consent": True}).eq("id", str(consent_in.id)).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Story not found")
    return StoryResponse.model_validate(response.data[0])


@app.get("/stories/", response_model=list[StoryResponse], tags=["stories"])
async def get_published_stories():
    """Get all published stories"""
    from supabase_client import supabase
    response = supabase.table(STORIES_TABLE).select("*").eq("status", "published").order("created_at", desc=True).execute()
    return [StoryResponse.model_validate(item) for item in response.data]


@app.get("/stories/{id}", response_model=StoryResponse, tags=["stories"])
async def get_story_by_id(id: UUID):
    """Get a story by ID"""
    from supabase_client import supabase
    response = supabase.table(STORIES_TABLE).select("*").eq("id", str(id)).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Story not found")
    return StoryResponse.model_validate(response.data[0])


@app.put("/stories/{id}/status", response_model=StoryResponse, tags=["stories"])
async def update_story_status(id: UUID, status_in: StoryUpdateStatus):
    """Update story status"""
    from supabase_client import supabase
    response = supabase.table(STORIES_TABLE).update({"status": status_in.status}).eq("id", str(id)).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Story not found")
    return StoryResponse.model_validate(response.data[0])


@app.post("/stories/upload", status_code=status.HTTP_201_CREATED, tags=["stories"])
async def upload_photo(photo: UploadFile = File(...)):
    """Upload a photo for a story"""
    unique_name = f"{uuid_module.uuid4()}-{photo.filename}".replace(" ", "-")
    base_url = "https://example-bucket.s3.amazonaws.com/uploads"
    return {"photo_url": f"{base_url}/{unique_name}"}