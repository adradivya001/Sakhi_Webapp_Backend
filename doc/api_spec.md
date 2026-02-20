# Sakhi Webapp Backend API Reference

**Base URL**: `https://sakhi.replit.app` (Deployment) / `http://localhost:8000` (Local)

## 1. User Authentication & Profile

### **Register User**
*   **Endpoint:** `POST /user/register`
*   **Request Body:**
    ```json
    {
      "name": "Full Name",
      "email": "user@example.com",
      "password": "securepassword",
      "phone_number": "+91...",
      "role": "USER",
      "preferred_language": "en",
      "user_relation": "Mother"
    }
    ```
*   **Response:**
    ```json
    {
      "status": "success",
      "user_id": "uuid",
      "user": { ...profile... }
    }
    ```

### **Login User**
*   **Endpoint:** `POST /user/login`
*   **Request Body:**
    ```json
    { "email": "...", "password": "..." }
    ```
*   **Response:**
    ```json
    { "status": "success", "user_id": "...", "user": { ... } }
    ```

---

## 2. Sakhi AI Chat

### **Send Chat Message**
*   **Endpoint:** `POST /sakhi/chat`
*   **Description:** Central gateway for Sakhi AI. Handles onboarding for new users and medical/general chat.
*   **Request Body:**
    ```json
    {
      "user_id": "uuid",
      "phone_number": "+91...",
      "message": "Hello Sakhi",
      "language": "en"
    }
    ```
*   **Response (Medical Flow):**
    ```json
    {
      "intent": "Checking symptoms",
      "reply": "I understand you are feeling...",
      "mode": "medical",
      "language": "en",
      "youtube_link": "URL",
      "infographic_url": "URL",
      "route": "slm_rag"
    }
    ```
*   **Response (Onboarding Flow):**
    ```json
    {
      "reply": "Welcome to Sakhi! What should I call you?",
      "mode": "onboarding"
    }
    ```

---

## 3. Onboarding & Journey

### **Get Next Onboarding Step**
*   **Endpoint:** `POST /onboarding/step`
*   **Request Body:**
    ```json
    {
      "parent_profile_id": "id",
      "relationship_type": "Mother",
      "current_step": 1,
      "answers_json": {}
    }
    ```

### **Complete Onboarding**
*   **Endpoint:** `POST /onboarding/complete`
*   **Request Body:**
    ```json
    {
      "user_id": "uuid",
      "relationship_type": "Mother",
      "answers_json": { "q1": "ans" }
    }
    ```

### **Update User Journey**
*   **Endpoint:** `POST /api/user/journey`
*   **Request Body:**
    ```json
    {
      "user_id": "uuid",
      "stage": "TTC | PREGNANT | PARENT",
      "date": "2024-01-01",
      "date_type": "LMP"
    }
    ```

---

## 4. Knowledge Hub

### **Get Articles**
*   **Endpoint:** `GET /api/knowledge-hub/`
*   **Query Params:** `lang`, `life_stage_id`, `is_featured`, `perPage`, `search`
*   **Response:** Array of `KnowledgeHubResponse` objects.

### **Get Recommendations**
*   **Endpoint:** `GET /api/knowledge-hub/recommendations`
*   **Query Params:** `userId`, `lang`, `limit`
