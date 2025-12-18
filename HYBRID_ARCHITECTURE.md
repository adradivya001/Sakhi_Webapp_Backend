# Hybrid Model Architecture - Implementation Summary

## ✅ Implementation Complete

The Sakhi WhatsApp chatbot has been successfully refactored to use a **Hybrid Model Architecture** with semantic routing. User queries are now intelligently routed to either a Small Language Model (SLM) or OpenAI GPT-4 based on query complexity.

## 📁 New Files Created

### 1. `modules/model_gateway.py`
**Semantic Router with Vector-Based Classification**

- **Route Enum**: Defines three routing destinations:
  - `SLM_DIRECT`: Small talk queries (no RAG needed)
  - `SLM_RAG`: Simple medical queries (RAG + SLM)
  - `OPENAI_RAG`: Complex medical queries (RAG + GPT-4)

- **Anchor Vectors**: Pre-computed mean embeddings for three categories:
  - **SMALL_TALK**: Greetings, thanks, identity questions (10 examples)
  - **MEDICAL_SIMPLE**: Basic medical info queries (10 examples)
  - **MEDICAL_COMPLEX**: Emergency symptoms, severe conditions (10 examples)

- **Routing Logic**:
  1. Converts user input to embedding vector using `rag.generate_embedding()`
  2. Calculates cosine similarity to each anchor vector
  3. Routes based on thresholds:
     - Small talk threshold: 0.75 (high confidence required)
     - Medical simple threshold: 0.65 (moderate confidence)
     - Default: Routes to OPENAI_RAG for safety

- **Logging**: All routing decisions are logged with similarity scores for debugging

### 2. `modules/slm_client.py`
**Async SLM Client with Mock Implementation**

- **Two Methods**:
  - `generate_chat()`: Direct chat responses (no context)
  - `generate_rag_response()`: Context-aware responses using RAG

- **Current State**: Mock implementation returns placeholder responses
- **Future Integration**: Designed to easily swap with real SLM API (Groq, vLLM, etc.)
- **Configuration**: Reads from environment variables:
  - `SLM_ENDPOINT_URL`: API endpoint
  - `SLM_API_KEY`: Authentication key (optional)
  - `SLM_MODEL_NAME`: Model identifier (optional)

### 3. `main.py` (Modified)
**Integrated Routing Logic**

- Converted `sakhi_chat()` to `async def` for async SLM calls
- Added routing decision before classification
- Implemented three routing paths:
  1. **SLM_DIRECT Path**: Skip RAG, call SLM directly
  2. **SLM_RAG Path**: Perform hierarchical RAG → call SLM with context
  3. **OPENAI_RAG Path**: Keep existing flow (classification → RAG → OpenAI)
- All routes preserve conversation history and metadata extraction
- Response payload includes `"route"` field for debugging

## 🧪 Testing

### Quick Test
Run the simple test to verify routing works:
```bash
python quick_test.py
```

Expected output:
```
hello                          -> slm_direct
severe bleeding                -> openai_rag
what is folic acid             -> openai_rag (or slm_rag)
```

### Comprehensive Test
Run the full test suite:
```bash
python test_routing.py
```

This tests 16 different queries across all three categories.

### Manual Testing via API

1. **Start the server**:
```bash
uvicorn main:app --reload
```

2. **Test small talk** (should route to SLM_DIRECT):
```bash
curl -X POST http://localhost:8000/sakhi/chat \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+1234567890", "message": "hello", "language": "en"}'
```

3. **Test simple medical** (should route to SLM_RAG or OPENAI_RAG):
```bash
curl -X POST http://localhost:8000/sakhi/chat \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+1234567890", "message": "what is folic acid", "language": "en"}'
```

4. **Test complex medical** (should route to OPENAI_RAG):
```bash
curl -X POST http://localhost:8000/sakhi/chat \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+1234567890", "message": "severe bleeding emergency", "language": "en"}'
```

## 🔧 Enabling Real SLM Integration

### Step 1: Set Environment Variables
Add to your `.env` file:
```env
SLM_ENDPOINT_URL=https://api.groq.com/openai/v1  # Example for Groq
SLM_API_KEY=your_api_key_here
SLM_MODEL_NAME=llama3-8b-8192  # Example model
```

### Step 2: Update SLM Client
Replace the mock implementation in `modules/slm_client.py` with real API calls.

Example using httpx for Groq (OpenAI-compatible):
```python
import httpx
from openai import AsyncOpenAI

# In __init__:
self.client = AsyncOpenAI(
    api_key=self.api_key,
    base_url=self.endpoint_url
)

# In generate_chat:
async def generate_chat(self, message, language="en", user_name=None):
    response = await self.client.chat.completions.create(
        model=self.model_name,
        messages=[
            {"role": "system", "content": f"You are Sakhi, a friendly companion. Respond in {language}."},
            {"role": "user", "content": message}
        ],
        temperature=0.7,
    )
    return response.choices[0].message.content

# In generate_rag_response:
async def generate_rag_response(self, context, message, language="en", user_name=None):
    system_prompt = f"You are Sakhi, a medical companion. Use the following context to answer. Respond in {language}.\n\nContext:\n{context}"
    response = await self.client.chat.completions.create(
        model=self.model_name,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ],
        temperature=0.7,
    )
    return response.choices[0].message.content
```

### Step 3: Install Dependencies (if needed)
```bash
pip install httpx
# or if using openai library for other providers:
pip install openai
```

## 📊 Monitoring & Debugging

### Console Logs
The system logs routing decisions with similarity scores:
```
INFO:modules.model_gateway:Query: 'hello...'
INFO:modules.model_gateway:Similarity scores - Small Talk: 0.892, Medical Simple: 0.234, Medical Complex: 0.156
INFO:modules.model_gateway:→ Routing to: SLM_DIRECT (small talk detected)
```

### API Response
All responses include a `"route"` field:
```json
{
  "reply": "...",
  "mode": "general",
  "language": "en",
  "route": "slm_direct"
}
```

Possible values: `"slm_direct"`, `"slm_rag"`, `"openai_rag"`

## 🎯 Routing Behavior

| Query Type | Example | Similarity Threshold | Route |
|------------|---------|---------------------|-------|
| Small Talk | "hello", "thanks" | > 0.75 to SMALL_TALK | SLM_DIRECT |
| Medical Simple | "what is folic acid" | > 0.65 to MEDICAL_SIMPLE & less than COMPLEX | SLM_RAG |
| Medical Complex | "severe bleeding" | Highest to MEDICAL_COMPLEX | OPENAI_RAG |
| Low Confidence | Ambiguous query | All similarities low | OPENAI_RAG (safe default) |

## 🔄 Workflow Changes

### Before (Simple Architecture):
```
User Input → Classify → RAG → OpenAI Generate → Response
```

### After (Hybrid Architecture):
```
User Input → Semantic Router → Branch:
  ├─ [Small Talk] → SLM Generate → Response
  ├─ [Simple Medical] → RAG → SLM Generate → Response
  └─ [Complex Medical] → Classify → RAG → OpenAI Generate → Response
```

## ⚙️ Tuning Recommendations

### Adjust Thresholds
If routing is too conservative (sending too many to OpenAI):
- Lower `SMALL_TALK_THRESHOLD` (currently 0.75)
- Lower `MEDICAL_SIMPLE_THRESHOLD` (currently 0.65)

In `modules/model_gateway.py`:
```python
SMALL_TALK_THRESHOLD = 0.70  # More queries go to SLM_DIRECT
MEDICAL_SIMPLE_THRESHOLD = 0.60  # More queries go to SLM_RAG
```

### Add More Anchor Examples
Add domain-specific examples to the anchor lists in `model_gateway.py`:
- `SMALL_TALK_EXAMPLES`
- `MEDICAL_SIMPLE_EXAMPLES`
- `MEDICAL_COMPLEX_EXAMPLES`

More examples = better routing accuracy.

## 🚀 Next Steps

1. **Test Routing**: Run `python quick_test.py` to verify basic routing
2. **Start Server**: Run `uvicorn main:app --reload`
3. **Monitor Logs**: Watch console for routing decisions
4. **Configure SLM**: When ready, set up real SLM endpoint
5. **Fine-tune**: Adjust thresholds based on real-world performance

## 📝 Notes

- **Backward Compatible**: Existing OpenAI flow is preserved for complex queries
- **Mock Mode**: SLM client runs in mock mode until endpoint configured
- **Conversation History**: All routes maintain conversation context
- **Metadata Preserved**: YouTube links and infographics work on all RAG routes
- **Language Detection**: Still uses classification for language detection across all routes

## 🐛 Troubleshooting

**Issue**: All queries route to OPENAI_RAG
- **Solution**: Check anchor vector generation didn't fail. Look for "Initializing ModelGateway" log.

**Issue**: Import errors
- **Solution**: Ensure `numpy` is installed: `pip install numpy`

**Issue**: SLM client errors
- **Solution**: Check if running in mock mode (expected). Set `SLM_ENDPOINT_URL` to enable real SLM.

**Issue**: Async errors
- **Solution**: Ensure FastAPI and all async dependencies are up to date.
