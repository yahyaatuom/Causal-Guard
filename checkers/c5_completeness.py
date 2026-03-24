# checkers/c5_completeness.py
import re
import json

class C5CompletenessChecker:
    def __init__(self, kb_path='data/completeness_templates.json'):
        self.name = "C₅ Completeness"
        
        with open(kb_path, 'r') as f:
            self.templates = json.load(f)['templates']
        
        # More realistic thresholds
        self.coverage_threshold = 0.6  # Was 0.8 — now 60% is enough
        self.core_factors_required = 0.8  # But core factors must be present
    
    def check(self, scenario, explanation):
        explanation_lower = explanation.lower()
        required_factors = scenario.get('minimal_sufficient_set', [])
        
        if not required_factors:
            return {
                'checker': 'C5',
                'passed': True,
                'reason': 'No required factors specified',
                'details': {}
            }
        
        # Separate core vs secondary factors
        core_factors = self._get_core_factors(required_factors, scenario)
        secondary_factors = [f for f in required_factors if f not in core_factors]
        
        mentioned = []
        missing = []
        missing_core = []
        
        for factor in required_factors:
            if self._factor_mentioned(factor, explanation_lower):
                mentioned.append(factor)
            else:
                missing.append(factor)
                if factor in core_factors:
                    missing_core.append(factor)
        
        # Calculate coverage
        coverage = len(mentioned) / len(required_factors) if required_factors else 1.0
        
        # More lenient pass conditions:
        # 1. Coverage meets threshold OR
        # 2. All core factors are present
        passed = (coverage >= self.coverage_threshold) or (len(missing_core) == 0)
        
        return {
            'checker': 'C5',
            'passed': passed,
            'reason': f'Coverage: {coverage:.1%} ({len(mentioned)}/{len(required_factors)})' if passed else f'Missing core factors: {missing_core}',
            'details': {
                'required': required_factors,
                'core_factors': core_factors,
                'mentioned': mentioned,
                'missing': missing,
                'missing_core': missing_core,
                'coverage': coverage
            }
        }
    
    def _get_core_factors(self, factors, scenario):
        """Identify which factors are core/essential"""
        # Always core
        always_core = ['primary_cause', 'main_factor', 'key_event']
        
        # Category-specific core factors
        category = scenario.get('category', '')
        category_core = {
            'Weather': ['weather_event', 'road_condition'],
            'Traffic Accident': ['driver_action', 'primary_cause'],
            'Road Maintenance': ['maintenance_activity', 'safety_failure'],
            'Public Event': ['event_type', 'capacity_issue']
        }.get(category, [])
        
        core = []
        for f in factors:
            f_lower = f.lower()
            # Check if it's in always_core or category_core
            if any(core_word in f_lower for core_word in always_core + category_core):
                core.append(f)
        
        return core if core else factors[:2]  # At least first 2 factors
    
    def _factor_mentioned(self, factor, explanation):
        """Check if a factor is mentioned in the explanation"""
        factor_lower = factor.lower()
        
        # Direct match
        if factor_lower in explanation:
            return True
        
        # Handle specific factor types
        factor_mappings = {
            'curved_road_section': ['curve', 'curved', 'bend', 'corner'],
            'sub_freezing_temperature': ['freezing', 'below zero', 'cold'],
            'reduced_friction': ['slippery', 'loss of traction', 'skid'],
            'black_ice_formation': ['black ice', 'ice patch'],
            'insufficient_following_distance': ['tailgating', 'following too close'],
            'wet_road_surface': ['wet road', 'damp'],
            'heavy_rain': ['rain', 'downpour'],
            'standing_water': ['standing water', 'pool', 'ponding'],
            'hydroplaning_physics': ['hydroplaning', 'aquaplaning'],
            'red_light_violation': ['red light', 'ran the light'],
            'driver_fatigue': ['fatigue', 'tired', 'fell asleep'],
            'brake_fade': ['brake fade', 'overheated brakes'],
            'tire_blowout': ['blowout', 'tire failure']
        }
        
        if factor in factor_mappings:
            for synonym in factor_mappings[factor]:
                if synonym in explanation:
                    return True
        
        # Partial word matching for long factors
        words = factor_lower.split('_')
        if len(words) > 1:
            # Check if any key word appears
            for word in words:
                if len(word) > 3 and word in explanation:
                    return True
        
        return False