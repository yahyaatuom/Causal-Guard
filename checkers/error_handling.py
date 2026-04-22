import json
import os

class ScenarioDataError(Exception):
    """Custom exception for structural issues within the JSON data."""
    pass

class ScenarioLoader:
    def __init__(self, paths):
        self.paths = paths
        self.required_fields = ["id", "category", "description"]

    def load(self):
        """Attempts to load from multiple pathes and validates content."""
        for path in self.paths:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    raw_data = json.load(f)
                    return self._validate_and_filter(raw_data)
            except FileNotFoundError:
                print(f"Skipping: {path} not found.")
                continue
            except json.JSONDecodeError:
                print(f"CRITICAL: {path} is not a valid JSON file.")
                continue

        print("Error: None of the provided paths were accessible.")
        return []
    def _validate_and_filter(self, data):
        if not isinstance(data, dict) or "scenarios" not in data:
            raise ScenarioDataError("Root JSON must be a dictionary containing a 'scenarios' key.")
        
        all_scenarios = data["scenarios"]
        valid_scenarios = []

        for index, s in enumerate(all_scenarios):
            missing = [field for field in self.required_fields if field not in s]

            if missing:
                s_id = s.get("id", f"Index {index}")
                print(f"WARNING: Scenario {s_id} skipped. Missing fields: {', '.join(missing)}")
                continue    

            valid_scenarios.append(s)
        
        print(f"Successfully loaded {len(valid_scenarios)}/{len(all_scenarios)} scenarios.")
        return valid_scenarios

candidate_paths = [
r"C:\Users\Dell\Desktop\Causal-Guard\data\json\scenarios.json",
]

loader = ScenarioLoader(candidate_paths)
scenarios = loader.load()