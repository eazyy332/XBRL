"""
DMP Database Validator
=====================
Validates XBRL facts against the DMP 4.0 database structure.
Focuses on pure database validation without Arelle dependencies.
"""

import logging
from typing import Dict, Any, List, Optional
from dmp_database import dmp_db
from dmp_concept_resolver import concept_resolver

logger = logging.getLogger(__name__)

class DMPValidator:
    """
    Pure DMP database validator that checks XBRL facts against
    the DMP 4.0 database structure and validates data integrity.
    """
    
    def __init__(self):
        self.validation_cache = {}
        logger.info("📊 DMP Validator initialized")
    
    def validate_facts(self, facts: Dict[str, Any], concept_resolutions: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate facts against DMP database structure
        
        Args:
            facts: Parsed XBRL facts dictionary
            concept_resolutions: Results from concept resolution stage (must be dict)
            
        Returns:
            Validation results with detailed analysis
        """
        
        try:
            # FIXED: Ensure concept_resolutions is a dictionary
            if not isinstance(concept_resolutions, dict):
                logger.error(f"❌ Invalid concept_resolutions type: {type(concept_resolutions)}. Expected dict.")
                return {
                    'method': 'pure_dmp_database',
                    'status': 'error',
                    'error': f'Invalid concept_resolutions type: {type(concept_resolutions)}. Expected dict.'
                }
            
            validation_result = {
                'method': 'pure_dmp_database',
                'status': 'completed',
                'timestamp': concept_resolutions.get('timestamp'),
                'total_facts': len(facts),
                'validation_summary': {
                    'valid_facts': 0,
                    'invalid_facts': 0,
                    'warning_facts': 0,
                    'unresolved_facts': 0
                },
                'fact_validations': [],
                'data_quality_issues': [],
                'validation_metrics': {}
            }
            
            # Get resolved concepts for quick lookup
            resolution_details = concept_resolutions.get('resolution_details', [])
            if not isinstance(resolution_details, list):
                logger.warning(f"⚠️ resolution_details is not a list: {type(resolution_details)}")
                resolution_details = []
            
            resolved_concepts = {
                detail['fact_name']: detail 
                for detail in resolution_details
                if isinstance(detail, dict) and detail.get('resolved', False)
            }
            
            # Validate each fact
            for fact_name, fact_data in facts.items():
                fact_validation = self._validate_single_fact(
                    fact_name, fact_data, resolved_concepts.get(fact_name)
                )
                
                validation_result['fact_validations'].append(fact_validation)
                
                # Update counters
                status = fact_validation['validation_status']
                if status == 'valid':
                    validation_result['validation_summary']['valid_facts'] += 1
                elif status == 'invalid':
                    validation_result['validation_summary']['invalid_facts'] += 1
                elif status == 'warning':
                    validation_result['validation_summary']['warning_facts'] += 1
                else:  # unresolved
                    validation_result['validation_summary']['unresolved_facts'] += 1
                
                # Collect data quality issues
                if fact_validation.get('issues'):
                    validation_result['data_quality_issues'].extend(fact_validation['issues'])
            
            # Calculate validation metrics
            self._calculate_validation_metrics(validation_result)
            
            # Add DMP-specific insights
            self._add_dmp_insights(validation_result, resolved_concepts)
            
            logger.info(f"✅ DMP validation completed - {validation_result['validation_summary']['valid_facts']}/{validation_result['total_facts']} facts valid")
            return validation_result
            
        except Exception as e:
            logger.error(f"❌ DMP validation failed: {e}")
            return {
                'method': 'pure_dmp_database',
                'status': 'error',
                'error': str(e)
            }
    
    def _validate_single_fact(self, fact_name: str, fact_data: Dict[str, Any], 
                            concept_resolution: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate a single fact against DMP database"""
        
        fact_validation = {
            'fact_name': fact_name,
            'value': fact_data.get('value'),
            'context': fact_data.get('context'),
            'unit': fact_data.get('unit'),
            'issues': []
        }
        
        # Check if concept was resolved
        if not concept_resolution:
            fact_validation['validation_status'] = 'unresolved'
            fact_validation['issues'].append({
                'type': 'concept_not_found',
                'severity': 'error',
                'message': f"Concept {fact_name} not found in DMP database"
            })
            return fact_validation
        
        # Get concept details
        concept_code = concept_resolution.get('concept_code')
        concept_type = concept_resolution.get('concept_type')
        source_table = concept_resolution.get('source_table')
        
        fact_validation['dmp_concept'] = {
            'concept_code': concept_code,
            'concept_type': concept_type,
            'source_table': source_table
        }
        
        # Validate fact value
        value_validation = self._validate_fact_value(fact_data.get('value'), concept_type)
        if value_validation['issues']:
            fact_validation['issues'].extend(value_validation['issues'])
        
        # Validate context requirements
        context_validation = self._validate_context_requirements(fact_data, concept_resolution)
        if context_validation['issues']:
            fact_validation['issues'].extend(context_validation['issues'])
        
        # Validate unit requirements  
        unit_validation = self._validate_unit_requirements(fact_data, concept_resolution)
        if unit_validation['issues']:
            fact_validation['issues'].extend(unit_validation['issues'])
        
        # Determine overall validation status
        error_issues = [issue for issue in fact_validation['issues'] if issue['severity'] == 'error']
        warning_issues = [issue for issue in fact_validation['issues'] if issue['severity'] == 'warning']
        
        if error_issues:
            fact_validation['validation_status'] = 'invalid'
        elif warning_issues:
            fact_validation['validation_status'] = 'warning'
        else:
            fact_validation['validation_status'] = 'valid'
        
        return fact_validation
    
    def _validate_fact_value(self, value: str, concept_type: str) -> Dict[str, Any]:
        """Validate fact value based on concept type"""
        
        validation = {'issues': []}
        
        if not value or value.strip() == '':
            validation['issues'].append({
                'type': 'empty_value',
                'severity': 'error',
                'message': 'Fact value is empty or null'
            })
            return validation
        
        # Basic data type validation based on concept type
        if concept_type in ['Monetary', 'Percentage', 'Number']:
            try:
                float_value = float(value)
                
                # Check for reasonable ranges
                if concept_type == 'Percentage' and (float_value < 0 or float_value > 100):
                    validation['issues'].append({
                        'type': 'value_out_of_range',
                        'severity': 'warning',
                        'message': f'Percentage value {float_value} may be out of expected range (0-100)'
                    })
                
                # Check for negative monetary values where inappropriate
                if concept_type == 'Monetary' and float_value < 0:
                    validation['issues'].append({
                        'type': 'negative_monetary',
                        'severity': 'warning',
                        'message': 'Negative monetary value detected - verify if appropriate'
                    })
                    
            except ValueError:
                validation['issues'].append({
                    'type': 'invalid_numeric_value',
                    'severity': 'error',
                    'message': f'Value "{value}" is not a valid number for {concept_type} concept'
                })
        
        return validation
    
    def _validate_context_requirements(self, fact_data: Dict[str, Any], 
                                     concept_resolution: Dict[str, Any]) -> Dict[str, Any]:
        """Validate context requirements for the fact"""
        
        validation = {'issues': []}
        context_ref = fact_data.get('context')
        
        if not context_ref:
            validation['issues'].append({
                'type': 'missing_context',
                'severity': 'error',
                'message': 'Fact is missing required context reference'
            })
        
        return validation
    
    def _validate_unit_requirements(self, fact_data: Dict[str, Any], 
                                  concept_resolution: Dict[str, Any]) -> Dict[str, Any]:
        """Validate unit requirements for the fact"""
        
        validation = {'issues': []}
        unit_ref = fact_data.get('unit')
        concept_type = concept_resolution.get('concept_type')
        
        # Check unit requirements based on concept type
        if concept_type in ['Monetary', 'Number', 'Percentage']:
            if not unit_ref:
                validation['issues'].append({
                    'type': 'missing_unit',
                    'severity': 'warning',
                    'message': f'{concept_type} concept should have a unit reference'
                })
        
        return validation
    
    def _calculate_validation_metrics(self, validation_result: Dict[str, Any]) -> None:
        """Calculate comprehensive validation metrics"""
        
        summary = validation_result['validation_summary']
        total = validation_result['total_facts']
        
        metrics = {}
        
        if total > 0:
            metrics['validity_rate'] = f"{(summary['valid_facts'] / total) * 100:.1f}%"
            metrics['error_rate'] = f"{(summary['invalid_facts'] / total) * 100:.1f}%"
            metrics['warning_rate'] = f"{(summary['warning_facts'] / total) * 100:.1f}%"
            metrics['resolution_rate'] = f"{((total - summary['unresolved_facts']) / total) * 100:.1f}%"
        else:
            metrics = {key: "0%" for key in ['validity_rate', 'error_rate', 'warning_rate', 'resolution_rate']}
        
        # Issue type distribution
        issue_types = {}
        for fact_val in validation_result['fact_validations']:
            for issue in fact_val.get('issues', []):
                issue_type = issue['type']
                issue_types[issue_type] = issue_types.get(issue_type, 0) + 1
        
        metrics['issue_type_distribution'] = issue_types
        metrics['total_issues'] = len(validation_result['data_quality_issues'])
        
        validation_result['validation_metrics'] = metrics
    
    def _add_dmp_insights(self, validation_result: Dict[str, Any], 
                         resolved_concepts: Dict[str, Any]) -> None:
        """Add DMP-specific insights to validation results"""
        
        insights = {
            'concept_source_distribution': {},
            'concept_type_distribution': {},
            'recommendations': []
        }
        
        # Analyze concept sources
        for concept_detail in resolved_concepts.values():
            source = concept_detail.get('source_table', 'unknown')
            concept_type = concept_detail.get('concept_type', 'unknown')
            
            insights['concept_source_distribution'][source] = insights['concept_source_distribution'].get(source, 0) + 1
            insights['concept_type_distribution'][concept_type] = insights['concept_type_distribution'].get(concept_type, 0) + 1
        
        # Generate recommendations
        error_rate = float(validation_result['validation_metrics']['error_rate'].replace('%', ''))
        warning_rate = float(validation_result['validation_metrics']['warning_rate'].replace('%', ''))
        
        if error_rate > 10:
            insights['recommendations'].append({
                'type': 'data_quality',
                'priority': 'high',
                'message': f'High error rate ({error_rate}%) detected - review fact values and formats'
            })
        
        if warning_rate > 20:
            insights['recommendations'].append({
                'type': 'data_review',
                'priority': 'medium', 
                'message': f'Many warnings ({warning_rate}%) detected - review data completeness'
            })
        
        if 'tMember' in insights['concept_source_distribution']:
            insights['recommendations'].append({
                'type': 'dimensional_data',
                'priority': 'info',
                'message': 'Member concepts detected - ensure dimensional context is properly defined'
            })
        
        validation_result['dmp_insights'] = insights

    def validate_against_dmp_rules(self, facts: Dict[str, Any]) -> Dict[str, Any]:
        """Validate facts against DMP business rules"""
        
        try:
            # This will be implemented by the rule engine
            # For now, return placeholder
            return {
                'method': 'dmp_business_rules',
                'status': 'not_implemented',
                'message': 'DMP business rule validation will be implemented by rule engine'
            }
            
        except Exception as e:
            logger.error(f"DMP rule validation failed: {e}")
            return {
                'method': 'dmp_business_rules',
                'status': 'error',
                'error': str(e)
            }