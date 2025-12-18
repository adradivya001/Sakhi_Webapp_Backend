"""Quick test of routing"""
from modules.model_gateway import get_model_gateway, Route

print("Initializing gateway...")
gateway = get_model_gateway()

tests = [
    "hello",
    "severe bleeding", 
    "what is folic acid"
]

print("\nTesting routing decisions:\n")
for query in tests:
    route = gateway.decide_route(query)
    print(f"{query:30} -> {route.value}")

print("\nDone!")
