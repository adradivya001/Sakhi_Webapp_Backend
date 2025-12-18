# modules/model_gateway.py
import logging
from enum import Enum
from typing import List
import numpy as np

from rag import generate_embedding

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Route(Enum):
    """Routing destinations for user queries."""
    SLM_DIRECT = "slm_direct"  # Small talk, no RAG needed
    SLM_RAG = "slm_rag"  # Simple medical, RAG + SLM
    OPENAI_RAG = "openai_rag"  # Complex medical, RAG + OpenAI


class ModelGateway:
    """
    Semantic router that directs user queries to appropriate model endpoints
    based on vector similarity to predefined anchor categories.
    """
    
    # Anchor examples for each category
    SMALL_TALK_EXAMPLES = [
        "hi",
        "hello",
        "hey there",
        "hey",
        "thanks",
        "thank you",
        "thanks a lot",
        "thank you so much",
        "who are you",
        "what is your name",
        "may i know your name",
        "how are you",
        "how are you doing",
        "how's it going",
        "what's up",
        "good morning",
        "good afternoon",
        "good evening",
        "good night",
        "bye",
        "goodbye",
        "see you",
        "see you later",
        "talk to you later",
        "nice to meet you",
        "pleased to meet you",
        "ok",
        "okay",
        "cool",
        "great",
        "awesome",
        "no problem",
        "you're welcome",
        "welcome",
    ]
    
    MEDICAL_SIMPLE_EXAMPLES = {
        "IVF": [
            "what is ivf",
            "how ivf treatment works",
            "ivf success rate",
            "ivf process step by step",
            "ivf treatment cost",
            "is ivf painful",
            "ivf risks",
            "who needs ivf",
        ],
        "IUI": [
            "what is iui",
            "iui treatment process",
            "iui success rate",
            "difference between iui and ivf",
            "iui cost",
            "is iui painful",
        ],
        "ICSI": [
            "what is icsi",
            "icsi vs ivf",
            "when is icsi needed",
            "icsi success rate",
            "icsi treatment steps",
        ],
        "FERTILITY": [
            "what is fertility",
            "how to improve fertility naturally",
            "fertility age limit",
            "fertility tests for women",
            "fertility tests for men",
        ],
        "FEMALE_INFERTILITY": [
            "what causes female infertility",
            "female infertility symptoms",
            "tests for female infertility",
            "can female infertility be treated",
        ],
        "MALE_INFERTILITY": [
            "what causes male infertility",
            "male infertility symptoms",
            "sperm count test",
            "how to improve sperm quality",
        ],
        "LAPAROSCOPY": [
            "what is laparoscopy",
            "laparoscopy for infertility",
            "is laparoscopy surgery painful",
            "recovery time after laparoscopy",
        ],
        "POSTPARTUM": [
            "what is postpartum period",
            "postpartum recovery tips",
            "postpartum depression symptoms",
            "diet after delivery",
        ],
        "CONCEPTION": [
            "what is conception",
            "how conception happens",
            "best time for conception",
            "how long does conception take",
        ],
        "EMBRYO_FREEZING": [
            "what is embryo freezing",
            "why embryo freezing is done",
            "how long embryos can be frozen",
            "is embryo freezing safe",
        ],
        "SPERM_FREEZING": [
            "what is sperm freezing",
            "how sperm freezing works",
            "how long sperm can be frozen",
            "who should freeze sperm",
        ],
        "EGG_FREEZING": [
            "what is egg freezing",
            "best age for egg freezing",
            "egg freezing process",
            "egg freezing success rate",
        ],
        "PCOS": [
            "what is pcos",
            "pcos symptoms",
            "pcos treatment",
            "pcos diet plan",
            "can pcos cause infertility",
        ],
        "PCOD": [
            "what is pcod",
            "pcod symptoms",
            "pcod vs pcos",
            "pcod treatment",
        ],
        "AYURVEDA_TREATMENTS": [
            "ayurveda treatment for infertility",
            "ayurvedic remedies for pcos",
            "is ayurveda safe for fertility",
            "ayurveda diet for pregnancy",
        ],
        "HYSTEROSCOPY": [
            "what is hysteroscopy",
            "why hysteroscopy is done",
            "hysteroscopy recovery time",
            "is hysteroscopy painful",
        ],
        "PREGNANCY": [
            "early pregnancy symptoms",
            "pregnancy diet tips",
            "safe exercises during pregnancy",
            "pregnancy tests accuracy",
        ],
        "SURROGACY": [
            "what is surrogacy",
            "surrogacy process",
            "who needs surrogacy",
            "is surrogacy legal in india",
        ],
        "C_SECTION": [
            "what is c section",
            "recovery after c section",
            "c section vs normal delivery",
            "when c section is needed",
        ],
        "NATURAL_BIRTH": [
            "what is natural birth",
            "benefits of normal delivery",
            "pain relief for natural birth",
            "preparing for natural delivery",
        ],
        "NUTRITION_AND_TESTS": [
            "nutrition needed for ivf",
            "fertility blood tests",
            "hormone tests for pregnancy",
            "vitamins needed for conception",
        ],
        "MEDICATION_AND_EXERCISES": [
            "fertility medicines for women",
            "medicines to improve sperm count",
            "exercises for fertility",
            "yoga for pregnancy",
        ],
    }
    
    MEDICAL_COMPLEX_EXAMPLES = [
        "severe bleeding",
        "baby not moving",
        "sharp abdominal pain",
        "emergency symptoms",
        "heavy bleeding in pregnancy",
        "sudden severe headache",
        "vision problems pregnancy",
        "chest pain difficulty breathing",
        "preeclampsia symptoms",
        "miscarriage signs",
    ]
    
    FACILITY_INFO_EXAMPLES = [
        "what is the phone number for vijayawada branch",
        "address of hyderabad clinic",
        "where is your office located",
        "contact number for the clinic",
        "how can I reach the xyz branch",
        "clinic timings",
        "where are you located",
        "phone number for appointment",
        "address for fertility center",
        "branch locations",
        "where are the clinics in vizag",
        "vizag clinic address",
        "visakhapatnam branch location",
        "show me clinics near me",
        "clinic contact details",
        "where can I find your clinic",
        "nearest clinic location",
        "fertility center address",
        "branch office contact",
        "how to reach the clinic",
    ]
    
    # Similarity thresholds for routing decisions
    SMALL_TALK_THRESHOLD = 0.75  # High confidence needed for small talk
    MEDICAL_SIMPLE_THRESHOLD = 0.65  # Moderate confidence for simple medical
    FACILITY_INFO_THRESHOLD = 0.50  # Lower threshold for facility/location queries to catch more
    
    def __init__(self):
        """Initialize the gateway by computing anchor vectors."""
        logger.info("Initializing ModelGateway with anchor vectors...")
        
        # Compute mean anchor vectors for each category
        self.small_talk_anchor = self._compute_mean_vector(self.SMALL_TALK_EXAMPLES)
        self.medical_simple_anchor = self._compute_mean_vector(self.MEDICAL_SIMPLE_EXAMPLES)
        self.medical_complex_anchor = self._compute_mean_vector(self.MEDICAL_COMPLEX_EXAMPLES)
        self.facility_info_anchor = self._compute_mean_vector(self.FACILITY_INFO_EXAMPLES)
        
        logger.info("ModelGateway initialized successfully")
    
    def _compute_mean_vector(self, examples: List[str]) -> np.ndarray:
        """
        Compute the mean embedding vector for a list of example texts.
        
        Args:
            examples: List of example texts for a category
            
        Returns:
            Mean embedding vector as numpy array
        """
        embeddings = [generate_embedding(example) for example in examples]
        mean_vector = np.mean(embeddings, axis=0)
        return mean_vector
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two vectors.
        
        Args:
            vec1: First vector
            vec2: Second vector
            
        Returns:
            Cosine similarity score (0 to 1)
        """
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def decide_route(self, user_text: str) -> Route:
        """
        Determine the appropriate route for a user query based on semantic similarity.
        
        Args:
            user_text: User's input message
            
        Returns:
            Route enum indicating which model to use
        """
        # Generate embedding for user input
        user_vector = np.array(generate_embedding(user_text))
        
        # Calculate similarities to each anchor
        small_talk_sim = self._cosine_similarity(user_vector, self.small_talk_anchor)
        medical_simple_sim = self._cosine_similarity(user_vector, self.medical_simple_anchor)
        medical_complex_sim = self._cosine_similarity(user_vector, self.medical_complex_anchor)
        facility_info_sim = self._cosine_similarity(user_vector, self.facility_info_anchor)
        
        # Log similarity scores for debugging
        logger.info(f"Query: '{user_text[:50]}...'")
        logger.info(f"Similarity scores - Small Talk: {small_talk_sim:.3f}, "
                   f"Medical Simple: {medical_simple_sim:.3f}, "
                   f"Medical Complex: {medical_complex_sim:.3f}, "
                   f"Facility Info: {facility_info_sim:.3f}")
        
        # Routing logic based on thresholds and highest similarity
        if small_talk_sim >= self.SMALL_TALK_THRESHOLD:
            logger.info(f"→ Routing to: SLM_DIRECT (small talk detected)")
            return Route.SLM_DIRECT
        
        # Check for facility/location queries FIRST - route to SLM since it has this info
        # This takes priority over medical queries to ensure clinic info is retrieved
        if facility_info_sim >= self.FACILITY_INFO_THRESHOLD:
            logger.info(f"→ Routing to: SLM_RAG (facility/location info query)")
            return Route.SLM_RAG
        
        # Only check medical queries if it's not a facility query
        if medical_complex_sim >= medical_simple_sim:
            # Complex medical or default to safest option
            logger.info(f"→ Routing to: OPENAI_RAG (complex medical or default)")
            return Route.OPENAI_RAG
        
        if medical_simple_sim >= self.MEDICAL_SIMPLE_THRESHOLD:
            logger.info(f"→ Routing to: SLM_RAG (simple medical query)")
            return Route.SLM_RAG
        
        # Default to OpenAI for safety when confidence is low
        logger.info(f"→ Routing to: OPENAI_RAG (low confidence, defaulting to safe option)")
        return Route.OPENAI_RAG
    
    def get_intent_description(self, user_text: str, route: Route) -> str:
        """
        Generate a warm, empathetic, patient-facing intent description.
        
        Args:
            user_text: User's input message
            route: The determined route for the query
            
        Returns:
            Empathetic, application-voice intent description
        """
        user_lower = user_text.lower()
        
        # Check for specific medical topics
        topic_intents = {
            "IVF": "We're here to gently guide you through understanding IVF, so you feel informed and supported every step of the way.",
            "IUI": "We want to help you understand IUI in a way that feels clear and reassuring as you explore your options.",
            "ICSI": "We're here to explain ICSI with care, helping you feel confident and informed about this treatment approach.",
            "PCOS": "We understand that PCOS can feel overwhelming, and we're here to provide gentle, clear information to support you.",
            "PCOD": "We're here to help you understand PCOD with compassion, offering information that feels supportive and easy to understand.",
            "Fertility": "We're here to walk alongside you on your fertility journey, offering information with warmth and understanding.",
            "Pregnancy": "We're here to support you with caring information about pregnancy, helping you feel confident and nurtured.",
            "Egg Freezing": "We're here to help you understand egg freezing in a supportive way, so you can make decisions that feel right for you.",
            "Sperm Freezing": "We're here to provide clear, compassionate guidance about sperm freezing to help you plan for the future.",
            "Embryo Freezing": "We're here to gently explain embryo freezing, helping you understand your options with care and clarity.",
            "Laparoscopy": "We're here to help you understand laparoscopy with reassurance, so you know what to expect and feel prepared.",
            "Hysteroscopy": "We want to help you feel at ease by explaining hysteroscopy in a gentle, supportive manner.",
            "Surrogacy": "We're here to provide thoughtful, compassionate information about surrogacy to help you explore this path.",
            "C-Section": "We're here to help you understand C-sections with care, so you feel informed and prepared for your journey.",
            "Natural Birth": "We're here to support your understanding of natural birth with warmth and encouragement.",
            "Postpartum": "We're here to gently guide you through the postpartum period with care and understanding.",
            "Male Infertility": "We're here to provide supportive, compassionate information about male fertility, helping you feel understood.",
            "Female Infertility": "We're here to walk with you through understanding female fertility with empathy and care.",
        }
        
        # Check for detected topic
        topic_keywords = {
            "IVF": ["ivf", "in vitro", "vitro fertilization"],
            "IUI": ["iui", "intrauterine insemination"],
            "ICSI": ["icsi", "intracytoplasmic"],
            "PCOS": ["pcos", "polycystic ovary"],
            "PCOD": ["pcod", "polycystic ovarian disease"],
            "Fertility": ["fertility", "fertile", "infertility", "infertile"],
            "Pregnancy": ["pregnancy", "pregnant", "conception", "conceive"],
            "Egg Freezing": ["egg freezing", "oocyte freezing", "freeze eggs"],
            "Sperm Freezing": ["sperm freezing", "freeze sperm"],
            "Embryo Freezing": ["embryo freezing", "freeze embryo"],
            "Laparoscopy": ["laparoscopy", "laparoscopic"],
            "Hysteroscopy": ["hysteroscopy", "hysteroscopic"],
            "Surrogacy": ["surrogacy", "surrogate"],
            "C-Section": ["c section", "c-section", "cesarean", "caesarean"],
            "Natural Birth": ["natural birth", "normal delivery", "vaginal delivery"],
            "Postpartum": ["postpartum", "after delivery", "post pregnancy"],
            "Male Infertility": ["male infertility", "sperm count", "sperm quality", "low sperm"],
            "Female Infertility": ["female infertility", "ovulation", "anovulation"],
        }
        
        detected_topic = None
        for topic, keywords in topic_keywords.items():
            if any(kw in user_lower for kw in keywords):
                detected_topic = topic
                break
        
        # Generate intent based on route and topic
        if route == Route.SLM_DIRECT:
            # Small talk / greetings
            greetings = ["hi", "hello", "hey", "good morning", "good afternoon", "good evening"]
            thanks = ["thank", "thanks"]
            bye = ["bye", "goodbye", "see you"]
            
            if any(g in user_lower for g in greetings):
                return "We're so glad you're here — this is a safe space where you can ask anything, and we're ready to listen."
            elif any(t in user_lower for t in thanks):
                return "We're touched by your gratitude, and we're always here whenever you need support or guidance."
            elif any(b in user_lower for b in bye):
                return "We're here whenever you need us — take care of yourself, and remember, you're never alone on this journey."
            else:
                return "We're here to listen and support you with warmth and understanding, no matter what's on your mind."
        
        elif route == Route.SLM_RAG:
            # Check for facility/location queries
            facility_keywords = ["clinic", "address", "location", "phone", "contact", "branch", "vizag", "hyderabad", "vijayawada", "where", "timing"]
            if any(fk in user_lower for fk in facility_keywords):
                return "We want to make it easy for you to connect with us, so here's the information you need to reach our care team."
            
            if detected_topic:
                return topic_intents.get(detected_topic, "We're here to provide you with clear, caring information to help you feel more confident and supported.")
            return "We're here to provide you with clear, caring information to help you feel more confident and supported."
        
        elif route == Route.OPENAI_RAG:
            if detected_topic:
                return topic_intents.get(detected_topic, "We're here to offer you thoughtful, detailed guidance to help you understand your journey with clarity and compassion.")
            return "We're here to offer you thoughtful, detailed guidance to help you understand your journey with clarity and compassion."
        
        return "We're here to support you with care and understanding — you're in a safe space."


# Module-level singleton instance
_gateway_instance = None


def get_model_gateway() -> ModelGateway:
    """
    Get or create a singleton ModelGateway instance.
    
    Returns:
        ModelGateway instance
    """
    global _gateway_instance
    if _gateway_instance is None:
        _gateway_instance = ModelGateway()
    return _gateway_instance