-- Add 'other' to the relationship_type check constraint on sakhi_parent_profiles table

-- Step 1: Drop the existing check constraint
ALTER TABLE sakhi_parent_profiles 
DROP CONSTRAINT IF EXISTS sakhi_parent_profiles_relationship_type_check;

-- Step 2: Add a new check constraint with 'other' included
ALTER TABLE sakhi_parent_profiles 
ADD CONSTRAINT sakhi_parent_profiles_relationship_type_check 
CHECK (relationship_type IN ('herself', 'himself', 'father', 'mother', 'father_in_law', 'mother_in_law', 'sibling', 'other'));
