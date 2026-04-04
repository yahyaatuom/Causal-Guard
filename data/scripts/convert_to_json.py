# data/scripts/convert_to_json.py
import pandas as pd
import json
import os
from datetime import datetime

def parse_list_field(value):
    """Parse comma-separated list from CSV, handling {braces}"""
    if pd.isna(value) or value == '':
        return []
    # Remove { } if present
    value = str(value).strip('{}').strip()
    if not value:
        return []
    return [item.strip() for item in value.split(',') if item.strip()]

def parse_perturbations(row):
    """Parse perturbation columns into list of dicts"""
    perturbations = []
    
    # Look for Perturbation_1, Perturbation_2, Perturbation_3 columns
    for i in range(1, 4):
        pert_col = f'Perturbation_{i}'
        exp_col = 'Expected_Perturbation_Violation'
        
        if pert_col in row and not pd.isna(row[pert_col]):
            # Get expected violation (might be comma-separated for multiple perturbations)
            expected = ''
            if exp_col in row and not pd.isna(row[exp_col]):
                exp_values = str(row[exp_col]).split(',')
                if len(exp_values) >= i:
                    expected = exp_values[i-1].strip()
            
            perturbations.append({
                "id": f"P{i}",
                "description": str(row[pert_col]).strip(),
                "expected_violation": expected
            })
    
    return perturbations

def extract_timeline(description):
    """Extract timeline events from description (simplified)"""
    # This is a simplified version - you may want to enhance this
    timeline = []
    
    # Look for time patterns in description
    import re
    time_pattern = r'(\d{1,2}):(\d{2})\s*(AM|PM)?'
    
    # For now, return empty list - you can enhance this later
    return timeline

def convert_excel_to_json(excel_path, output_path):
    """Convert Excel scenarios to JSON format"""
    
    print(f"Reading Excel file: {excel_path}")
    df = pd.read_excel(excel_path, sheet_name='Scenario')
    
    scenarios = []
    
    for idx, row in df.iterrows():
        # Skip if no Scenario_ID
        if pd.isna(row.get('Scenario_ID')):
            continue
            
        scenario_id = str(row['Scenario_ID']).strip()
        print(f"Processing: {scenario_id}")
        
        # Parse minimal sufficient set (it's in {format} with commas)
        minimal_set = parse_list_field(row.get('Minimal_Sufficient_Set', ''))
        
        # Parse contributing factors
        contributing = parse_list_field(row.get('Contributing_Factors', ''))
        
        # Parse non-causal correlates
        non_causal = parse_list_field(row.get('Non_Causal_Correlates', ''))
        
        # Get temperature if available (for environment)
        temp = None
        desc = str(row.get('Incident_Description', ''))
        import re
        temp_match = re.search(r'(\d+)[°\s]?C', desc)
        if temp_match:
            temp = int(temp_match.group(1))
        
        # Build scenario object
        scenario = {
            "id": scenario_id,
            "category": str(row.get('Incident_Category', '')).strip(),
            "complexity_level": int(row.get('Complexity_Level', 2)) if not pd.isna(row.get('Complexity_Level')) else 2,
            "description": str(row.get('Incident_Description', '')).strip(),
            "context": {
                "timeline": [],  # You can enhance this later
                "locations": [
                    {
                        "name": str(row.get('Location', '')).strip(),
                        "type": "unknown",
                        "coordinates": []  # Add coordinates if you have them
                    }
                ],
                "road_network": {
                    "segment_id": "",
                    "geometry": "",
                    "gradient": None,
                    "speed_limit": None
                },
                "environment": {
                    "weather": str(row.get('Primary Weather', '')).strip() if not pd.isna(row.get('Primary Weather')) else "",
                    "temperature": temp,
                    "visibility": None,
                    "road_condition": "",
                    "lighting": str(row.get('Time_of_Day', '')).strip() if not pd.isna(row.get('Time_of_Day')) else ""
                }
            },
            "causal_ground_truth": {
                "primary_cause": str(row.get('Primary_Cause', '')).strip() if not pd.isna(row.get('Primary_Cause')) else "",
                "mechanism": str(row.get('Mechanism_Description', '')).strip() if not pd.isna(row.get('Mechanism_Description')) else "",
                "contributing_factors": contributing,
                "non_causal_correlates": non_causal
            },
            "minimal_sufficient_set": minimal_set,
            "perturbations": parse_perturbations(row)
        }
        
        scenarios.append(scenario)
    
    # Create final JSON structure
    output = {
        "metadata": {
            "generated": datetime.now().isoformat(),
            "source": os.path.basename(excel_path),
            "scenario_count": len(scenarios)
        },
        "scenarios": scenarios
    }
    
    # Write to file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Successfully converted {len(scenarios)} scenarios")
    print(f"📁 Output saved to: {output_path}")
    
    # Print summary by category
    categories = {}
    for s in scenarios:
        cat = s['category']
        categories[cat] = categories.get(cat, 0) + 1
    
    print("\n📊 Summary by category:")
    for cat, count in categories.items():
        print(f"  {cat}: {count} scenarios")

if __name__ == "__main__":
    # Set your paths here
    excel_path = "data/raw/Causal_Admissibility_Evaluation.xlsx"
    output_path = "data/json/scenarios.json"
    
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Run conversion
    convert_excel_to_json(excel_path, output_path)