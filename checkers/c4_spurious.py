# checkers/c4_spurious.py
import re
import json

class C4SpuriousChecker:
    def __init__(self, kb_path='data/spurious_patterns.json'):
        self.name = "C₄ Non-Spuriousness"
        
        # Load spurious patterns
        with open(kb_path, 'r') as f:
            self.patterns = json.load(f)['patterns']
    
    def check(self, scenario, explanation):
        """
        Check if explanation uses spurious correlations as causes
        """
        explanation_lower = explanation.lower()
        violations = []
        
        # Check each spurious pattern
        for pattern in self.patterns:
            matches = re.findall(pattern['regex'], explanation, re.IGNORECASE)
            
            for match in matches:
                # Handle both string and tuple returns from re.findall
                if isinstance(match, tuple):
                    # Join all parts of the tuple into one string
                    match_text = ' '.join([str(part) for part in match if part])
                else:
                    match_text = str(match)
                
                if not self._is_causal_in_scenario(match_text, scenario):
                    violations.append({
                        'factor': match_text,
                        'pattern': pattern['name'],
                        'reason': pattern['reason']
                    })
        
        passed = len(violations) == 0
        
        return {
            'checker': 'C4',
            'passed': passed,
            'reason': 'No spurious correlations detected' if passed else f'{len(violations)} spurious factor(s)',
            'details': {
                'violations': violations
            }
        }
    
    def _is_causal_in_scenario(self, factor, scenario):
        """Check if a factor is actually causal in the scenario"""
        factor_lower = factor.lower()
        
        # Check non-causal correlates from scenario
        if 'causal_ground_truth' in scenario:
            non_causal = scenario['causal_ground_truth'].get('non_causal_correlates', [])
            for nc in non_causal:
                if isinstance(nc, str) and nc.lower() in factor_lower:
                    return False
        
        # Check if it's in minimal sufficient set (then it IS causal)
        if 'minimal_sufficient_set' in scenario:
            for causal in scenario['minimal_sufficient_set']:
                if isinstance(causal, str) and causal.lower() in factor_lower:
                    return True
        
        # Common non-causal patterns
        common_spurious = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 
                          'saturday', 'sunday', 'morning', 'evening', 'afternoon',
                          'red', 'blue', 'white', 'black', 'silver', 'grey', 'yellow']
        
        for word in common_spurious:
            if word in factor_lower and word not in str(scenario.get('description', '')).lower():
                return False
        
        return True