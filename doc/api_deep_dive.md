# Sakhi Webapp Backend API Deep-Dive

This document provides a technical reference for the Sakhi Webapp Backend (Python/FastAPI) to facilitate the construction of a robust binding layer (SDK).

## 1. Request Schemas
- **User Registration**: `RegisterRequest` (name: str, email: str, password: str, phone_number: Optional[str], role: Optional[str] = "USER").
- **Chat**: `ChatRequest` (user_id: Optional[str], phone_number: Optional[str], message: str, language: str = "en").
- **Tools**: Pydantic models for specific tool inputs (e.g., `VaccinationRequest` with `dob` date).

## 2. Response Schemas
- **Standard**: `{ status: "success", data: Object }` or `{ reply: string, mode: string, intent: string }`.
- **Error**: `{ detail: string }` (FastAPI default).

## 3. Sample Responses
```json
{
  "reply": "Welcome to Sakhi!",
  "mode": "onboarding",
  "intent": "user_initialization"
}
```

## 4. HTTP Status Codes
- `200 OK`: Success.
- `400 Bad Request`: Validation failure (e.g., missing fields).
- `401 Unauthorized`: Login failure.
- `500 Internal Server Error`: Logic/Supabase failure.

## 5. Pagination
- Handled internally via Supabase queries but not explicitly exposed as standardized query params in the main routes studied. Tools usually return lists.

## 6. Headers
- `Content-Type: application/json`
- `Authorization: Bearer <token>` (where applicable, though many routes rely on `user_id` passed in body).
- `Access-Control-Allow-Origin: *` (CORS).

## 7. Rate Limiting
- Not explicitly implemented in the application middleware; handled at the infrastructure/ngrok level if at all.

## 8. Streaming vs Normal
- **Normal**: All endpoints studied return synchronous JSON responses. No streaming (`EventSource` or `chunked`) detected in `main.py`.

## 9. Timeouts/Retry Logic
- `SUPPORT_API_TIMEOUT_MS` used in bridges.
- Internal `asyncio.gather` used for parallel LLM tasks with default timeouts.

## 10. Transaction Atomicity
- No explicit database transaction blocks (`begin/commit`) found in the Supabase client wrapper; relies on single-row atomic operations provided by Supabase REST API.

## 11. Role Mapping
- **Roles**: `USER`, `DOCTOR`, `ADMIN`.
- Primarily used in user registration and onboarding flow branch logic.

## 12. Naming Conventions
- **API Inputs**: `snake_case` (e.g., `phone_number`, `user_id`).
- **Database**: `snake_case`.

## 13. API Versioning
- No URL-based versioning (e.g., `/v1/`) found in the current routing table.

## 14. Logging Formats
- Custom `print` statements and `console.error` for errors.
- No trace/correlation ID implementation detected.

## 15. File Uploads
- Primarily URLs based. Interactive tools might reference static images (e.g., `Sakhi_intro.png`). Direct binary multipart/form-data not heavily used in core routes.
