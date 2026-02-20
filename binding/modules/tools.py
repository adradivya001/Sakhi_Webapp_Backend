from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict
from dateutil.relativedelta import relativedelta
import math

router = APIRouter(prefix="/api/tools", tags=["tools"])

# ================= DATA CONSTANTS =================
VACCINES = [
    { "age": "Birth", "offset": { "days": 0 }, "items": ['BCG', 'Hep B-1', 'Oral Polio Vaccine'] },
    { "age": "6 Weeks", "offset": { "weeks": 6 }, "items": ['Hep B-2', 'IPV-1', 'DTwP/DTaP 1', 'Hib-1', 'PCV-1', 'RV-1'] },
    { "age": "10 Weeks", "offset": { "weeks": 10 }, "items": ['Hep B-3', 'IPV-2', 'DTwP/DTaP 2', 'Hib-2', 'PCV-2', 'RV-2'] },
    { "age": "14 Weeks", "offset": { "weeks": 14 }, "items": ['Hep B-4', 'IPV-3', 'DTwP/DTaP 3', 'Hib-3', 'PCV-3', 'RV-3'] },
    { "age": "6 Months", "offset": { "months": 6 }, "items": ['Influenza IIV-1'] },
    { "age": "6-9 Months", "offset": { "months": 6 }, "items": ['TCV'] },
    { "age": "7 Months", "offset": { "months": 7 }, "items": ['Influenza IIV-2'] },
    { "age": "9 Months", "offset": { "months": 9 }, "items": ['Meningococcal-1', 'MMR-1'] },
    { "age": "12 Months", "offset": { "months": 12 }, "items": ['Hepatitis A', 'Meningococcal-2', 'JE-1'] },
    { "age": "13 Months", "offset": { "months": 13 }, "items": ['JE-2'] },
    { "age": "12-18 Months", "offset": { "months": 12 }, "items": ['PCV Booster'] },
    { "age": "15 Months", "offset": { "months": 15 }, "items": ['MMR-2', 'Varicella-1'] },
    { "age": "16-18 Months", "offset": { "months": 16 }, "items": ['IPV 1st Booster', 'DTwP/DTaP-B1', 'Hib B1'] },
    { "age": "18-24 Months", "offset": { "months": 18 }, "items": ['Hepatitis A-2', 'Varicella-2'] },
    { "age": "4-6 Years", "offset": { "years": 4 }, "items": ['IPV 2nd Booster', 'DTwP/DTaP-B2', 'MMR-3'] },
    { "age": "9-14 Years", "offset": { "years": 9 }, "items": ['Tdap/Td', 'HPV-1', 'HPV-2'] },
    { "age": "15-18 Years", "offset": { "years": 15 }, "items": ['HPV-1', 'HPV-2', 'HPV-3'] },
    { "age": "16 Years", "offset": { "years": 16 }, "items": ['Tdap/Td'] },
]

PREGNANCY_WEEKS = [
    { "week": 4, "fruit": "Poppy Seed", "size": "1-2 mm", "weight": "< 1g", "description": "Your baby is the size of a poppy seed. The blastocyst is implanting in your uterus.", "image": "/assets/fruits/poppyseed.png" },
    { "week": 5, "fruit": "Sesame Seed", "size": "3-5 mm", "weight": "< 1g", "description": "Your baby is the size of a sesame seed. The neural tube is forming.", "image": "/assets/fruits/sesameseed.png" },
    { "week": 6, "fruit": "Lentil", "size": "5-7 mm", "weight": "< 1g", "description": "Your baby is the size of a sweet pea or lentil. The heart starts beating.", "image": "/assets/fruits/lentil.png" },
    { "week": 7, "fruit": "Blueberry", "size": "10-13 mm", "weight": "< 1g", "description": "Your baby is doubling in size and is now the size of a blueberry.", "image": "/assets/fruits/blueberry.png" },
    { "week": 8, "fruit": "Raspberry", "size": "1.6 cm", "weight": "1g", "description": "Your baby is the size of a raspberry. Fingers and toes are forming.", "image": "/assets/fruits/raspberry.png" },
    { "week": 9, "fruit": "Grape", "size": "2.3 cm", "weight": "2g", "description": "Your baby is the size of a grape. Eyes are fully formed but eyelids are fused shut.", "image": "/assets/fruits/grape.png" },
    { "week": 10, "fruit": "Kumquat", "size": "3.1 cm", "weight": "4g", "description": "Your baby is the size of a kumquat. Vital organs are starting to function.", "image": "/assets/fruits/kumquat.png" },
    { "week": 11, "fruit": "Fig", "size": "4.1 cm", "weight": "7g", "description": "Your baby is the size of a fig. Usually, the head makes up half the body length.", "image": "/assets/fruits/fig.png" },
    { "week": 12, "fruit": "Lime", "size": "5.4 cm", "weight": "14g", "description": "Your baby is the size of a lime. You're nearing the end of the first trimester!", "image": "/assets/fruits/lime.png" },
    { "week": 13, "fruit": "Lemon", "size": "7.4 cm", "weight": "23g", "description": "Your baby is the size of a lemon. Vocal cords are developing.", "image": "/assets/fruits/lemon.png" },
    { "week": 14, "fruit": "Nectarine", "size": "8.7 cm", "weight": "43g", "description": "Your baby is the size of a nectarine. Welcome to the second trimester!", "image": "/assets/fruits/nectarine.png" },
    { "week": 15, "fruit": "Apple", "size": "10.1 cm", "weight": "70g", "description": "Your baby is the size of an apple. They can sense light now.", "image": "/assets/fruits/apple.png" },
    { "week": 16, "fruit": "Avocado", "size": "11.6 cm", "weight": "100g", "description": "Your baby is the size of an avocado. You might start feeling movement soon.", "image": "/assets/fruits/avocado.png" },
    { "week": 17, "fruit": "Pear", "size": "13 cm", "weight": "140g", "description": "Your baby is the size of a pear. Skeleton is hardening.", "image": "/assets/fruits/pear.png" },
    { "week": 18, "fruit": "Bell Pepper", "size": "14.2 cm", "weight": "190g", "description": "Your baby is the size of a bell pepper. Nerves are developing myelin.", "image": "/assets/fruits/pepper.png" },
    { "week": 19, "fruit": "Heirloom Tomato", "size": "15.3 cm", "weight": "240g", "description": "Your baby is the size of a tomato. Senses (smell, taste, canvas) are developing.", "image": "/assets/fruits/tomato.png" },
    { "week": 20, "fruit": "Banana", "size": "16.4 cm", "weight": "300g", "description": "Your baby is the size of a banana. You're halfway there!", "image": "/assets/fruits/banana.png" },
    { "week": 21, "fruit": "Carrot", "size": "26.7 cm", "weight": "360g", "description": "Your baby is the size of a large carrot. Eyebrows and eyelids are present.", "image": "/assets/fruits/carrot.png" },
    { "week": 22, "fruit": "Spaghetti Squash", "size": "27.8 cm", "weight": "430g", "description": "Your baby is the size of a squash. Taste buds are active.", "image": "/assets/fruits/squash.png" },
    { "week": 23, "fruit": "Large Mango", "size": "28.9 cm", "weight": "500g", "description": "Your baby is the size of a mango. Hearing is well established.", "image": "/assets/fruits/mango.png" },
    { "week": 24, "fruit": "Ear of Corn", "size": "30 cm", "weight": "600g", "description": "Your baby is the size of corn. Lungs are developing branches.", "image": "/assets/fruits/corn.png" },
    { "week": 25, "fruit": "Rutabaga", "size": "34.6 cm", "weight": "660g", "description": "Your baby is the size of a rutabaga. Hair is growing.", "image": "/assets/fruits/rutabaga.png" },
    { "week": 26, "fruit": "Scallion", "size": "35.6 cm", "weight": "760g", "description": "Your baby is the size of a scallion. Eyelids can open now.", "image": "/assets/fruits/scallion.png" },
    { "week": 27, "fruit": "Cauliflower", "size": "36.6 cm", "weight": "875g", "description": "Your baby is the size of cauliflower. Welcome to the third trimester!", "image": "/assets/fruits/cauliflower.png" },
    { "week": 28, "fruit": "Eggplant", "size": "37.6 cm", "weight": "1 kg", "description": "Your baby is the size of an eggplant. Can dream while sleeping.", "image": "/assets/fruits/eggplant.png" },
    { "week": 29, "fruit": "Butternut Squash", "size": "38.6 cm", "weight": "1.15 kg", "description": "Your baby is the size of a butternut squash. Bones are fully developed.", "image": "/assets/fruits/butternut.png" },
    { "week": 30, "fruit": "Cabbage", "size": "39.9 cm", "weight": "1.3 kg", "description": "Your baby is the size of a cabbage. Memory is starting to work.", "image": "/assets/fruits/cabbage.png" },
    { "week": 31, "fruit": "Coconut", "size": "41.1 cm", "weight": "1.5 kg", "description": "Your baby is the size of a coconut. Reproductive organs are fully formed.", "image": "/assets/fruits/coconut.png" },
    { "week": 32, "fruit": "Jicama", "size": "42.4 cm", "weight": "1.7 kg", "description": "Your baby is the size of a jicama. Practicing breathing motions.", "image": "/assets/fruits/jicama.png" },
    { "week": 33, "fruit": "Pineapple", "size": "43.7 cm", "weight": "1.9 kg", "description": "Your baby is the size of a pineapple. Immune system is developing.", "image": "/assets/fruits/pineapple.png" },
    { "week": 34, "fruit": "Cantaloupe", "size": "45 cm", "weight": "2.1 kg", "description": "Your baby is the size of a cantaloupe. Vernix is getting thicker.", "image": "/assets/fruits/cantaloupe.png" },
    { "week": 35, "fruit": "Honeydew Melon", "size": "46.2 cm", "weight": "2.4 kg", "description": "Your baby is the size of a honeydew. Kidneys are fully developed.", "image": "/assets/fruits/honeydew.png" },
    { "week": 36, "fruit": "Romaine Lettuce", "size": "47.4 cm", "weight": "2.6 kg", "description": "Your baby is the size of a head of lettuce. Shedding lanugo.", "image": "/assets/fruits/lettuce.png" },
    { "week": 37, "fruit": "Swiss Chard", "size": "48.6 cm", "weight": "2.9 kg", "description": "Your baby is the size of chard. Considered early term.", "image": "/assets/fruits/chard.png" },
    { "week": 38, "fruit": "Leek", "size": "49.8 cm", "weight": "3.1 kg", "description": "Your baby is the size of a leek. Systems are ready for the world.", "image": "/assets/fruits/leek.png" },
    { "week": 39, "fruit": "Watermelon", "size": "50.7 cm", "weight": "3.3 kg", "description": "Your baby is the size of a small watermelon. Waiting for hello day!", "image": "/assets/fruits/watermelon.png" },
    { "week": 40, "fruit": "Pumpkin", "size": "51.2 cm", "weight": "3.5 kg", "description": "Your baby is the size of a pumpkin. Happy Due Date!", "image": "/assets/fruits/pumpkin.png" }
]

TTC_READINESS_ITEMS = [
    {
        "category": "Medical",
        "items": [
            { "id": "med_1", "text": "Schedule a preconception checkup" },
            { "id": "med_2", "text": "Start taking folic acid (400mcg daily)" },
            { "id": "med_3", "text": "Check immunization history (Rubella, Varicella)" },
            { "id": "med_4", "text": "Review current medications with your doctor" },
            { "id": "med_5", "text": "Get a dental checkup" }
        ]
    },
    {
        "category": "Lifestyle",
        "items": [
            { "id": "life_1", "text": "Stop smoking and limit alcohol" },
            { "id": "life_2", "text": "Reduce caffeine intake (<200mg/day)" },
            { "id": "life_3", "text": "Maintain a healthy BMI range" },
            { "id": "life_4", "text": "Establish a regular sleep schedule" },
            { "id": "life_5", "text": "Identify and reduce sources of stress" }
        ]
    },
    {
        "category": "Financial (India Context)",
        "items": [
            { "id": "fin_1", "text": "Review maternity insurance coverage (waiting periods?)" },
            { "id": "fin_2", "text": "Create a baby budget (delivery costs, vaccinations)" },
            { "id": "fin_3", "text": "Check employer's maternity leave policy" },
            { "id": "fin_4", "text": "Start an emergency fund" }
        ]
    },
    {
        "category": "Conversation",
        "items": [
            { "id": "conv_1", "text": "Discuss parenting styles with partner" },
            { "id": "conv_2", "text": "Talk about family involvement/support" },
            { "id": "conv_3", "text": "Agree on career/work-life balance expectations" }
        ]
    }
]

SAFETY_ITEMS = [
    { "id": "safe_1", "name": "Papaya (Ripe)", "category": "Food", "status": "SAFE", "note": "Ripe papaya is safe and healthy." },
    { "id": "safe_2", "name": "Papaya (Unripe/Semi-ripe)", "category": "Food", "status": "AVOID", "note": "Contains latex which may trigger contractions." },
    { "id": "safe_3", "name": "Paracetamol", "category": "App", "status": "SAFE", "note": "Generally considered safe for pain/fever. Consult dosage." },
    { "id": "safe_4", "name": "Ibuprofen", "category": "Meds", "status": "AVOID", "note": "Avoid, especially in third trimester. Use Paracetamol instead." },
    { "id": "safe_5", "name": "Sushi (Raw Fish)", "category": "Food", "status": "AVOID", "note": "Risk of parasites/bacteria. Cooked fish is fine." },
    { "id": "safe_6", "name": "Coffee", "category": "Drink", "status": "CAUTION", "note": "Limit to 200mg caffeine per day (approx 1-2 cups)." },
    { "id": "safe_7", "name": "Yoga", "category": "Activity", "status": "SAFE", "note": "Prenatal yoga is excellent. Avoid hot yoga or lying on back after 1st trimester." },
    { "id": "safe_8", "name": "Hair Dye", "category": "Beauty", "status": "CAUTION", "note": "Wait until second trimester to be safe. Use well-ventilated area." },
    { "id": "safe_9", "name": "Flying", "category": "Activity", "status": "SAFE", "note": "Generally safe until 36 weeks. Check airline policy." },
    { "id": "safe_10", "name": "Retinol/Vitamin A", "category": "Beauty", "status": "AVOID", "note": "High doses can cause birth defects. Switch to Bakuchiol." }
]

# ================= MODELS =================

class VaccinationRequest(BaseModel):
    dob: date

class VaccinationStage(BaseModel):
    age: str
    items: List[str]
    dueDate: date
    isPast: bool

class DueDateRequest(BaseModel):
    lmp: date

class DueDateResponse(BaseModel):
    dueDate: date
    weeksPregnant: int
    trimester: int

class OvulationRequest(BaseModel):
    lastPeriod: date
    cycleLength: int = 28

class OvulationResponse(BaseModel):
    ovulationDate: date
    fertileWindowStart: date
    fertileWindowEnd: date
    nextPeriod: date

class PregnancyWeekRequest(BaseModel):
    referenceDate: str # Can be passed as full ISO string or YYYY-MM-DD
    type: str = "LMP" # or DUE_DATE

# ================= ENDPOINTS =================

@router.post("/vaccination-schedule", response_model=List[VaccinationStage])
def get_vaccination_schedule(req: VaccinationRequest):
    dob = req.dob
    today = date.today()
    schedule = []
    
    for stage in VACCINES:
        due_date = dob
        offset = stage["offset"]
        
        if "days" in offset:
            due_date = dob + timedelta(days=offset["days"])
        if "weeks" in offset:
            due_date = dob + timedelta(weeks=offset["weeks"])
        if "months" in offset:
            due_date = dob + relativedelta(months=offset["months"])
        if "years" in offset:
            due_date = dob + relativedelta(years=offset["years"])
            
        schedule.append({
            "age": stage["age"],
            "items": stage["items"],
            "dueDate": due_date,
            "isPast": due_date < today
        })
        
    return schedule

@router.post("/due-date", response_model=DueDateResponse)
def calculate_due_date(req: DueDateRequest):
    lmp = req.lmp
    today = date.today()
    
    # Due Date = LMP + 280 days
    due_date = lmp + timedelta(days=280)
    
    # Weeks Pregnant = (Today - LMP) / 7
    weeks_pregnant_delta = (today - lmp).days
    weeks_pregnant = max(0, weeks_pregnant_delta // 7)
    
    # Trimester logic
    trimester = 1
    if weeks_pregnant >= 13 and weeks_pregnant < 27:
        trimester = 2
    if weeks_pregnant >= 27:
        trimester = 3
        
    return {
        "dueDate": due_date,
        "weeksPregnant": weeks_pregnant,
        "trimester": trimester
    }

@router.post("/ovulation", response_model=OvulationResponse)
def calculate_ovulation(req: OvulationRequest):
    last_period = req.lastPeriod
    cycle_length = req.cycleLength
    
    # Next Period = LMP + Cycle Length
    next_period = last_period + timedelta(days=cycle_length)
    
    # Ovulation = Next Period - 14 days
    ovulation_date = next_period - timedelta(days=14)
    
    # Fertile Window = 5 days before ovulation + ovulation day
    fertile_window_start = ovulation_date - timedelta(days=5)
    fertile_window_end = ovulation_date
    
    return {
        "ovulationDate": ovulation_date,
        "fertileWindowStart": fertile_window_start,
        "fertileWindowEnd": fertile_window_end,
        "nextPeriod": next_period
    }

@router.post("/pregnancy-week")
def get_pregnancy_week_calculation(req: PregnancyWeekRequest):
    try:
        # Handle full ISO strings if passed, by taking first 10 chars
        ref_date_str = req.referenceDate[:10]
        ref_date = datetime.strptime(ref_date_str, "%Y-%m-%d").date()
    except ValueError as e:
         raise HTTPException(status_code=400, detail=f"Invalid date format: {req.referenceDate}. Use YYYY-MM-DD.")

    today = date.today()
    week = 4
    
    if req.type == 'DUE_DATE':
        if ref_date > today:
             # It IS a due date in future
             # Weeks Left = (Due - Today) / 7
             # Total 40 - Weeks Left
             days_diff = (ref_date - today).days
             weeks_left = days_diff // 7
             week = 40 - weeks_left
        else:
            # Past due date?? assume 40
            week = 40
    else:
        # LMP
        days_diff = (today - ref_date).days
        week = days_diff // 7
        
    # Clamp
    week = max(4, min(40, week))
    
    # Find data
    week_data = next((w for w in PREGNANCY_WEEKS if w["week"] == week), None)
    
    return {
        "currentWeek": week,
        "weekData": week_data
    }

@router.get("/pregnancy-week/{week_num}")
def get_pregnancy_week_detail(week_num: int):
    week_data = next((w for w in PREGNANCY_WEEKS if w["week"] == week_num), None)
    if not week_data:
        raise HTTPException(status_code=404, detail="Week not found")
    return week_data

@router.get("/pregnancy-weeks")
def get_all_pregnancy_weeks():
    # Only return summary or full? Full is fine, it's small.
    return PREGNANCY_WEEKS

@router.get("/safety-check")
def safety_check(q: Optional[str] = None):
    if not q:
        return SAFETY_ITEMS
    
    q_lower = q.lower()
    results = [
        item for item in SAFETY_ITEMS
        if q_lower in item["name"].lower() or q_lower in item["category"].lower()
    ]
    return results

@router.get("/readiness-checklist")
def get_readiness_checklist():
    return TTC_READINESS_ITEMS

# ================= CONCEPTION CALCULATOR =================

class ConceptionRequest(BaseModel):
    date: date
    type: str  # "LMP" or "DUE_DATE"
    cycleLength: Optional[int] = 28
    isIrregular: Optional[bool] = False
    dueDateConfidence: Optional[str] = None # "DOCTOR" or "ESTIMATED"

class ConceptionResponse(BaseModel):
    conceptionWindowStart: date
    conceptionWindowEnd: date
    probableConceptionDate: date
    confidenceLevel: str # "High", "Medium", "Low"
    explanation: str

@router.post("/conception-calculator", response_model=ConceptionResponse)
def calculate_conception(req: ConceptionRequest):
    # Standard period: 280 days total pregnancy, 266 days from conception
    # Ovulation ~ 14 days before next period
    
    conception_date = None
    confidence = "High"
    
    if req.type == "DUE_DATE":
        # Path A: Based on Due Date
        # Conception is approx 38 weeks (266 days) before due date
        conception_date = req.date - timedelta(days=266)
        
        if req.dueDateConfidence == "ESTIMATED":
            confidence = "Medium"
    else:
        # Path B: Based on LMP
        # Ovulation day = Cycle Length - 14
        if req.cycleLength is None:
             days_to_ovulate = 14 # Default 28 - 14
        else:
             days_to_ovulate = req.cycleLength - 14
             
        conception_date = req.date + timedelta(days=days_to_ovulate)
        
        if req.isIrregular:
            confidence = "Low"
        elif req.cycleLength and (req.cycleLength < 26 or req.cycleLength > 30):
            confidence = "Medium"
            
    # Window: +/- 4 days to give a wide enough range (probabilistic)
    # Prompt asks for +/- 3-5 days. Let's do +/- 3 days for High confidence, 
    # +/- 5 days for Low confidence? 
    # Let's standardize to a safe +/- 3 days around the probable date (7 day window)
    # Or +/- 4 days (9 day window).
    
    window_days = 3
    if confidence == "Low":
        window_days = 5
    elif confidence == "Medium":
        window_days = 4
        
    start_date = conception_date - timedelta(days=window_days)
    end_date = conception_date + timedelta(days=window_days)
    
    # Explanation
    if req.type == "DUE_DATE":
        expl = "We calculated this by counting back 38 weeks from your due date, which is the average time from conception to birth."
    else:
        expl = f"Based on a {req.cycleLength or 28}-day cycle, conception likely occurred around the time of ovulation, which is typically 14 days before your next period."

    return {
        "conceptionWindowStart": start_date,
        "conceptionWindowEnd": end_date,
        "probableConceptionDate": conception_date,
        "confidenceLevel": confidence,
        "explanation": expl
    }

# ================= AM I PREGNANT TOOL =================

class AmIPregnantRequest(BaseModel):
    q1_period: str # "LATE_5_PLUS", "LATE_1_4", "NO", "NOT_SURE"
    q2_sex: str    # "YES", "NOT_SURE", "NO"
    q3_spotting: str # "YES_LIGHT", "YES_HEAVY", "NO"
    q4_symptoms: str # "NONE", "ONE_TWO", "SEVERAL"
    q5_test: str     # "POSITIVE", "NEGATIVE", "UNCLEAR", "NO"

class AmIPregnantResponse(BaseModel):
    result: str # "VERY_LIKELY", "POSSIBLY", "UNLIKELY", "INCONCLUSIVE"
    copy: str
    nextGuidance: List[str]

@router.post("/am-i-pregnant", response_model=AmIPregnantResponse)
def check_pregnancy_probability(req: AmIPregnantRequest):
    # Rule based Scoring
    score = 0
    
    # Q5 Override Logic (Immediate High Probability)
    if req.q5_test == "POSITIVE":
        return {
            "result": "VERY_LIKELY",
            "copy": "Based on your positive test result, there is a high chance that you may be pregnant.",
            "nextGuidance": ["Consult a doctor to confirm with a blood test/ultrasound", "Start taking prenatal vitamins if you haven't already"]
        }
        
    # Scoring
    
    # Q1: Period
    if req.q1_period == "LATE_5_PLUS":
        score += 3
    elif req.q1_period == "LATE_1_4":
        score += 2
    elif req.q1_period == "NO":
        score += 0
    # NOT_SURE: 0
    
    # Q2: Timing
    if req.q2_sex == "YES":
        score += 3
    elif req.q2_sex == "NOT_SURE":
        score += 1
    # NO: 0
    
    # Q3: Spotting
    if req.q3_spotting == "YES_LIGHT":
        score += 1
    elif req.q3_spotting == "YES_HEAVY":
        # Heavy bleeding usually suggests period
        score -= 2 
    # NO: 0
    
    # Q4: Symptoms
    if req.q4_symptoms == "SEVERAL":
        score += 2
    elif req.q4_symptoms == "ONE_TWO":
        score += 1
    # NONE: 0
        
    # Q5: Test (Negative)
    if req.q5_test == "NEGATIVE":
        score -= 2
    elif req.q5_test == "UNCLEAR":
        score += 0 # Neutral, triggers retest suggestion
        
    # --- RESULT DETERMINATION ---
    
    # Logic for Inconclusive
    if req.q1_period == "NOT_SURE" and req.q2_sex == "NOT_SURE":
        return {
            "result": "INCONCLUSIVE", 
            "copy": "We don’t have enough information yet to be sure.",
            "nextGuidance": ["Monitor your cycle for the next few days", "Take a pregnancy test if your period remains absent"]
        }
    
    # Logic for Very Likely
    # - Missed period (>5 days) + Timing (Yes) + Symptoms (Several) = 3 + 3 + 2 = 8
    # - Minimum threshold for Very Likely? Maybe > 6
    if score >= 6:
        return {
            "result": "VERY_LIKELY",
            "copy": "Based on your answers, there is a high chance that you may be pregnant.",
            "nextGuidance": ["Take a home pregnancy test for confirmation", "Consult a doctor"]
        }
        
    # Logic for Possibly
    # - Late 1-4 days (+2) + Symptoms (+1) = 3
    # - Score 3 to 5
    if score >= 3:
        return {
            "result": "POSSIBLY",
            "copy": "There is a possibility of pregnancy, but it may be too early to confirm.",
            "nextGuidance": ["Wait 3–5 days and observe symptoms", "Take a pregnancy test if your period doesn't start"]
        }
        
    # Logic for Unlikely
    return {
        "result": "UNLIKELY",
        "copy": "Pregnancy seems unlikely right now, but bodies can vary.",
        "nextGuidance": ["Track your next period", "Learn about early signs of pregnancy"]
    }

# ================= BABY COST CALCULATOR TOOL =================

class BabyCostRequest(BaseModel):
    city_tier: str # "METRO", "TIER2", "TIER3"
    
    # A. Pregnancy & Delivery
    hospital_type: str # "GOVT", "PVT_STD", "PVT_PREM"
    delivery_type: str # "NORMAL", "C_SECTION"
    custom_delivery_cost: Optional[float] = None

    # B. Feeding
    feeding_type: str # "BREAST", "MIXED", "FORMULA"
    formula_tier: Optional[str] = "STD" # "BUDGET", "STD", "PREM"
    custom_feeding_cost: Optional[float] = None
    
    # C. Hygiene
    diapers_per_day: int
    diaper_brand: str # "BUDGET", "BRANDED"
    wipes_enabled: bool
    custom_hygiene_cost: Optional[float] = None

    # D. Clothing
    clothing_tier: str # "BUDGET", "STANDARD", "PREMIUM"
    custom_clothing_cost: Optional[float] = None

    # E. Healthcare
    health_type: str # "GOVT", "PVT_PED", "PVT_PLUS"
    custom_health_cost: Optional[float] = None
    
    # F. Childcare
    childcare_type: str # "NONE", "PART_TIME", "FULL_TIME"
    custom_childcare_cost: Optional[float] = None

    # G. Gear (Items + Type)
    # { "cradle": "budget", "stroller": "premium" } - keys must match our map
    gear_selection: Dict[str, str] 
    custom_gear_cost: Optional[float] = None

    # H. Toys
    custom_toy_cost: Optional[float] = 1000.0

class BabyCostResult(BaseModel):
    # Final Costs (Used for Totals)
    delivery: int
    feeding: int
    hygiene: int
    clothing: int
    healthYearly: int
    childcare: int
    gear: int
    toys: int
    
    # Standard Costs (For UI Defaults)
    standard_delivery: int
    standard_feeding: int
    standard_hygiene: int
    standard_clothing: int
    standard_healthYearly: int
    standard_childcare: int
    standard_gear: int
    standard_toys: int

    # Totals
    monthlyTotal: int
    firstYearTotal: int
    oneTime: int

@router.post("/baby-cost-calculator", response_model=BabyCostResult)
def calculate_baby_cost(req: BabyCostRequest):
    # Data Setup
    CITIES = {
        "METRO": 1.2,
        "TIER2": 1.0,
        "TIER3": 0.8
    }
    
    DELIVERY_COSTS = {
        "GOVT": { "NORMAL": 5000, "C_SECTION": 15000 },
        "PVT_STD": { "NORMAL": 50000, "C_SECTION": 90000 },
        "PVT_PREM": { "NORMAL": 100000, "C_SECTION": 250000 },
    }
    
    FEEDING_COSTS = {
        "BREAST": 800,
        "FORMULA_BUDGET": 3000,
        "FORMULA_STD": 5000,
        "FORMULA_PREM": 8000
    }
    
    DIAPER_COST = { "BUDGET": 9, "BRANDED": 15 }
    CLOTHING_COST = { "BUDGET": 1000, "STANDARD": 2500, "PREMIUM": 5000 }
    HEALTH_COST = { "GOVT": 3000, "PVT_PED": 15000, "PVT_PLUS": 30000 }
    
    # Childcare Base Rates
    CHILDCARE_COST = { "NONE": 0, "PART_TIME": 6000, "FULL_TIME": 12000 }
    
    GEAR_ITEMS = {
        "cradle": { "budget": 3000, "premium": 10000 },
        "stroller": { "budget": 4000, "premium": 15000 },
        "carrier": { "budget": 1500, "premium": 5000 },
        "carseat": { "budget": 5000, "premium": 18000 },
        "walker": { "budget": 1500, "premium": 4000 },
        "bedding": { "budget": 500, "premium": 2000 },
        "mosquito_net": { "budget": 400, "premium": 1200 },
    }

    # Calculation
    city_factor = CITIES.get(req.city_tier, 1.0)
    
    # A. Delivery
    base_del = DELIVERY_COSTS.get(req.hospital_type, {}).get(req.delivery_type, 0)
    standard_delivery = base_del * city_factor
    
    if req.custom_delivery_cost is not None:
        delivery_total = req.custom_delivery_cost
    else:
        delivery_total = standard_delivery

    # B. Feeding
    if req.feeding_type == "BREAST":
        standard_feeding = FEEDING_COSTS["BREAST"]
    elif req.feeding_type == "FORMULA":
        key = f"FORMULA_{req.formula_tier or 'STD'}"
        standard_feeding = FEEDING_COSTS.get(key, 5000)
    else: # Mixed
        key = f"FORMULA_{req.formula_tier or 'STD'}"
        f_cost = FEEDING_COSTS.get(key, 5000)
        standard_feeding = (FEEDING_COSTS["BREAST"] + f_cost) / 1.5
        
    if req.custom_feeding_cost is not None:
        feeding_total = req.custom_feeding_cost
    else:
        feeding_total = standard_feeding

    # C. Hygiene
    d_cost = req.diapers_per_day * 30 * DIAPER_COST.get(req.diaper_brand, 15)
    w_cost = 500 if req.wipes_enabled else 0
    standard_hygiene = d_cost + w_cost
    
    if req.custom_hygiene_cost is not None:
        hygiene_total = req.custom_hygiene_cost
    else:
        hygiene_total = standard_hygiene

    # D. Clothing
    standard_clothing = CLOTHING_COST.get(req.clothing_tier, 2500)
    
    if req.custom_clothing_cost is not None:
        clothing_total = req.custom_clothing_cost
    else:
        clothing_total = standard_clothing

    # E. Healthcare (Yearly)
    standard_health_yearly = HEALTH_COST.get(req.health_type, 15000) * city_factor
    
    if req.custom_health_cost is not None:
        health_yearly_total = req.custom_health_cost
    else:
        health_yearly_total = standard_health_yearly
    
    health_monthly = health_yearly_total / 12

    # F. Childcare
    base_cc = CHILDCARE_COST.get(req.childcare_type, 0)
    # Metro multiplier
    cc_factor = 1.0
    if req.city_tier == "METRO": cc_factor = 1.4
    elif req.city_tier == "TIER3": cc_factor = 0.7
    standard_childcare = base_cc * cc_factor
    
    if req.custom_childcare_cost is not None:
        childcare_total = req.custom_childcare_cost
    else:
        childcare_total = standard_childcare

    # G. Gear
    standard_gear = 0
    for item, tier in req.gear_selection.items():
        cost_info = GEAR_ITEMS.get(item)
        if cost_info:
            standard_gear += cost_info.get(tier, cost_info.get("budget", 0))
            
    if req.custom_gear_cost is not None:
        gear_total = req.custom_gear_cost
    else:
        gear_total = standard_gear

    # H. Toys
    standard_toys = 1000
    toys_total = req.custom_toy_cost if req.custom_toy_cost is not None else standard_toys

    # Totals
    monthly_recurring = feeding_total + hygiene_total + clothing_total + childcare_total + toys_total + health_monthly
    
    one_time = delivery_total + gear_total
    
    first_year = one_time + (monthly_recurring * 12)
    
    return {
        "delivery": int(delivery_total),
        "feeding": int(feeding_total),
        "hygiene": int(hygiene_total),
        "clothing": int(clothing_total),
        "healthYearly": int(health_yearly_total),
        "childcare": int(childcare_total),
        "gear": int(gear_total),
        "toys": int(toys_total),
        
        "standard_delivery": int(standard_delivery),
        "standard_feeding": int(standard_feeding),
        "standard_hygiene": int(standard_hygiene),
        "standard_clothing": int(standard_clothing),
        "standard_healthYearly": int(standard_health_yearly),
        "standard_childcare": int(standard_childcare),
        "standard_gear": int(standard_gear),
        "standard_toys": int(standard_toys),
        
        "monthlyTotal": int(monthly_recurring),
        "firstYearTotal": int(first_year),
        "oneTime": int(one_time)
    }
