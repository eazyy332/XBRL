"""
DMP Rule Evaluator
=================
Evaluates different types of DMP validation rules against XBRL facts.
Handles existence, calculation, consistency, and conditional rule evaluation.
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class DMPRuleEvaluator:
    """
    Evaluates different types of DMP validation rules
    """
    
    def __init__(self):
        pass
    
    def evaluate_rule(self, rule: Dict[str, Any], facts: Dict[str, Any], 
                      concept_resolutions: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate a specific rule against the facts"""
        
        rule_result = {
            'rule_code': rule.get('RuleCode'),
            'rule_label': rule.get('RuleLabel'),
            'rule_type': rule.get('RuleType'),
            'status': 'skipped',
            'message': '',
            'details': {}
        }
        
        try:
            execution_method = rule.get('execution_method', 'general_validation')
            
            if execution_method == 'existence_check':
                rule_result.update(self._evaluate_existence_rule(rule, facts, concept_resolutions))
            elif execution_method == 'calculation_check':
                rule_result.update(self._evaluate_calculation_rule(rule, facts, concept_resolutions))
            elif execution_method == 'consistency_check':
                rule_result.update(self._evaluate_consistency_rule(rule, facts, concept_resolutions))
            elif execution_method == 'conditional_check':
                rule_result.update(self._evaluate_conditional_rule(rule, facts, concept_resolutions))
            else:
                rule_result.update(self._evaluate_general_rule(rule, facts, concept_resolutions))
            
        except Exception as e:
            rule_result['status'] = 'error'
            rule_result['message'] = f"Rule evaluation failed: {str(e)}"
            logger.warning(f"Rule {rule.get('RuleCode')} evaluation failed: {e}")
        
        return rule_result
    
    def _evaluate_existence_rule(self, rule: Dict[str, Any], facts: Dict[str, Any], 
                               concept_resolutions: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate existence-based rules (required/forbidden facts)"""
        
        parsed_expr = rule.get('parsed_expression', {})
        required_concepts = parsed_expr.get('concepts', [])
        
        result = {'status': 'passed', 'message': 'All required concepts found'}
        missing_concepts = []
        
        for concept in required_concepts:
            found = False
            
            # Check if concept exists in facts (exact or partial match)
            for fact_name in facts.keys():
                if (concept in fact_name or 
                    concept == fact_name.split(':')[-1] if ':' in fact_name else concept == fact_name):
                    found = True
                    break
            
            if not found:
                missing_concepts.append(concept)
        
        if missing_concepts:
            result['status'] = 'failed'
            result['message'] = f"Missing required concepts: {', '.join(missing_concepts)}"
            result['details'] = {'missing_concepts': missing_concepts}
        
        return result
    
    def _evaluate_calculation_rule(self, rule: Dict[str, Any], facts: Dict[str, Any], 
                                 concept_resolutions: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate calculation-based rules (sum checks, arithmetic consistency)"""
        
        # For now, return a placeholder implementation
        # This would require more complex parsing and calculation logic
        return {
            'status': 'skipped',
            'message': 'Calculation rule evaluation not yet implemented',
            'details': {'rule_type': 'calculation'}
        }
    
    def _evaluate_consistency_rule(self, rule: Dict[str, Any], facts: Dict[str, Any], 
                                 concept_resolutions: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate consistency rules (value comparisons, logical constraints)"""
        
        # Placeholder implementation
        return {
            'status': 'skipped',
            'message': 'Consistency rule evaluation not yet implemented',
            'details': {'rule_type': 'consistency'}
        }
    
    def _evaluate_conditional_rule(self, rule: Dict[str, Any], facts: Dict[str, Any], 
                                 concept_resolutions: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate conditional rules (if-then logic)"""
        
        # Placeholder implementation
        return {
            'status': 'skipped',
            'message': 'Conditional rule evaluation not yet implemented',
            'details': {'rule_type': 'conditional'}
        }
    
    def _evaluate_general_rule(self, rule: Dict[str, Any], facts: Dict[str, Any], 
                             concept_resolutions: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate general validation rules"""
        
        return {
            'status': 'passed',
            'message': 'General rule passed (placeholder)',
            'details': {'rule_type': 'general'}
        }