"""
DMP Rule Parser
==============
Parses and processes DMP validation rule expressions.
Extracts concepts, conditions, calculations from rule expressions.
"""

import logging
import re
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class DMPRuleParser:
    """
    Parses DMP validation rule expressions and extracts validation logic
    """
    
    def __init__(self):
        pass
    
    def process_rule(self, rule_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Process and prepare a validation rule for execution"""
        
        processed_rule = rule_dict.copy()
        
        # Parse rule expression
        expression = rule_dict.get('Expression', '')
        if expression:
            processed_rule['parsed_expression'] = self._parse_rule_expression(expression)
        
        # Determine rule execution method
        rule_type = rule_dict.get('RuleType', '').lower()
        processed_rule['execution_method'] = self._determine_execution_method(rule_type, expression)
        
        # Set default severity if missing
        if not processed_rule.get('ErrorSeverity'):
            processed_rule['ErrorSeverity'] = 'ERROR'
        
        return processed_rule
    
    def _parse_rule_expression(self, expression: str) -> Dict[str, Any]:
        """Parse rule expression to extract validation logic"""
        
        parsed = {
            'original': expression,
            'type': 'unknown',
            'concepts': [],
            'conditions': [],
            'calculations': []
        }
        
        # Common DMP rule patterns
        if 'sum(' in expression.lower():
            parsed['type'] = 'calculation'
            parsed['calculations'] = self._extract_calculations(expression)
        elif 'exists(' in expression.lower() or 'not exists(' in expression.lower():
            parsed['type'] = 'existence'
            parsed['concepts'] = self._extract_concept_references(expression)
        elif any(op in expression for op in ['=', '>', '<', '>=', '<=', '!=']):
            parsed['type'] = 'comparison'
            parsed['conditions'] = self._extract_conditions(expression)
        elif 'if' in expression.lower() or 'when' in expression.lower():
            parsed['type'] = 'conditional'
            parsed['conditions'] = self._extract_conditions(expression)
        
        # Extract all concept references
        all_concepts = self._extract_concept_references(expression)
        parsed['concepts'].extend(all_concepts)
        parsed['concepts'] = list(set(parsed['concepts']))  # Remove duplicates
        
        return parsed
    
    def _extract_concept_references(self, expression: str) -> List[str]:
        """Extract concept references from rule expression"""
        
        # Common patterns for concept references in DMP rules
        patterns = [
            r'([a-zA-Z_][a-zA-Z0-9_]*:[a-zA-Z_][a-zA-Z0-9_]*)',  # namespace:concept
            r'\b([a-zA-Z_][a-zA-Z0-9_]{3,})\b',  # concept codes (4+ chars)
            r'{([^}]+)}',  # concepts in braces
            r'\[([^\]]+)\]'  # concepts in brackets
        ]
        
        concepts = []
        for pattern in patterns:
            matches = re.findall(pattern, expression)
            concepts.extend(matches)
        
        # Filter out common keywords and short strings
        filtered_concepts = []
        skip_words = {'and', 'or', 'not', 'if', 'then', 'else', 'sum', 'exists', 'null', 'true', 'false'}
        
        for concept in concepts:
            if (len(concept) >= 3 and 
                concept.lower() not in skip_words and
                not concept.isdigit()):
                filtered_concepts.append(concept)
        
        return list(set(filtered_concepts))
    
    def _extract_calculations(self, expression: str) -> List[Dict[str, Any]]:
        """Extract calculation expressions from rule"""
        
        calculations = []
        
        # Look for sum() expressions
        sum_pattern = r'sum\(([^)]+)\)'
        sum_matches = re.findall(sum_pattern, expression, re.IGNORECASE)
        
        for match in sum_matches:
            calc = {
                'type': 'sum',
                'expression': match,
                'concepts': self._extract_concept_references(match)
            }
            calculations.append(calc)
        
        return calculations
    
    def _extract_conditions(self, expression: str) -> List[Dict[str, Any]]:
        """Extract conditional expressions from rule"""
        
        conditions = []
        
        # Simple condition patterns
        condition_patterns = [
            r'([^<>=!]+)\s*(>=|<=|>|<|=|!=)\s*([^<>=!]+)',
            r'if\s+(.+?)\s+then',
            r'when\s+(.+?)\s+then'
        ]
        
        for pattern in condition_patterns:
            matches = re.findall(pattern, expression, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple) and len(match) >= 2:
                    condition = {
                        'left': match[0].strip(),
                        'operator': match[1].strip() if len(match) > 2 else '=',
                        'right': match[2].strip() if len(match) > 2 else match[1].strip()
                    }
                    conditions.append(condition)
        
        return conditions
    
    def _determine_execution_method(self, rule_type: str, expression: str) -> str:
        """Determine how to execute the rule based on type and expression"""
        
        if 'calculation' in rule_type or 'sum(' in expression.lower():
            return 'calculation_check'
        elif 'existence' in rule_type or 'exists(' in expression.lower():
            return 'existence_check'
        elif 'consistency' in rule_type or any(op in expression for op in ['=', '>', '<']):
            return 'consistency_check'
        elif 'conditional' in rule_type or 'if' in expression.lower():
            return 'conditional_check'
        else:
            return 'general_validation'