# Frontend Handover: Journey Awareness Layer

## 1. User Profile Updates
The user profile object (returned from login and `/api/user/me`) now includes the following fields:

- `sakhi_journey_stage`: String enum (`TTC`, `PREGNANT`, `PARENT`)
- `sakhi_journey_date`: Date string (YYYY-MM-DD)
- `sakhi_journey_date_type`: String enum (`LMP`, `DUE_DATE`, `DOB`)

## 2. New API Endpoints

### Update User Journey
**Endpoint**: `POST /api/user/journey`

**Payload**:
```json
{
  "user_id": "string (UUID)",
  "stage": "TTC" | "PREGNANT" | "PARENT",
  "date": "2025-10-25" | null,     // ISO Date String
  "date_type": "LMP" | "DUE_DATE" | "DOB" | null
}
```

**Response**:
```json
{
  "status": "success",
  "updates": {
    "sakhi_journey_stage": "PREGNANT",
    ...
  }
}
```

## 3. Implementation Requirements

### 3.1 Onboarding / Modal
- When the user selects their stage in the UI, call `POST /api/user/journey`.
- On app launch, check `user.sakhi_journey_stage`. If strictly `null` or empty, show the "Choose Your Journey" modal. If set, pre-fill or hide the modal.

### 3.2 Analytics (Event Tracking)
Fire the `journey_selected` event when the user successfully updates their journey.

**Event Properties**:
- `stage`: `TTC` | `PREGNANT` | `PARENT`
- `week` (if PREGNANT): Calculated week number (1-40) based on `date` (LMP/Due Date).
- `child_age_months` (if PARENT): Calculated age in months based on `date` (DOB).

### 3.3 Content Filtering
- Use `user.sakhi_journey_stage` to filter content in the "For You" or "Learn" sections.
- Content items will (eventually) be tagged with these stages.
