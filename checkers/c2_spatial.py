# checkers/c2_spatial.py (UPDATED)
import re
import math

class C2SpatialChecker:
    def __init__(self):
        self.name = "C₂ Spatial Relevance"
        self.max_distance_km = 2.0
    
    def check(self, scenario, explanation):
        """
        Check if causes are spatially relevant to effects
        """
        
        # Extract location mentions from explanation
        mentioned_locations = self._extract_locations(explanation)
        
        # Get scenario locations from multiple possible sources
        scenario_locations = self._get_scenario_locations(scenario)
        
        # If no locations found in scenario, assume pass (can't verify)
        if not scenario_locations:
            return {
                'checker': 'C2',
                'passed': True,
                'reason': 'No locations in scenario to verify against',
                'details': {
                    'mentioned_locations': mentioned_locations,
                    'note': 'Skipped verification - insufficient scenario data'
                }
            }
        
        violations = []
        
        for loc in mentioned_locations:
            is_plausible, reason = self._check_location_plausibility(
                loc, scenario_locations, scenario
            )
            
            if not is_plausible:
                violations.append({
                    'location': loc['text'],
                    'reason': reason
                })
        
        passed = len(violations) == 0
        
        return {
            'checker': 'C2',
            'passed': passed,
            'reason': 'All locations spatially relevant' if passed else f'{len(violations)} spatial violation(s)',
            'details': {
                'mentioned_locations': mentioned_locations,
                'scenario_locations': [loc['name'] for loc in scenario_locations],
                'violations': violations
            }
        }
    
    def _extract_locations(self, text):
        """Extract location mentions using patterns"""
        # Common road/location patterns in UAE
        patterns = [
            (r'on\s+([A-Za-z0-9\s]+(?:Road|Street|Highway|E\d+|SZR|Corniche))', 'road'),
            (r'at\s+([A-Za-z0-9\s]+(?:intersection|exit|roundabout|bridge))', 'intersection'),
            (r'near\s+([A-Za-z0-9\s]+(?:Mall|Mosque|Island|City|exit))', 'area'),
            (r'in\s+([A-Za-z0-9\s]+(?:lane|underpass|tunnel))', 'location'),
        ]
        
        locations = []
        for pattern, loc_type in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                locations.append({
                    'text': match.strip(),
                    'type': loc_type
                })
        
        # Also extract any proper nouns that might be locations
        proper_nouns = re.findall(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b', text)
        for pn in proper_nouns:
            # Avoid duplicates and common non-locations
            if (pn not in [l['text'] for l in locations] and 
                len(pn) > 3 and
                not any(word in pn.lower() for word in ['caused', 'resulted', 'due', 'because'])):
                locations.append({
                    'text': pn,
                    'type': 'proper_noun'
                })
        
        return locations
    
    def _get_scenario_locations(self, scenario):
        """Extract all location info from scenario with flexible access"""
        locations = []
        
        # Try different possible field names
        possible_location_fields = ['Location', 'location', 'road', 'Road']
        
        # Check direct location field
        for field in possible_location_fields:
            if field in scenario and scenario[field]:
                locations.append({
                    'name': str(scenario[field]),
                    'type': 'primary',
                    'source': 'direct_field'
                })
                break
        
        # Check description for location clues
        if 'description' in scenario:
            desc = scenario['description']
            # Look for road names in description
            road_pattern = r'([A-Za-z0-9\s]+(?:Road|Street|Highway|E\d+|SZR|Corniche))'
            roads = re.findall(road_pattern, desc)
            for road in roads:
                if road not in [l['name'] for l in locations]:
                    locations.append({
                        'name': road.strip(),
                        'type': 'from_description',
                        'source': 'description'
                    })
        
        # Check context if available
        if 'context' in scenario and isinstance(scenario['context'], dict):
            if 'locations' in scenario['context']:
                for loc in scenario['context']['locations']:
                    if isinstance(loc, dict) and 'name' in loc:
                        locations.append({
                            'name': loc['name'],
                            'type': loc.get('type', 'unknown'),
                            'source': 'context'
                        })
            if 'road_network' in scenario['context']:
                road = scenario['context']['road_network']
                if 'segment_id' in road:
                    locations.append({
                        'name': road['segment_id'],
                        'type': 'road_segment',
                        'source': 'road_network'
                    })
        
        return locations
    
    def _check_location_plausibility(self, mentioned_loc, scenario_locations, scenario):
        """Check if mentioned location is plausible given scenario"""
        mentioned_text = mentioned_loc['text'].lower()
        
        # Clean up mentioned text
        mentioned_text = re.sub(r'[^\w\s]', '', mentioned_text)
        
        # Check against known scenario locations
        for sc_loc in scenario_locations:
            sc_name = sc_loc['name'].lower()
            sc_name = re.sub(r'[^\w\s]', '', sc_name)
            
            # Exact match
            if mentioned_text == sc_name:
                return True, f"Exact match: {sc_loc['name']}"
            
            # One contains the other
            if mentioned_text in sc_name or sc_name in mentioned_text:
                # Check length to avoid false positives
                if len(mentioned_text) > 3 or len(sc_name) > 3:
                    return True, f"Partial match: {mentioned_loc['text']} ↔ {sc_loc['name']}"
            
            # Check for key road identifiers
            road_ids = ['e95', 'e311', 'e10', 'e11', 'szr']
            for road_id in road_ids:
                if road_id in mentioned_text and road_id in sc_name:
                    return True, f"Road ID match: {road_id}"
        
        # Check against description
        if 'description' in scenario:
            desc = scenario['description'].lower()
            if mentioned_text in desc:
                return True, f"Mentioned in description"
        
        # If it's a common road type, assume plausible
        common_terms = ['road', 'street', 'highway', 'lane', 'intersection', 'exit', 'bridge']
        if any(term in mentioned_text for term in common_terms):
            return True, f"Common road term: {mentioned_loc['text']}"
        
        # If we get here, location seems implausible
        return False, f"Location '{mentioned_loc['text']}' not found in scenario"