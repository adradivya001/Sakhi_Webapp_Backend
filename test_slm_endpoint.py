"""
Test SLM endpoint integration
"""
import asyncio
import sys
from modules.slm_client import get_slm_client


async def test_slm_endpoint():
    """Test that the SLM client can connect to the ngrok endpoint."""
    print("=" * 70)
    print("Testing SLM Endpoint Integration")
    print("=" * 70)
    print()
    
    client = get_slm_client()
    
    # Check if running in mock mode
    if client.is_mock():
        print("⚠️  WARNING: SLM client is in MOCK mode")
        print("   Please check that SLM_ENDPOINT_URL is set in .env file")
        return False
    
    print(f"✓ SLM endpoint configured: {client.endpoint_url}")
    print()
    
    # Test 1: Simple chat
    print("Test 1: Simple chat (no RAG)")
    print("-" * 70)
    try:
        response = await client.generate_chat(
            message="Hello, how are you?",
            language="en",
            user_name="Test User"
        )
        print(f"✓ Response received: {response[:200]}...")
        print()
    except Exception as e:
        print(f"✗ Error: {e}")
        print()
        return False
    
    # Test 2: RAG-enhanced chat
    print("Test 2: RAG-enhanced response")
    print("-" * 70)
    try:
        test_context = "Folic acid is a B vitamin that is important for pregnant women."
        response = await client.generate_rag_response(
            context=test_context,
            message="What is folic acid?",
            language="en",
            user_name="Test User"
        )
        print(f"✓ Response received: {response[:200]}...")
        print()
    except Exception as e:
        print(f"✗ Error: {e}")
        print()
        return False
    
    print("=" * 70)
    print("✓ All tests passed! SLM endpoint is working correctly.")
    print("=" * 70)
    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(test_slm_endpoint())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
