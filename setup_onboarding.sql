-- Add columns for onboarding flow
ALTER TABLE sakhi_users ADD COLUMN IF NOT EXISTS gender text;
ALTER TABLE sakhi_users ADD COLUMN IF NOT EXISTS location text;
-- Removed onboarding_step as we will use NULL checks
ALTER TABLE sakhi_users ALTER COLUMN email DROP NOT NULL;
ALTER TABLE sakhi_users ALTER COLUMN password_hash DROP NOT NULL;
