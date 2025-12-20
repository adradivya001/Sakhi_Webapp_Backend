# main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from modules.user_profile import (
    create_user,
    update_preferred_language,
    update_relation,
    get_user_profile,
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
from search_hierarchical import hierarchical_rag_query, format_hierarchical_context

app = FastAPI()

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


# Login model
class LoginRequest(BaseModel):
    email: str
    password: str


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

    print(f"DEBUG: User={user_id}, Name={current_name}, Gender={current_gender}, Location={current_location}")

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
    import traceback
    
    print(f"DEBUG: Received onboarding complete request")
    print(f"DEBUG: user_id={req.user_id}, relationship={req.relationship_type}")
    print(f"DEBUG: parent_profile_id={req.parent_profile_id}")
    print(f"DEBUG: answers_json={req.answers_json}")
    
    if not req.user_id or not req.relationship_type:
        raise HTTPException(
            status_code=400,
            detail="user_id and relationship_type are required"
        )
    
    try:
        # Create or update parent profile
        if req.parent_profile_id:
            # Update existing profile
            print(f"DEBUG: Updating existing profile")
            profile = update_parent_profile_answers(
                parent_profile_id=req.parent_profile_id,
                answers_json=req.answers_json
            )
        else:
            # Create new profile
            print(f"DEBUG: Creating new profile")
            profile = create_parent_profile(
                user_id=req.user_id,
                target_user_id=req.target_user_id,
                relationship_type=req.relationship_type,
                answers_json=req.answers_json
            )
        
        print(f"DEBUG: Success! Profile={profile}")
        return {
            "status": "success",
            "parent_profile_id": profile.get("parent_profile"),
            "profile": profile
        }
        
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"ERROR in onboarding_complete: {e}")
        print(f"TRACEBACK: {error_trace}")
        raise HTTPException(status_code=500, detail=f"{str(e)} | Trace: {error_trace[:500]}")
