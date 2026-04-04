# debug.py
import json

with open('data/json/scenarios.json', 'r' ,encoding='utf-8') as f:
    all_scenarios = json.load(f)['scenarios']
    
with open('results.json', 'r') as f:
    results = json.load(f)

result_ids = [r['scenario_id'] for r in results]
all_ids = [s['id'] for s in all_scenarios]

missing = set(all_ids) - set(result_ids)
print(f"Total scenarios: {len(all_ids)}")
print(f"Results: {len(result_ids)}")
print(f"Missing: {missing}")