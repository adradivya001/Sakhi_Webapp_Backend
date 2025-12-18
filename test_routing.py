#!/usr/bin/env python3
"""
Test script for the Hybrid Model Architecture routing logic.
Tests the semantic router with different query types.
"""

import sys
sys.path.insert(0, '.')

from modules.model_gateway import get_model_gateway, Route


def test_routing():
    """Test the model gateway routing decisions."""
    print("=" * 70)
    print("Testing Model Gateway Routing")
    print("=" * 70)
    print()
    
    gateway = get_model_gateway()
    
    # Test cases for each route type
    test_cases = [
        # Small talk queries (should route to SLM_DIRECT)
        ("hello", Route.SLM_DIRECT),
        ("hi there", Route.SLM_DIRECT),
        ("thank you", Route.SLM_DIRECT),
        ("who are you", Route.SLM_DIRECT),
        ("good morning", Route.SLM_DIRECT),
        
        # Simple medical queries (should route to SLM_RAG or OPENAI_RAG)
        ("what is folic acid", [Route.SLM_RAG, Route.OPENAI_RAG]),
        ("foods for iron", [Route.SLM_RAG, Route.OPENAI_RAG]),
        ("headache remedies", [Route.SLM_RAG, Route.OPENAI_RAG]),
        ("vitamin d benefits", [Route.SLM_RAG, Route.OPENAI_RAG]),
        
        # Complex medical queries (should route to OPENAI_RAG)
        ("severe bleeding", Route.OPENAI_RAG),
        ("baby not moving", Route.OPENAI_RAG),
        ("sharp abdominal pain", Route.OPENAI_RAG),
        ("emergency symptoms", Route.OPENAI_RAG),
    ]
    
    passed = 0
    failed = 0
    
    for query, expected in test_cases:
        print(f"\nQuery: '{query}'")
        actual = gateway.decide_route(query)
        
        # Check if expected is a list (multiple valid routes) or single route
        if isinstance(expected, list):
            is_correct = actual in expected
            expected_str = " or ".join([r.value for r in expected])
        else:
            is_correct = actual == expected
            expected_str = expected.value
        
        status = "✓ PASS" if is_correct else "✗ FAIL"
        print(f"Expected: {expected_str}")
        print(f"Actual: {actual.value}")
        print(f"Status: {status}")
        
        if is_correct:
            passed += 1
        else:
            failed += 1
        print("-" * 70)
    
    print()
    print("=" * 70)
    print(f"Test Results: {passed} passed, {failed} failed out of {passed + failed} tests")
    print("=" * 70)
    
    return failed == 0


if __name__ == "__main__":
    try:
        success = test_routing()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\nError running tests: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
