# debug_checker.py
import json
from checkers.c3_mechanism import C3MechanismChecker

# Load scenarios
with open('data/json/scenarios.json', 'r') as f:
    data = json.load(f)

checker = C3MechanismChecker()

# Test WD-05 manually
for s in data['scenarios']:
    if s['id'] == 'WD-05':
        print(f"\nTesting {s['id']}")
        print(f"Description: {s['description'][:100]}...")
        
        # Create a simple test explanation
        test_explanation = "Black ice formed at 2°C causing loss of control"
        
        result = checker.check(s, test_explanation)
        print(f"C3 Result: {'❌ FAIL' if not result['passed'] else '✅ PASS'}")
        print(f"Reason: {result.get('reason', 'No reason')}")