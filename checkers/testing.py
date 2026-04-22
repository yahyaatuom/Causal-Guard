import sys
import json
import os

sys.path.append(r"C:\Users\Dell\Desktop\Causal-Guard\checkers")

from c1_temporal import C1TemporalChecker
from error_handling import ScenarioLoader

paths = [r"C:\Users\Dell\Desktop\Causal-Guard\data\json\scenarios.json"]
loader = ScenarioLoader(paths)
scenarios_list = loader.load()

def run_test():
    with open(r"C:\Users\Dell\Desktop\Causal-Guard\data\json\scenarios.json", 'r', encoding='utf-8') as f:
        data = json.load(f)
        scenarios = data.get("scenarios", [])[:10]

    checker = C1TemporalChecker()
    results = []
    failed_items=[]

    for s in scenarios:
        explanation_text = s.get("description", "")
        is_valid = checker.check(s, explanation_text)
        results.append({"id": s['id'], "status": "PASS" if is_valid else "FAIL"})
        if not is_valid:
            failed_items.append(s)
    
    print(f"{'ID':<10} | {'STATUS':<6}")
    print("-" * 20)
    for res in results:
        print(f"{res['id']:<10} | {res['status']:<6}")

    with open("failed_scenarios.json", "w") as f:
        json.dump(failed_items, f, indent=4)
    print(f"\n{len(failed_items)} failures saved to failed_scenarios.json")

if __name__ == "__main__":
    run_test()