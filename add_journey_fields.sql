-- Add journey tracking columns to sakhi_users table

-- 1. Journey Stage (TTC, PREGNANT, PARENT)
ALTER TABLE sakhi_users 
ADD COLUMN IF NOT EXISTS sakhi_journey_stage text;

-- 2. Journey Date (LMP, Due Date, or DOB)
ALTER TABLE sakhi_users 
ADD COLUMN IF NOT EXISTS sakhi_journey_date date;

-- 3. Journey Date Type (LMP, DUE_DATE, DOB)
ALTER TABLE sakhi_users 
ADD COLUMN IF NOT EXISTS sakhi_journey_date_type text;

-- Optional: Add constraints if you want to enforce specific values
-- ALTER TABLE sakhi_users ADD CONSTRAINT check_journey_stage CHECK (sakhi_journey_stage IN ('TTC', 'PREGNANT', 'PARENT'));
-- ALTER TABLE sakhi_users ADD CONSTRAINT check_journey_date_type CHECK (sakhi_journey_date_type IN ('LMP', 'DUE_DATE', 'DOB'));
