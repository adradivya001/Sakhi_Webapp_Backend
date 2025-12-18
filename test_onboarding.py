# test_onboarding.py
"""
Automated test script for onboarding state engine.
Tests the stateless onboarding flow for all relationship types.
"""

import json
from modules.onboarding_engine import OnboardingRequest, get_next_question
from modules.onboarding_config import get_questions_for_relationship


def test_herself_flow():
    """Test complete 'herself' onboarding flow (7 steps)"""
    print("=" * 60)
    print("TEST: 'herself' relationship flow")
    print("=" * 60)
    
    parent_profile_id = "test-uuid-herself"
    relationship_type = "herself"
    answers = {}
    
    # Step 1: Get age question
    req = OnboardingRequest(parent_profile_id, relationship_type, 1, answers)
    resp = get_next_question(req)
    data = resp.to_dict()
    
    print(f"\nStep 1:")
    print(json.dumps(data, indent=2))
    assert data["step"] == 1
    assert data["total_steps"] == 7
    assert data["question"]["field_name"] == "age"
    assert data["question"]["type"] == "number"
    
    # Answer: age = 28
    answers["age"] = 28
    
    # Step 2: Get tryingDuration question
    req = OnboardingRequest(parent_profile_id, relationship_type, 2, answers)
    resp = get_next_question(req)
    data = resp.to_dict()
    
    print(f"\nStep 2:")
    print(json.dumps(data, indent=2))
    assert data["step"] == 2
    assert data["question"]["field_name"] == "tryingDuration"
    assert len(data["question"]["options"]) == 4
    
    # Answer: tryingDuration
    answers["tryingDuration"] = "1–2 years"
    
    # Step 3: previousTreatments
    req = OnboardingRequest(parent_profile_id, relationship_type, 3, answers)
    resp = get_next_question(req)
    data = resp.to_dict()
    
    print(f"\nStep 3:")
    print(json.dumps(data, indent=2))
    assert data["question"]["field_name"] == "previousTreatments"
    
    answers["previousTreatments"] = "No / first time"
    
    # Step 4: diagnosis
    req = OnboardingRequest(parent_profile_id, relationship_type, 4, answers)
    resp = get_next_question(req)
    data = resp.to_dict()
    
    print(f"\nStep 4:")
    print(json.dumps(data, indent=2))
    assert data["question"]["field_name"] == "diagnosis"
    
    answers["diagnosis"] = "Both"
    
    # Step 5: partnerAge (optional)
    req = OnboardingRequest(parent_profile_id, relationship_type, 5, answers)
    resp = get_next_question(req)
    data = resp.to_dict()
    
    print(f"\nStep 5:")
    print(json.dumps(data, indent=2))
    assert data["question"]["field_name"] == "partnerAge"
    assert data["question"]["allow_not_applicable"] == True
    
    # Test skipping optional field (null)
    answers["partnerAge"] = None
    
    # Step 6: previousPregnancy
    req = OnboardingRequest(parent_profile_id, relationship_type, 6, answers)
    resp = get_next_question(req)
    data = resp.to_dict()
    
    print(f"\nStep 6:")
    print(json.dumps(data, indent=2))
    assert data["question"]["field_name"] == "previousPregnancy"
    
    answers["previousPregnancy"] = "Never"
    
    # Step 7: priority
    req = OnboardingRequest(parent_profile_id, relationship_type, 7, answers)
    resp = get_next_question(req)
    data = resp.to_dict()
    
    print(f"\nStep 7:")
    print(json.dumps(data, indent=2))
    assert data["question"]["field_name"] == "priority"
    
    answers["priority"] = "Medical process"
    
    # Final step: Should return completion
    req = OnboardingRequest(parent_profile_id, relationship_type, 8, answers)
    resp = get_next_question(req)
    data = resp.to_dict()
    
    print(f"\nCompletion:")
    print(json.dumps(data, indent=2))
    assert data["completed"] == True
    assert data["parent_profile_id"] == parent_profile_id
    assert data["relationship_type"] == relationship_type
    assert len(data["answers_json"]) == 7
    
    print("\n✓ 'herself' flow test PASSED")


def test_himself_flow():
    """Test 'himself' onboarding flow (5 steps)"""
    print("\n" + "=" * 60)
    print("TEST: 'himself' relationship flow")
    print("=" * 60)
    
    parent_profile_id = "test-uuid-himself"
    relationship_type = "himself"
    answers = {}
    
    # Step 1
    req = OnboardingRequest(parent_profile_id, relationship_type, 1, answers)
    resp = get_next_question(req)
    data = resp.to_dict()
    
    print(f"\nStep 1:")
    print(json.dumps(data, indent=2))
    assert data["step"] == 1
    assert data["total_steps"] == 5
    assert data["question"]["field_name"] == "tryingForBaby"
    
    answers["tryingForBaby"] = "Actively trying"
    
    # Step 2
    answers["smokingDrinking"] = "No"
    
    # Step 3
    answers["fertilityTests"] = "Both tested"
    
    # Step 4
    answers["healthProblems"] = "No problems"
    
    # Step 5
    answers["previousIVF"] = "First time"
    
    # Check completion
    req = OnboardingRequest(parent_profile_id, relationship_type, 6, answers)
    resp = get_next_question(req)
    data = resp.to_dict()
    
    print(f"\nCompletion:")
    print(json.dumps(data, indent=2))
    assert data["completed"] == True
    assert len(data["answers_json"]) == 5
    
    print("\n✓ 'himself' flow test PASSED")


def test_invalid_relationship():
    """Test error handling for invalid relationship type"""
    print("\n" + "=" * 60)
    print("TEST: Invalid relationship type error handling")
    print("=" * 60)
    
    try:
        req = OnboardingRequest("test-id", "invalid_type", 1, {})
        resp = get_next_question(req)
        print("✗ Should have raised ValueError")
        assert False
    except ValueError as e:
        print(f"✓ Correctly raised ValueError: {e}")
        assert "Invalid relationship_type" in str(e)


def test_optional_field_handling():
    """Test that optional fields can be null"""
    print("\n" + "=" * 60)
    print("TEST: Optional field handling")
    print("=" * 60)
    
    parent_profile_id = "test-optional"
    relationship_type = "herself"
    
    # Fill all required fields but leave partnerAge as null
    answers = {
        "age": 30,
        "tryingDuration": "1–2 years",
        "previousTreatments": "IVF",
        "diagnosis": "Unexplained",
        "partnerAge": None,  # Optional field set to null
        "previousPregnancy": "Never",
        "priority": "Emotional stress"
    }
    
    req = OnboardingRequest(parent_profile_id, relationship_type, 8, answers)
    resp = get_next_question(req)
    data = resp.to_dict()
    
    print(json.dumps(data, indent=2))
    assert data["completed"] == True
    assert data["answers_json"]["partnerAge"] is None
    
    print("\n✓ Optional field test PASSED")


def test_all_relationship_types():
    """Test that all relationship types have valid question sets"""
    print("\n" + "=" * 60)
    print("TEST: All relationship types validation")
    print("=" * 60)
    
    relationship_types = [
        "herself", "himself", "father", "mother",
        "father_in_law", "mother_in_law", "sibling"
    ]
    
    for rel_type in relationship_types:
        questions = get_questions_for_relationship(rel_type)
        print(f"\n{rel_type}: {len(questions)} questions")
        
        # Verify each question has required fields
        for q in questions:
            assert "field_name" in q
            assert "text" in q
            assert "type" in q
            assert "allow_not_applicable" in q
            
            if q["type"] == "radio":
                assert "options" in q
                assert len(q["options"]) > 0
        
        print(f"  ✓ Valid question set")
    
    print("\n✓ All relationship types validation PASSED")


if __name__ == "__main__":
    print("\n" + "█" * 60)
    print("ONBOARDING STATE ENGINE TEST SUITE")
    print("█" * 60)
    
    try:
        test_herself_flow()
        test_himself_flow()
        test_invalid_relationship()
        test_optional_field_handling()
        test_all_relationship_types()
        
        print("\n" + "█" * 60)
        print("ALL TESTS PASSED ✓")
        print("█" * 60 + "\n")
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        raise
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        raise
