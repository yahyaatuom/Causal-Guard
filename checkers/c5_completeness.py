# checkers/c5_completeness.py
import re
import json
from pathlib import Path


class C5CompletenessChecker:
    def __init__(self, kb_path='data/completeness_templates.json'):
        self.name = "C₅ Completeness"
        
        # Load completeness templates
        kb_full_path = Path(__file__).parent.parent / kb_path
        if kb_full_path.exists():
            with open(kb_full_path, 'r', encoding='utf-8') as f:
                self.templates = json.load(f)['templates']
        else:
            self.templates = []
        
        self.coverage_threshold = 0.8  # Default: need 80% of required factors
    
    def check(self, scenario, explanation, context=None):
        """
        Check if explanation includes all necessary causal factors.
        
        Args:
            scenario: dict with scenario information
            explanation: str or dict with LLM explanation
            context: Optional CheckerContext for inter-checker communication
        
        Returns:
            dict with passed (bool), confidence (float), reason (str), details (dict)
        """
        
        # Extract explanation text (handle both string and structured output)
        if isinstance(explanation, dict):
            explanation_text = explanation.get('explanation', '')
            structured_data = explanation.get('structured_output', {})
            # Prefer structured contributing factors if available
            if structured_data and structured_data.get('contributing_factors'):
                structured_factors = structured_data['contributing_factors']
                explanation_text = explanation_text + ' ' + ' '.join(structured_factors)
        else:
            explanation_text = explanation
        
        # Get required factors from scenario
        required_factors = scenario.get('minimal_sufficient_set', [])
        
        # If no required factors, try category-based template
        if not required_factors:
            category = scenario.get('category', '')
            required_factors = self._get_template_factors(category)
        
        if not required_factors:
            return {
                'checker': 'C5',
                'passed': True,
                'confidence': 0.5,
                'reason': 'No required factors specified',
                'details': {'warning': 'Missing minimal_sufficient_set in scenario'}
            }
        
        # Adjust threshold based on context (inter-checker communication)
        if context:
            mechanism_failed = context.has_violation('C3')
            if mechanism_failed:
                # If mechanism is wrong, completeness becomes more critical
                context.add_note("C5: C3 violation detected — checking completeness more strictly")
                self.coverage_threshold = 0.9
            else:
                self.coverage_threshold = 0.8
        
        # Check which factors are mentioned
        mentioned = []
        missing = []
        partial_matches = []
        
        explanation_lower = explanation_text.lower()
        
        for factor in required_factors:
            is_mentioned, match_quality = self._factor_mentioned(factor, explanation_lower)
            if is_mentioned:
                mentioned.append(factor)
                if match_quality == 'partial':
                    partial_matches.append(factor)
            else:
                missing.append(factor)
        
        # Calculate coverage
        coverage = len(mentioned) / len(required_factors) if required_factors else 1.0
        
        # Identify core factors (essential for this incident type)
        core_factors = self._get_core_factors(required_factors, scenario)
        core_missing = [f for f in core_factors if f in missing]
        
        # Determine pass/fail
        # Pass if: coverage meets threshold OR all core factors are present
        passed = (coverage >= self.coverage_threshold) or (len(core_missing) == 0)
        
        # Calculate confidence
        # Base confidence = coverage
        confidence = coverage
        
        # Penalize if core factors missing
        if core_missing:
            confidence *= 0.7
        
        # Boost if all core factors present
        if len(core_missing) == 0 and coverage < self.coverage_threshold:
            confidence = 0.6  # Almost passed
        
        # Add cross-checker insight
        if context and not passed and mechanism_failed:
            context.add_note("C5 failure may be related to C3 mechanism failure")
        
        # Build reason string
        if passed:
            reason = f'Coverage: {coverage:.1%} ({len(mentioned)}/{len(required_factors)})'
            if partial_matches:
                reason += f' (partial matches: {", ".join(partial_matches[:2])})'
        else:
            reason = f'Missing factors: {", ".join(missing[:5])}'
            if len(missing) > 5:
                reason += f' and {len(missing)-5} more'
        
        return {
            'checker': 'C5',
            'passed': passed,
            'confidence': round(confidence, 3),
            'reason': reason,
            'details': {
                'required': required_factors,
                'mentioned': mentioned,
                'missing': missing,
                'core_factors': core_factors,
                'core_missing': core_missing,
                'coverage': coverage,
                'threshold': self.coverage_threshold,
                'partial_matches': partial_matches
            }
        }
    
    def _factor_mentioned(self, factor, explanation_lower):
        """
        Check if a factor is mentioned in the explanation.
        Returns (is_mentioned, match_quality) where match_quality is 'exact', 'partial', or 'none'
        """
        factor_lower = factor.lower()
        
        # Exact match
        if factor_lower in explanation_lower:
            return True, 'exact'
        
        # Handle specific factor mappings (synonyms)
        factor_mappings = {
            'curved_road_section': ['curve', 'curved', 'bend', 'corner', 'turn'],
            'sub_freezing_temperature': ['freezing', 'below zero', 'cold', 'ice', 'below freezing'],
            'reduced_friction': ['slippery', 'loss of traction', 'skid', 'lost grip'],
            'black_ice_formation': ['black ice', 'ice patch', 'icy road'],
            'insufficient_following_distance': ['tailgating', 'following too close', 'insufficient distance', 'too close'],
            'wet_road_surface': ['wet road', 'damp', 'moist', 'slick surface'],
            'heavy_rain': ['rain', 'downpour', 'heavy rain', 'torrential'],
            'standing_water': ['standing water', 'pool', 'ponding', 'water accumulation'],
            'hydroplaning_physics': ['hydroplaning', 'aquaplaning', 'lost contact', 'water film'],
            'red_light_violation': ['red light', 'ran the light', 'failed to stop', 'ignored signal'],
            'driver_fatigue': ['fatigue', 'tired', 'fell asleep', 'drowsy', 'exhausted'],
            'brake_fade': ['brake fade', 'overheated brakes', 'brake failure', 'lost braking'],
            'tire_blowout': ['blowout', 'tire failure', 'flat tire', 'burst tire'],
            'unsafe_lane_change': ['lane change', 'changed lanes', 'swerved', 'without signaling'],
            'no_signal': ['without signaling', 'no signal', 'did not signal'],
            'emergency_braking': ['braked hard', 'emergency brake', 'slammed brakes'],
            'pedestrian_crossing': ['pedestrian', 'crossing', 'zebra crossing', 'crosswalk'],
            'airborne_debris': ['debris', 'banner', 'object', 'obstruction'],
            'evasive_maneuver': ['swerved', 'avoid', 'dodged', 'evasive'],
            'mountain_road_geometry': ['mountain road', 'incline', 'descent', 'slope', 'steep'],
            'underpass_geometry': ['underpass', 'depression', 'low point', 'dip'],
            'engine_hydro_lock': ['hydro-lock', 'stalled', 'water in engine', 'hydrolock'],
            'drop_zone_capacity_exceeded': ['drop-off', 'drop zone', 'queuing', 'blocked lanes'],
            'security_screening_bottleneck': ['security screening', 'checkpoint', 'bottleneck', 'queue']
        }
        
        if factor in factor_mappings:
            for synonym in factor_mappings[factor]:
                if synonym in explanation_lower:
                    return True, 'partial'
        
        # Check for word stems (e.g., "curve" matches "curved")
        if '_' in factor:
            # snake_case to word
            words = factor.split('_')
            for word in words:
                if len(word) > 3 and word in explanation_lower:
                    return True, 'partial'
        
        return False, 'none'
    
    def _get_core_factors(self, factors, scenario):
        """
        Identify which factors are core/essential for this incident.
        Core factors are those without which the explanation is meaningless.
        """
        category = scenario.get('category', '')
        
        # Define core factors by category
        category_core = {
            'Weather': [
                'weather_event', 'primary_cause', 'road_condition'
            ],
            'Traffic Accident': [
                'driver_action', 'primary_cause', 'collision_type'
            ],
            'Road Maintenance': [
                'maintenance_activity', 'safety_failure', 'hazard'
            ],
            'Public Event': [
                'event_type', 'capacity_issue', 'traffic_impact'
            ]
        }.get(category, [])
        
        core = []
        for f in factors:
            f_lower = f.lower()
            # Check if it matches category core patterns
            for core_pattern in category_core:
                if core_pattern in f_lower:
                    core.append(f)
                    break
        
        # If no core factors identified, treat first 2 factors as core
        if not core and len(factors) >= 2:
            core = factors[:2]
        
        return core
    
    def _get_template_factors(self, category):
        """Get required factors from category template"""
        for template in self.templates:
            if template.get('category') == category:
                # Return category-level required factors
                return template.get('required', [])
        
        # Domain-specific fallbacks
        domain_factors = {
            'Weather': ['weather_event', 'road_condition', 'driver_action'],
            'Traffic Accident': ['primary_cause', 'contributing_factor', 'outcome'],
            'Road Maintenance': ['maintenance_activity', 'safety_failure', 'resulting_hazard'],
            'Public Event': ['event_type', 'capacity_issue', 'traffic_impact'],
            'Healthcare': ['primary_condition', 'contributing_factors', 'outcome'],
            'Finance': ['trigger_event', 'market_condition', 'result']
        }
        
        return domain_factors.get(category, [])
    
    def get_completeness_report(self, scenario, explanation):
        """
        Detailed report on what's missing (for debugging/UI).
        """
        result = self.check(scenario, explanation)
        
        if result['passed']:
            return {
                'status': 'complete',
                'coverage': result['details']['coverage'],
                'mentioned': result['details']['mentioned']
            }
        else:
            return {
                'status': 'incomplete',
                'coverage': result['details']['coverage'],
                'missing': result['details']['missing'],
                'core_missing': result['details']['core_missing'],
                'suggestion': self._generate_suggestion(result['details']['missing'])
            }
    
    def _generate_suggestion(self, missing_factors):
        """Generate human-readable suggestion for missing factors"""
        if not missing_factors:
            return None
        
        suggestions = {
            'curved_road_section': 'Consider mentioning the curve geometry',
            'sub_freezing_temperature': 'Specify that temperature was below freezing',
            'insufficient_following_distance': 'Note that following distance was inadequate',
            'wet_road_surface': 'Mention that the road was wet/slick',
            'driver_fatigue': 'Include that driver fatigue was a factor',
            'pedestrian_crossing': 'Note the presence of a pedestrian crossing'
        }
        
        missing_suggestions = []
        for factor in missing_factors[:3]:
            if factor in suggestions:
                missing_suggestions.append(suggestions[factor])
        
        if missing_suggestions:
            return f"Suggest adding: {'; '.join(missing_suggestions)}"
        
        return f"Missing factors: {', '.join(missing_factors[:3])}"