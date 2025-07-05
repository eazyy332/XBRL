"""
DMP Rule Engine
==============
Main coordinator for DMP rule validation.
Orchestrates rule loading, parsing, and evaluation.
"""

import logging
from typing import Dict, Any, List
from datetime import datetime
from rule_loader import DMPRuleLoader
from rule_parser import DMPRuleParser
from rule_evaluator import DMPRuleEvaluator

logger = logging.getLogger(__name__)

class DMPRuleEngine:
    """
    Main DMP business rule validation engine that coordinates
    rule loading, parsing, and evaluation against XBRL facts
    """
    
    def __init__(self, architecture_version=None):
        self.architecture_version = architecture_version
        self.rule_loader = DMPRuleLoader()
        self.rule_parser = DMPRuleParser()
        self.rule_evaluator = DMPRuleEvaluator()
        
        # Switch database based on architecture
        if architecture_version:
            from dmp_database import dmp_db
            dmp_db.switch_database(architecture_version)
        
        # Load and process rules
        self._initialize_rules()
        
        logger.info(f"🔧 DMP Rule Engine initialized with {len(self.rules_cache)} rules for {architecture_version or 'default'}")
    
    def _initialize_rules(self) -> None:
        """Initialize rules by loading and processing them"""
        # Load raw rules from database
        load_result = self.rule_loader.load_validation_rules()
        
        if not load_result:
            self.rules_cache = {}
            self.rule_categories = {}
            return
        
        raw_rules_cache = load_result.get('rules_cache', {})
        self.rule_categories = load_result.get('rule_categories', {})
        
        # Process rules through parser
        self.rules_cache = {}
        for rule_code, rule_dict in raw_rules_cache.items():
            processed_rule = self.rule_parser.process_rule(rule_dict)
            self.rules_cache[rule_code] = processed_rule
    
    def validate_facts_against_rules(self, facts: Dict[str, Any], 
                                   concept_resolutions: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate facts against all applicable DMP rules
        
        Args:
            facts: Parsed XBRL facts
            concept_resolutions: Results from concept resolution
            
        Returns:
            Rule validation results
        """
        
        try:
            validation_result = {
                'method': 'dmp_rule_validation',
                'status': 'completed',
                'timestamp': datetime.now().isoformat(),
                'total_rules_evaluated': 0,
                'rules_passed': 0,
                'rules_failed': 0,
                'rules_skipped': 0,
                'rule_results': [],
                'validation_summary': {}
            }
            
            # Get applicable rules for the facts
            applicable_rules = self._find_applicable_rules(facts, concept_resolutions)
            
            logger.info(f"🔍 Evaluating {len(applicable_rules)} applicable rules...")
            
            # Evaluate each applicable rule
            for rule_code in applicable_rules:
                rule = self.rules_cache[rule_code]
                rule_result = self.rule_evaluator.evaluate_rule(rule, facts, concept_resolutions)
                
                validation_result['rule_results'].append(rule_result)
                validation_result['total_rules_evaluated'] += 1
                
                # Update counters
                if rule_result['status'] == 'passed':
                    validation_result['rules_passed'] += 1
                elif rule_result['status'] == 'failed':
                    validation_result['rules_failed'] += 1
                else:
                    validation_result['rules_skipped'] += 1
            
            # Generate summary
            validation_result['validation_summary'] = self._generate_rule_summary(validation_result)
            
            logger.info(f"✅ Rule validation completed - {validation_result['rules_passed']}/{validation_result['total_rules_evaluated']} rules passed")
            return validation_result
            
        except Exception as e:
            logger.error(f"❌ Rule validation failed: {e}")
            return {
                'method': 'dmp_rule_validation',
                'status': 'error',
                'error': str(e)
            }
    
    def _find_applicable_rules(self, facts: Dict[str, Any], 
                             concept_resolutions: Dict[str, Any]) -> List[str]:
        """Find rules that are applicable to the given facts"""
        
        applicable_rules = []
        
        # Get all concept codes from resolved facts
        resolved_concepts = set()
        for detail in concept_resolutions.get('resolution_details', []):
            if detail.get('resolved'):
                concept_code = detail.get('concept_code')
                if concept_code:
                    resolved_concepts.add(concept_code)
        
        # Get all fact names (including prefixed versions)
        fact_names = set(facts.keys())
        for fact_name in facts.keys():
            if ':' in fact_name:
                local_name = fact_name.split(':')[-1]
                fact_names.add(local_name)
        
        # Check each rule for applicability
        for rule_code, rule in self.rules_cache.items():
            if self._is_rule_applicable(rule, resolved_concepts, fact_names):
                applicable_rules.append(rule_code)
        
        return applicable_rules
    
    def _is_rule_applicable(self, rule: Dict[str, Any], resolved_concepts: set, 
                          fact_names: set) -> bool:
        """Check if a rule is applicable to the current fact set"""
        
        parsed_expr = rule.get('parsed_expression', {})
        rule_concepts = parsed_expr.get('concepts', [])
        
        if not rule_concepts:
            # If no specific concepts in rule, consider it generally applicable
            return True
        
        # Check if any rule concepts match resolved concepts or fact names
        for rule_concept in rule_concepts:
            if (rule_concept in resolved_concepts or 
                rule_concept in fact_names or
                any(rule_concept in fact_name for fact_name in fact_names)):
                return True
        
        return False
    
    def _generate_rule_summary(self, validation_result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary of rule validation results"""
        
        total = validation_result['total_rules_evaluated']
        passed = validation_result['rules_passed']
        failed = validation_result['rules_failed']
        skipped = validation_result['rules_skipped']
        
        summary = {
            'total_rules': total,
            'pass_rate': f"{(passed/total)*100:.1f}%" if total > 0 else "0%",
            'fail_rate': f"{(failed/total)*100:.1f}%" if total > 0 else "0%",
            'skip_rate': f"{(skipped/total)*100:.1f}%" if total > 0 else "0%",
            'rules_by_type': {},
            'critical_failures': []
        }
        
        # Analyze by rule type
        for rule_result in validation_result['rule_results']:
            rule_type = rule_result.get('rule_type', 'unknown')
            if rule_type not in summary['rules_by_type']:
                summary['rules_by_type'][rule_type] = {'total': 0, 'passed': 0, 'failed': 0}
            
            summary['rules_by_type'][rule_type]['total'] += 1
            if rule_result['status'] == 'passed':
                summary['rules_by_type'][rule_type]['passed'] += 1
            elif rule_result['status'] == 'failed':
                summary['rules_by_type'][rule_type]['failed'] += 1
        
        # Identify critical failures
        for rule_result in validation_result['rule_results']:
            if rule_result['status'] == 'failed':
                summary['critical_failures'].append({
                    'rule_code': rule_result['rule_code'],
                    'rule_label': rule_result['rule_label'],
                    'message': rule_result['message']
                })
        
        return summary
    
    def get_rule_engine_info(self) -> Dict[str, Any]:
        """Get information about the rule engine status"""
        
        return {
            'status': 'active' if self.rules_cache else 'inactive',
            'total_rules_loaded': len(self.rules_cache),
            'rule_categories': {cat: len(rules) for cat, rules in self.rule_categories.items()},
            'sample_rules': [
                {
                    'rule_code': rule_code,
                    'rule_type': rule_data.get('RuleType'),
                    'execution_method': rule_data.get('execution_method')
                }
                for rule_code, rule_data in list(self.rules_cache.items())[:5]
            ]
        }
    
    def debug_rule(self, rule_code: str, facts: Dict[str, Any]) -> Dict[str, Any]:
        """Debug a specific rule execution"""
        
        if rule_code not in self.rules_cache:
            return {'error': f'Rule {rule_code} not found'}
        
        rule = self.rules_cache[rule_code]
        
        debug_info = {
            'rule_code': rule_code,
            'rule_details': rule,
            'applicable_facts': [],
            'execution_simulation': {}
        }
        
        # Find facts that would be relevant to this rule
        rule_concepts = rule.get('parsed_expression', {}).get('concepts', [])
        for fact_name in facts.keys():
            for concept in rule_concepts:
                if concept in fact_name:
                    debug_info['applicable_facts'].append(fact_name)
                    break
        
        # Simulate rule execution
        try:
            debug_info['execution_simulation'] = {
                'would_execute': len(debug_info['applicable_facts']) > 0,
                'execution_method': rule.get('execution_method'),
                'concepts_required': rule_concepts
            }
        except Exception as e:
            debug_info['execution_simulation'] = {'error': str(e)}
        
        return debug_info