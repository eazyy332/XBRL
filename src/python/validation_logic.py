import subprocess
import json
import time
import logging
from arelle_runner import ArelleRunner  # FIXED: Use enhanced ArelleRunner instead of arelle_core
from config import FINREP_RULES
from dmp_concept_resolver import concept_resolver
import os
import re

logger = logging.getLogger(__name__)

class ValidationProcessor:
    def __init__(self):
        self.finrep_rules = FINREP_RULES
        self.arelle_runner = ArelleRunner()  # FIXED: Use enhanced ArelleRunner

    def run_arelle_validation(self, instance_path, taxonomy_path):
        """Run standard Arelle validation with taxonomy - DEPRECATED, use EnhancedValidationEngine"""
        logger.warning("DEPRECATED: Use EnhancedValidationEngine.run_comprehensive_validation() instead")
        return self.arelle_runner.validate_with_arelle(instance_path, taxonomy_path)
    
    def run_arelle_validation_minimal(self, instance_path):
        """FIXED: Run Arelle validation with enhanced ArelleRunner (comprehensive error detection)"""
        # Use dummy taxonomy path for compatibility - ArelleRunner will handle properly
        dummy_taxonomy_path = "dummy_taxonomy.zip"
        
        logger.info(f"🔧 ENHANCED VALIDATION: Using ArelleRunner for {os.path.basename(instance_path)}")
        arelle_result = self.arelle_runner.validate_with_arelle(instance_path, dummy_taxonomy_path)
        
        # Convert ArelleRunner result format to subprocess.CompletedProcess format for compatibility
        if arelle_result.get('status') == 'completed':
            # Create mock subprocess result object
            class MockResult:
                def __init__(self, return_code, stdout, stderr):
                    self.returncode = return_code
                    self.stdout = stdout or ""
                    self.stderr = stderr or ""
            
            raw_output = arelle_result.get('raw_output', {})
            return MockResult(
                arelle_result.get('return_code', 1),
                raw_output.get('stdout', ''),
                raw_output.get('stderr', '')
            )
        else:
            # Error case
            error_msg = arelle_result.get('error', 'Unknown validation error')
            class MockResult:
                def __init__(self):
                    self.returncode = 1
                    self.stdout = ""
                    self.stderr = f"[ERROR] ArelleRunner: {error_msg}"
            return MockResult()

    def analyze_xbrl_dmp_version_compatibility(self, xbrl_file_path):
        """
        NIEUW: Analyseer of XBRL file compatible is met DPM 4.0
        """
        try:
            with open(xbrl_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Zoek naar versie indicatoren
            version_indicators = {
                'eba_met_3.0': content.count('eba_met_3.0:'),
                'eba_met_3.4': content.count('eba_met_3.4:'),
                'eba_met_4.0': content.count('eba_met:') - content.count('eba_met_3'),
                'eba_met_generic': content.count('eba_met:')
            }
            
            # Zoek naar namespace declaraties
            namespaces = {
                'dpm_3.0': 'http://www.eba.europa.eu/xbrl/crr/dict/met/2015-03-31' in content,
                'dmp_3.4': 'http://www.eba.europa.eu/xbrl/crr/dict/met/2019-' in content,
                'dpm_4.0': 'http://www.eba.europa.eu/xbrl/crr/dict/met/2024-' in content or 'http://www.eba.europa.eu/xbrl/crr/dict/met/2023-' in content
            }
            
            # Analyseer bestandsnaam voor versie hints
            filename = os.path.basename(xbrl_file_path)
            filename_analysis = {
                'creation_date': '2020' in filename,  # Old sample if 2020
                'template_version': 'FINREP020400' in filename,  # Version 2.4.0
                'likely_dmp_version': '3.4' if '2020' in filename else '4.0'
            }
            
            # Bepaal meest waarschijnlijke DPM versie
            if version_indicators['eba_met_3.4'] > 10:
                detected_version = '3.4'
            elif version_indicators['eba_met_3.0'] > 10:
                detected_version = '3.0'
            elif '2020' in filename or '2019' in filename:
                detected_version = '3.4'  # Oude samples
            else:
                detected_version = '4.0'
            
            compatibility_analysis = {
                'detected_dmp_version': detected_version,
                'target_dmp_version': '4.0',
                'version_mismatch': detected_version != '4.0',
                'version_indicators': version_indicators,
                'namespaces': namespaces,
                'filename_analysis': filename_analysis,
                'compatibility_score': self._calculate_compatibility_score(version_indicators, namespaces)
            }
            
            logger.info(f"🔍 DPM VERSION ANALYSIS:")
            logger.info(f"   📊 Detected Version: DPM {detected_version}")
            logger.info(f"   📊 Target Version: DPM 4.0") 
            logger.info(f"   📊 Version Mismatch: {compatibility_analysis['version_mismatch']}")
            logger.info(f"   📊 Compatibility Score: {compatibility_analysis['compatibility_score']}/100")
            
            return compatibility_analysis
            
        except Exception as e:
            logger.error(f"DPM version analysis failed: {e}")
            return None

    def _calculate_compatibility_score(self, version_indicators, namespaces):
        """
        Bereken compatibility score (0-100)
        """
        score = 100
        
        # Penalty voor oude versie indicators
        if version_indicators['eba_met_3.4'] > 10:
            score -= 30
        if version_indicators['eba_met_3.0'] > 10:
            score -= 40
        
        # Penalty voor oude namespaces
        if namespaces.get('dpm_3.0'):
            score -= 40
        if namespaces.get('dmp_3.4'):
            score -= 30
            
        # Bonus voor 4.0 indicators
        if version_indicators['eba_met_4.0'] > 20:
            score += 20
        if namespaces.get('dmp_4.0'):
            score += 20
        
        return max(0, min(100, score))

    def suggest_compatibility_fixes(self, compatibility_analysis):
        """
        NIEUW: Suggereer fixes voor version compatibility
        """
        suggestions = []
        
        if compatibility_analysis['version_mismatch']:
            suggestions.append({
                'type': 'VERSION_MISMATCH',
                'severity': 'HIGH',
                'description': f"XBRL file appears to be DPM {compatibility_analysis['detected_dmp_version']} format but validating against DPM 4.0",
                'solution': 'Use DPM 4.0 compatible XBRL sample or enable backwards compatibility mode'
            })
        
        if compatibility_analysis['compatibility_score'] < 50:
            suggestions.append({
                'type': 'LOW_COMPATIBILITY',
                'severity': 'HIGH', 
                'description': f"Low compatibility score: {compatibility_analysis['compatibility_score']}/100",
                'solution': 'Consider using a DPM 4.0 native XBRL sample file'
            })
        
        if compatibility_analysis['filename_analysis']['creation_date']:
            suggestions.append({
                'type': 'OLD_SAMPLE',
                'severity': 'MEDIUM',
                'description': 'XBRL file appears to be from 2020 (pre-DPM 4.0)',
                'solution': 'Use more recent XBRL sample file or apply concept mapping'
            })
        
        return suggestions

    def process_arelle_output(self, arelle_result, enhanced_mode=False):
        """ENHANCED: Process Arelle output met DMP concept resolution inclusief Member table"""
        try:
            # Combine all output for comprehensive analysis
            full_output = (arelle_result.stdout or "") + "\n" + (arelle_result.stderr or "")
            output_lines = full_output.split('\n')
            
            logger.info(f"🔍 PROCESSING ARELLE OUTPUT WITH ENHANCED DMP CONCEPT RESOLUTION")
            logger.info(f"Processing {len(output_lines)} lines of output")
            logger.info(f"Total output length: {len(full_output)} characters")
            logger.info(f"Arelle return code: {arelle_result.returncode}")
            
            # Initialize collections
            errors = []
            dmp_results = []
            
            # ENHANCED: Extract missing concepts with DMP resolution
            missing_concepts = self._extract_missing_concepts_enhanced(full_output)
            logger.info(f"📊 Missing concepts detected: {len(missing_concepts)}")
            
            # ENHANCED: Resolve concepts tegen DMP database inclusief Member table
            resolved_concepts = {}
            unresolved_concepts = []
            member_resolved_concepts = {}
            
            for concept in missing_concepts:
                dmp_concept = concept_resolver.resolve_concept_from_dmp(concept)
                if dmp_concept:
                    resolved_concepts[concept] = dmp_concept
                    if dmp_concept.get('source') == 'tMember':
                        member_resolved_concepts[concept] = dmp_concept
                        logger.info(f"🎯 MEMBER RESOLVED: {concept} -> {dmp_concept['ConceptCode']} (XBRL: {dmp_concept.get('MemberXbrlCode', 'N/A')})")
                    else:
                        logger.info(f"✅ RESOLVED: {concept} -> {dmp_concept['ConceptCode']} (source: {dmp_concept.get('source', 'unknown')})")
                else:
                    unresolved_concepts.append(concept)
                    logger.warning(f"❌ UNRESOLVED: {concept}")
            
            logger.info(f"🎯 ENHANCED CONCEPT RESOLUTION RESULTS:")
            logger.info(f"   ✅ Total Resolved: {len(resolved_concepts)}")
            logger.info(f"   🎯 Member Table Resolved: {len(member_resolved_concepts)}")
            logger.info(f"   ❌ Unresolved: {len(unresolved_concepts)}")
            
            # Convert results to DMP format
            issue_id = 1
            
            # Process resolved concepts (now as warnings instead of errors)
            for concept, dmp_concept in resolved_concepts.items():
                severity = 'info' if dmp_concept.get('source') == 'tMember' else 'warning'
                source_info = f"Found in {dmp_concept.get('source', 'unknown')} table"
                
                if dmp_concept.get('source') == 'tMember':
                    xbrl_code = dmp_concept.get('MemberXbrlCode', '')
                    source_info += f" (XBRL Code: {xbrl_code})" if xbrl_code else ""
                
                error_entry = {
                    'message': f'Concept resolved in DMP database: {concept}',
                    'severity': severity,
                    'code': f'CONCEPT-RESOLVED-{issue_id}',
                    'concept': concept,
                    'line': issue_id
                }
                errors.append(error_entry)
                
                dmp_result = {
                    'concept': concept,
                    'rule': f'EBA-RESOLUTION-{issue_id}',
                    'status': 'Resolved',
                    'message': f'Concept {concept} exists in DMP 4.0 database as {dmp_concept["ConceptCode"]}',
                    'annotation': f'{source_info}. Consider updating taxonomy to include this concept.',
                    'ruleType': 'resolution',
                    'severity': severity,
                    'source': dmp_concept.get('source', 'unknown'),
                    'dmpData': dmp_concept
                }
                dmp_results.append(dmp_result)
                issue_id += 1
            
            # Process truly unresolved concepts (still errors)
            for concept in unresolved_concepts:
                error_entry = {
                    'message': f'Missing schema concept definition: {concept}',
                    'severity': 'error',
                    'code': f'MISSING-CONCEPT-{issue_id}',
                    'concept': concept,
                    'line': issue_id
                }
                errors.append(error_entry)
                
                dmp_result = {
                    'concept': concept,
                    'rule': f'EBA-MISSING-{issue_id}',
                    'status': 'Failed',
                    'message': f'Schema concept definition missing for {concept}',
                    'annotation': f'Required EBA concept {concept} not found in loaded taxonomy schemas or DMP 4.0 database (including Member table)',
                    'ruleType': 'schema',
                    'severity': 'error'
                }
                dmp_results.append(dmp_result)
                issue_id += 1
            
            # Extract other error types (unchanged)
            loading_errors = self._extract_loading_errors_fixed(full_output)
            business_errors = self._extract_business_rule_errors_fixed(full_output)
            
            # Calculate totals with enhanced resolution
            total_errors = len([e for e in errors if e.get('severity') == 'error'])
            total_warnings = len([e for e in errors if e.get('severity') == 'warning'])
            total_info = len([e for e in errors if e.get('severity') == 'info'])
            total_failed_rules = len([r for r in dmp_results if r.get('status') == 'Failed'])
            
            # Enhanced validation success criteria
            is_valid = total_errors == 0 and arelle_result.returncode == 0
            
            logger.info(f"🎯 ENHANCED VALIDATION RESULTS WITH MEMBER TABLE SUPPORT:")
            logger.info(f"Total errors: {total_errors}")
            logger.info(f"Total warnings: {total_warnings}")
            logger.info(f"Total info messages: {total_info}")
            logger.info(f"Total DMP results: {len(dmp_results)}")
            logger.info(f"Member table resolutions: {len(member_resolved_concepts)}")
            logger.info(f"Concept resolution rate: {len(resolved_concepts)}/{len(missing_concepts)} ({len(resolved_concepts)*100//max(len(missing_concepts),1)}%)")
            logger.info(f"Document valid: {is_valid}")
            
            # Enhanced stats
            validation_stats = {
                'totalRules': len(dmp_results),
                'passedRules': len([r for r in dmp_results if r.get('status') == 'Passed']),
                'failedRules': len([r for r in dmp_results if r.get('status') == 'Failed']),
                'resolvedRules': len([r for r in dmp_results if r.get('status') == 'Resolved']),
                'warningRules': len([r for r in dmp_results if r.get('status') == 'Warning']),
                'totalErrorsDetected': total_errors,
                'totalWarningsDetected': total_warnings,
                'totalInfoDetected': total_info,
                'conceptResolutionRate': len(resolved_concepts) * 100 // max(len(missing_concepts), 1),
                'resolvedConcepts': len(resolved_concepts),
                'memberTableResolutions': len(member_resolved_concepts),
                'unresolvedConcepts': len(unresolved_concepts)
            }
            
            return {
                'isValid': is_valid,
                'status': 'valid' if is_valid else 'invalid',
                'errors': errors,
                'dmpResults': dmp_results,
                'validationStats': validation_stats,
                'conceptResolution': {
                    'resolved': resolved_concepts,
                    'memberResolved': member_resolved_concepts,
                    'unresolved': unresolved_concepts,
                    'resolutionRate': validation_stats['conceptResolutionRate']
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error processing validation results: {str(e)}")
            return {
                'isValid': False,
                'status': 'invalid',
                'errors': [{
                    'message': f'Processing error: {str(e)}',
                    'severity': 'error',
                    'code': 'PROCESSING-ERROR'
                }],
                'dmpResults': [{
                    'concept': 'ProcessingError',
                    'rule': 'OUTPUT-PROCESSING',
                    'status': 'Failed',
                    'message': f'Failed to process validation results: {str(e)}',
                    'annotation': 'System error during validation processing',
                    'ruleType': 'system',
                    'severity': 'error'
                }],
                'validationStats': {
                    'totalRules': 1,
                    'passedRules': 0,
                    'failedRules': 1,
                    'totalErrorsDetected': 1
                }
            }
    
    def _extract_missing_concepts_enhanced(self, output):
        """ENHANCED: Extract missing concepts with better pattern matching"""
        missing_concepts = []
        
        # Enhanced pattern matching for missing concepts
        patterns = [
            r'Instance facts missing schema concept definition:\s*([^\n]+)',
            r'facts missing schema concept definition:\s*([^\n]+)',
            r'missing schema concept:\s*([^\n]+)',
            r'concept definition not found:\s*([^\n]+)',
            r'undefined concept:\s*([^\n]+)',
            r'No concept definition for:\s*([^\n]+)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, output, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                # Split by comma and clean concept names
                concepts = [c.strip() for c in match.split(',') if c.strip()]
                for concept in concepts:
                    # Clean up concept name
                    concept = concept.strip().strip('"\'').strip()
                    if concept and len(concept) > 2:
                        missing_concepts.append(concept)
        
        # Extract EBA specific concept patterns
        eba_patterns = [
            r'\b(eba_met[^:\s]*:[A-Za-z][A-Za-z0-9_]*)\b',
            r'\b(find:[A-Za-z][A-Za-z0-9_]*)\b'
        ]
        
        for pattern in eba_patterns:
            matches = re.findall(pattern, output, re.IGNORECASE)
            for match in matches:
                if match not in missing_concepts and len(match) > 5:
                    missing_concepts.append(match)
        
        # Remove duplicates and return
        unique_concepts = list(set(missing_concepts))
        logger.info(f"Extracted {len(unique_concepts)} unique missing concepts")
        return unique_concepts
    
    def _extract_loading_errors_fixed(self, output):
        """FIXED: Extract file loading errors"""
        errors = []
        patterns = [
            r'File can not be loaded:\s*([^\n]+)',
            r'Cannot load file:\s*([^\n]+)',
            r'Failed to load:\s*([^\n]+)',
            r'Unable to retrieve:\s*([^\n]+)',
            r'Error loading:\s*([^\n]+)',
            r'File not found:\s*([^\n]+)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, output, re.IGNORECASE)
            for match in matches:
                cleaned_error = match.strip()
                if cleaned_error and cleaned_error not in errors:
                    errors.append(cleaned_error)
        
        return errors
    
    def _extract_business_rule_errors_fixed(self, output):
        """FIXED: Extract EBA business rule validation errors"""
        errors = []
        patterns = [
            r'assertion.*failed:\s*([^\n]+)',
            r'business rule.*violated:\s*([^\n]+)',
            r'rule.*not satisfied:\s*([^\n]+)',
            r'validation rule.*failed:\s*([^\n]+)',
            r'formula.*false:\s*([^\n]+)',
            r'calculation.*inconsistent:\s*([^\n]+)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, output, re.IGNORECASE)
            for match in matches:
                cleaned_error = match.strip()
                if cleaned_error and cleaned_error not in errors:
                    errors.append(cleaned_error)
        
        return errors
    
    def _extract_concept_from_line(self, line):
        """Extract concept name from error line"""
        if not line:
            return None
            
        # Enhanced patterns for EBA concepts
        patterns = [
            r"'([^']+)'",  # Single quotes
            r'"([^"]+)"',  # Double quotes
            r'\b(eba_met[^:\s]*:[A-Za-z0-9_]+)\b',  # EBA concepts
            r'\b(find:[A-Za-z0-9_]+)\b',  # FIND concepts
            r'\b([A-Za-z][A-Za-z0-9_]*:[A-Za-z][A-Za-z0-9_]+)\b',  # Namespace:concept
            r'\b([A-Za-z][A-Za-z0-9_]{5,})\b'  # Long identifiers
        ]
        
        exclude_words = {
            'error', 'warning', 'info', 'missing', 'failed', 'validation',
            'schema', 'definition', 'concept', 'rule', 'assertion'
        }
        
        for pattern in patterns:
            matches = re.findall(pattern, line, re.IGNORECASE)
            for match in matches:
                if len(match) > 3 and match.lower() not in exclude_words:
                    return match
        
        return None
