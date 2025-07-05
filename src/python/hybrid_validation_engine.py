"""
Hybrid EBA Validation Engine with Dual Architecture Support
===========================================================
Main orchestrator for hybrid validation combining:
1. Pure DMP database validation (primary) - supports both DPM 3.3 and 4.0
2. Arelle fallback validation (secondary) - with correct taxonomy switching
3. Result synthesis and reporting

This module coordinates different validation strategies and provides
unified interface for hybrid validation with automatic architecture detection.
"""

import logging
import os
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Dict, Any, Optional, List
from dmp_database import dmp_db
from dmp_concept_resolver import concept_resolver

logger = logging.getLogger(__name__)

# Architecture configurations - Updated to use same path resolution as working DMP system
def get_database_path(db_name: str) -> str:
    """Get database path using same logic as working DMP system"""
    import os
    # Try different possible base paths
    possible_paths = [
        r"C:\Users\berbe\Documents\AI\XBRL-validation\DPM",
        r".\DPM",
        r"..\DPM", 
        os.path.join(os.getcwd(), "DPM"),
        os.path.join(os.path.dirname(__file__), "..", "DPM")
    ]
    
    for base_path in possible_paths:
        full_path = os.path.join(base_path, db_name)
        if os.path.exists(full_path):
            logger.info(f"✅ Found database at: {full_path}")
            return full_path
    
    # Return default path if none found
    logger.warning(f"⚠️ Database not found in any expected locations, using default")
    return os.path.join(possible_paths[0], db_name)

ARCHITECTURES = {
    'arch_1_0': {
        'name': 'DPM Architecture 1.0 (DPM 3.3)',
        'dmp_db_path': get_database_path('DPM_Database_3.3.phase3.accdb'),
        'taxonomy_folder': 'FullTaxonomy3.0.1.errata3',
        'namespaces': ['xbrl/crr/dict/dpm/3.0', 'eba.europa.eu/eu/cr/3.0']
    },
    'arch_2_0': {
        'name': 'DPM Architecture 2.0 (DPM 4.0)', 
        'dmp_db_path': get_database_path('DPM_Database_v4_0_20241218.accdb'),
        'taxonomy_folder': 'taxo_package_4.0_errata5',
        'namespaces': ['xbrl/dpm/4.0', 'eba.europa.eu/eu/cr/4.0']
    }
}

def detect_architecture_version(xbrl_path: str) -> str:
    """
    Enhanced DPM architecture detection from XBRL file and filename
    Returns: 'arch_1_0', 'arch_2_0', or 'unknown'
    """
    try:
        import os
        filename = os.path.basename(xbrl_path).lower()
        
        # ENHANCED: Check filename patterns first for quick detection
        arch_1_0_filename_patterns = [
            'finrep020400', 'finrep9indgaap', 'gb_finrep', '_2021-06-30_', '_2020',
            'fulltaxonomy3.0', 'phase2', 'dummylei', '_20201218', 'finrep2.4'
        ]
        
        for pattern in arch_1_0_filename_patterns:
            if pattern in filename:
                logger.info(f"✅ Architecture 1.0 detected via filename pattern: {pattern}")
                return 'arch_1_0'
        
        # Parse XBRL file for namespace detection
        tree = ET.parse(xbrl_path)
        root = tree.getroot()
        
        # Enhanced namespace extraction
        namespaces = {}
        for key, value in root.attrib.items():
            if key.startswith('xmlns:'):
                prefix = key.replace('xmlns:', '')
                namespaces[prefix] = value
            elif key == 'xmlns':
                namespaces['default'] = value
        
        # Also scan first few elements if root has no namespaces
        if not namespaces:
            for element in root.iter():
                for key, value in element.attrib.items():
                    if key.startswith('xmlns:'):
                        prefix = key.replace('xmlns:', '')
                        namespaces[prefix] = value
                    elif key == 'xmlns':
                        namespaces['default'] = value
                if len(namespaces) > 5:
                    break
        
        logger.info(f"🔍 Detected namespaces: {list(namespaces.values())}")
        
        # Enhanced patterns for DPM 3.0/Architecture 1.0 detection
        arch_1_0_patterns = [
            'dpm/3.0', 'eu/cr/3.0', 'finrep/3.0', 'corep/3.0', 'finrep/2.4',
            'gb_finrep', 'finrep020400', 'finrep9indgaap', 'phase2'
        ]
        
        # Enhanced patterns for DPM 4.0/Architecture 2.0 detection  
        arch_2_0_patterns = [
            'dpm/4.0', 'eu/cr/4.0', 'finrep/4.0', 'corep/4.0', 'eba_', 'find_',
            'errata5', 'taxo_package_4.0'
        ]
        
        # Check for architecture 1.0 first (DPM 3.0)
        for namespace in namespaces.values():
            for pattern in arch_1_0_patterns:
                if pattern in namespace.lower():
                    logger.info(f"✅ Architecture 1.0 (DPM 3.0) detected via pattern: {pattern} in {namespace}")
                    return 'arch_1_0'
            # Original check for exact matches
            for arch_ns in ARCHITECTURES['arch_1_0']['namespaces']:
                if arch_ns in namespace:
                    logger.info(f"✅ Architecture 1.0 detected via namespace: {arch_ns}")
                    return 'arch_1_0'
        
        # Check for architecture 2.0 (DPM 4.0)
        for namespace in namespaces.values():
            for pattern in arch_2_0_patterns:
                if pattern in namespace.lower():
                    logger.info(f"✅ Architecture 2.0 (DPM 4.0) detected via pattern: {pattern} in {namespace}")
                    return 'arch_2_0'
            # Original check for exact matches
            for arch_ns in ARCHITECTURES['arch_2_0']['namespaces']:
                if arch_ns in namespace:
                    logger.info(f"✅ Architecture 2.0 detected via namespace: {arch_ns}")
                    return 'arch_2_0'
        
        # ENHANCED: Check prefixes in namespaces for EBA patterns
        for prefix, namespace in namespaces.items():
            if prefix.startswith('eba_') or 'eba' in prefix.lower():
                # EBA prefixes typically indicate newer architecture
                logger.info(f"✅ Architecture 2.0 detected via EBA prefix: {prefix}")
                return 'arch_2_0'
        
        logger.warning(f"⚠️ Unknown architecture - no matching patterns found")
        logger.info(f"📝 Available namespaces: {dict(list(namespaces.items())[:5])}")
        
        # ENHANCED: Filename-based fallback
        if any(pattern in filename for pattern in ['2021', '2020', 'phase2', 'fulltaxonomy3']):
            logger.info(f"🔄 Fallback: Using Architecture 1.0 based on filename indicators")
            return 'arch_1_0'
        else:
            logger.info(f"🔄 Fallback: Using Architecture 2.0 as default")
            return 'arch_2_0'
        
    except Exception as e:
        logger.error(f"❌ Architecture detection failed: {e}")
        return 'unknown'

class HybridValidationEngine:
    """
    Main hybrid validation engine with dual architecture support:
    - Detects DPM architecture version automatically
    - Switches between DMP 3.3 and 4.0 databases dynamically
    - Uses correct taxonomy folder for fallback validation
    - Maintains unified API interface
    """
    
    def __init__(self, architecture_version: str = None, dmp_db_path: str = None):
        self.architecture_version = architecture_version
        self.config = ARCHITECTURES.get(architecture_version) if architecture_version else None
        self.dmp_db_path = dmp_db_path or (self.config['dmp_db_path'] if self.config else None)
        
        self.dmp_available = self._check_dmp_availability()
        self.arelle_available = self._check_arelle_availability()
        
        # Import validation modules
        from dmp_validator import DMPValidator
        from arelle_runner import ArelleRunner
        from fact_parser import XBRLFactParser
        from rule_engine import DMPRuleEngine
        
        self.dmp_validator = DMPValidator() if self.dmp_available else None
        self.arelle_runner = ArelleRunner() if self.arelle_available else None
        self.fact_parser = XBRLFactParser()
        self.rule_engine = DMPRuleEngine() if self.dmp_available else None
        
        arch_name = self.config['name'] if self.config else 'Unknown'
        logger.info(f"🚀 Hybrid engine initialized - Architecture: {arch_name}")
        logger.info(f"   📊 DMP: {self.dmp_available}, Arelle: {self.arelle_available}")
    
    def _check_dmp_availability(self) -> bool:
        """Check if DMP database is available for current architecture"""
        try:
            if not self.dmp_db_path or not os.path.exists(self.dmp_db_path):
                logger.warning(f"⚠️ DMP database not found: {self.dmp_db_path}")
                return False
            
            # Test connection with architecture-specific database
            from dmp_connection import DMPConnection
            connection = DMPConnection(self.dmp_db_path)
            status = connection.test_connection()
            connection.close_connection()
            
            available = status.get('status') == 'connected'
            logger.info(f"{'✅' if available else '❌'} DMP database available: {available}")
            return available
        except Exception as e:
            logger.error(f"DMP availability check failed: {e}")
            return False
    
    def _check_arelle_availability(self) -> bool:
        """Check if Arelle is available - always return True since arelle_runner.py exists"""
        try:
            # FIXED: Check if arelle_runner module exists instead of CLI
            from arelle_runner import ArelleRunner
            logger.info("✅ Arelle validation enabled via arelle_runner.py")
            return True
        except ImportError as e:
            logger.warning(f"⚠️ Arelle runner not available: {e}")
            return False
        except Exception as e:
            logger.warning(f"⚠️ Arelle availability check failed: {e}")
            return False
    
    def validate_hybrid(self, xbrl_path: str, taxonomy_path: Optional[str] = None, 
                       auto_detect_architecture: bool = True) -> Dict[str, Any]:
        """
        Execute hybrid validation strategy with architecture detection:
        1. Auto-detect architecture version (if enabled)
        2. Parse XBRL facts with architecture context
        3. DMP validation using correct database
        4. DMP rule validation 
        5. Arelle fallback with correct taxonomy
        6. Synthesize results with architecture metadata
        """
        
        # Auto-detect architecture if not already set
        detected_architecture = None
        if auto_detect_architecture and not self.architecture_version:
            detected_architecture = detect_architecture_version(xbrl_path)
            logger.info(f"🎯 Auto-detected architecture: {detected_architecture}")
            # Update engine configuration
            self.architecture_version = detected_architecture
            self.config = ARCHITECTURES[detected_architecture]
            self.dmp_db_path = self.config['dmp_db_path']
            
            # Re-initialize components with correct database
            self.dmp_available = self._check_dmp_availability()
            if self.dmp_available:
                # CRITICAL: Switch DMP database connection to correct architecture  
                logger.info(f"🔄 Switching DMP database to: {self.dmp_db_path}")
                dmp_db.switch_database(detected_architecture)  # Use consistent architecture parameter
                
                # Re-initialize components with correct database
                from dmp_validator import DMPValidator
                from rule_engine import DMPRuleEngine
                self.dmp_validator = DMPValidator()
                self.rule_engine = DMPRuleEngine()
                logger.info(f"✅ Re-initialized DMP components for {detected_architecture} using {os.path.basename(self.dmp_db_path)}")
                
                # Initialize taxonomy processor with architecture awareness
                from taxonomy_processor import TaxonomyProcessor
                self.taxonomy_processor = TaxonomyProcessor(architecture_version=detected_architecture)
                logger.info(f"✅ Initialized architecture-aware taxonomy processor")
        
        validation_result = {
            'timestamp': datetime.now().isoformat(),
            'strategy': 'hybrid_dual_architecture',
            'architecture_version': self.architecture_version or detected_architecture or 'unknown',
            'dmp_database': os.path.basename(self.dmp_db_path) if self.dmp_db_path else None,
            'taxonomy_used': self.config['taxonomy_folder'] if self.config else None,
            'file_info': {
                'xbrl_file': os.path.basename(xbrl_path),
                'taxonomy_file': os.path.basename(taxonomy_path) if taxonomy_path else None
            },
            'stages': {}
        }
        
        try:
            # STAGE 1: Parse XBRL Facts
            logger.info("📄 Stage 1: Parsing XBRL facts...")
            parsed_data = self.fact_parser.parse_xbrl_instance(xbrl_path)
            
            # FIXED: Extract facts from parsed data structure correctly
            if isinstance(parsed_data, dict):
                facts = parsed_data.get('facts', {})
                parsing_stats = parsed_data.get('parsing_statistics', {})
                logger.info(f"📊 Extracted {len(facts)} facts from parsing data structure")
                logger.info(f"📈 Parsing stats: {parsing_stats}")
            else:
                facts = parsed_data if parsed_data else {}
                logger.warning(f"⚠️ Unexpected parsing data type: {type(parsed_data)}")
            
            validation_result['stages']['fact_parsing'] = {
                'status': 'completed',
                'total_facts': len(facts),
                'parsed_data_type': str(type(parsed_data)),
                'fact_count_by_namespace': self._count_facts_by_namespace(facts)
            }
            
            # STAGE 2: DMP Concept Resolution
            if self.dmp_available:
                logger.info("🔍 Stage 2: DMP concept resolution...")
                dmp_resolution = self._resolve_concepts_in_dmp(facts)
                validation_result['stages']['dmp_concept_resolution'] = dmp_resolution
                
                # STAGE 3: DMP Rule Validation
                logger.info("📏 Stage 3: DMP rule validation...")
                # FIXED: Ensure resolved concepts are passed to rule engine properly
                if isinstance(dmp_resolution, dict) and dmp_resolution.get('resolution_details'):
                    rule_validation = self.rule_engine.validate_facts_against_rules(facts, dmp_resolution)
                    validation_result['stages']['dmp_rule_validation'] = rule_validation
                else:
                    logger.warning("⚠️ No resolved concepts available for rule validation")
                    validation_result['stages']['dmp_rule_validation'] = {
                        'status': 'skipped',
                        'reason': 'no_resolved_concepts',
                        'applicable_rules': 0
                    }
                
                # STAGE 4: DMP Database Validation
                logger.info("💾 Stage 4: DMP database validation...")
                # FIXED: Handle both dict and list types for dmp_resolution
                try:
                    if isinstance(dmp_resolution, dict):
                        dmp_validation = self.dmp_validator.validate_facts(facts, dmp_resolution)
                        validation_result['stages']['dmp_validation'] = dmp_validation
                    elif isinstance(dmp_resolution, list):
                        # Convert list to dict format expected by validator
                        converted_resolution = {
                            'status': 'completed',
                            'resolution_details': dmp_resolution,
                            'resolved_facts': len([r for r in dmp_resolution if r.get('resolved', False)])
                        }
                        dmp_validation = self.dmp_validator.validate_facts(facts, converted_resolution)
                        validation_result['stages']['dmp_validation'] = dmp_validation
                    else:
                        logger.error(f"❌ Invalid dmp_resolution type for DMP validation: {type(dmp_resolution)}")
                        validation_result['stages']['dmp_validation'] = {
                            'status': 'error',
                            'error': f'Invalid dmp_resolution type: {type(dmp_resolution)}'
                        }
                except Exception as e:
                    logger.error(f"❌ DMP validation failed: {e}")
                    validation_result['stages']['dmp_validation'] = {
                        'status': 'error',
                        'error': str(e)
                    }
            else:
                logger.warning("⚠️ DMP database not available - skipping DMP stages")
                validation_result['stages']['dmp_concept_resolution'] = {'status': 'skipped', 'reason': 'dmp_unavailable'}
                validation_result['stages']['dmp_rule_validation'] = {'status': 'skipped', 'reason': 'dmp_unavailable'}
                validation_result['stages']['dmp_validation'] = {'status': 'skipped', 'reason': 'dmp_unavailable'}
            
            # STAGE 5: Architecture-Aware Taxonomy Processing (if taxonomy provided)
            if taxonomy_path and hasattr(self, 'taxonomy_processor'):
                logger.info("📋 Stage 5: Architecture-aware taxonomy processing...")
                try:
                    schemas, packages, extraction_dir = self.taxonomy_processor.process_taxonomy_file(
                        taxonomy_path, architecture_version=self.architecture_version
                    )
                    validation_result['stages']['taxonomy_processing'] = {
                        'status': 'completed',
                        'schemas_found': len(schemas),
                        'packages_found': len(packages),
                        'extraction_dir': extraction_dir,
                        'architecture': self.architecture_version
                    }
                except Exception as e:
                    logger.error(f"❌ Taxonomy processing failed: {e}")
                    validation_result['stages']['taxonomy_processing'] = {
                        'status': 'error',
                        'error': str(e)
                    }
            else:
                validation_result['stages']['taxonomy_processing'] = {
                    'status': 'skipped', 
                    'reason': 'no_taxonomy_or_processor'
                }

            # STAGE 6: Enhanced Arelle Validation (primary validation, not fallback)
            arelle_results = None
            if self.arelle_available:
                logger.info("🔄 Stage 6: Arelle business rule validation...")
                try:
                    # Use extracted taxonomy path if available, otherwise use provided taxonomy
                    arelle_taxonomy_path = taxonomy_path
                    if hasattr(self, 'taxonomy_processor') and 'taxonomy_processing' in validation_result['stages']:
                        extraction_dir = validation_result['stages']['taxonomy_processing'].get('extraction_dir')
                        if extraction_dir:
                            arelle_taxonomy_path = extraction_dir
                            logger.info(f"🎯 Using extracted taxonomy for Arelle: {extraction_dir}")
                    
                    arelle_results = self.arelle_runner.validate_with_arelle(xbrl_path, arelle_taxonomy_path)
                    validation_result['stages']['arelle_validation'] = arelle_results
                    
                    # Log Arelle validation results
                    if isinstance(arelle_results, dict) and 'validation_errors' in arelle_results:
                        error_count = len(arelle_results.get('validation_errors', []))
                        logger.info(f"🎯 Arelle validation completed: {error_count} issues found")
                except Exception as e:
                    logger.error(f"❌ Arelle validation failed: {e}")
                    validation_result['stages']['arelle_validation'] = {
                        'status': 'error',
                        'error': str(e)
                    }
            else:
                reason = 'arelle_unavailable'
                validation_result['stages']['arelle_validation'] = {'status': 'skipped', 'reason': reason}
            
            # STAGE 7: Result Synthesis
            logger.info("🔀 Stage 7: Synthesizing hybrid results...")
            synthesis = self._synthesize_results(validation_result['stages'])
            validation_result['final_report'] = synthesis
            
            logger.info(f"✅ Hybrid validation completed - Overall: {synthesis.get('overall_status', 'UNKNOWN')}")
            return validation_result
            
        except Exception as e:
            logger.error(f"❌ Hybrid validation failed: {e}")
            validation_result['status'] = 'error'
            validation_result['error'] = str(e)
            return validation_result
    
    def _count_facts_by_namespace(self, facts: Dict[str, Any]) -> Dict[str, int]:
        """Count facts by namespace prefix"""
        namespace_counts = {}
        for fact_name in facts.keys():
            if ':' in fact_name:
                prefix = fact_name.split(':')[0]
                namespace_counts[prefix] = namespace_counts.get(prefix, 0) + 1
        return namespace_counts
    
    def _resolve_concepts_in_dmp(self, facts: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve business facts against DMP database with enhanced filtering and pipeline connectivity"""
        results = {
            'status': 'completed',
            'total_facts': len(facts),
            'business_facts': 0,
            'resolved_facts': 0,
            'unresolved_facts': 0,
            'resolution_details': [],
            'resolution_by_source': {},
            'timestamp': datetime.now().isoformat()
        }
        
        # Debug initial facts structure
        logger.info(f"🔍 Resolving concepts from {len(facts)} initial facts")
        logger.debug(f"📊 Facts structure: {list(facts.keys())[:10]}")
        
        # ENHANCED: Skip structural XBRL elements completely
        structural_elements = {
            'facts', 'contexts', 'units', 'namespaces', 'parsing_statistics', 'file_path'
        }
        
        processed_facts = 0
        
        for fact_name, fact_data in facts.items():
            processed_facts += 1
            
            # Skip structural elements first
            if fact_name in structural_elements:
                logger.debug(f"🚫 Skipping structural element: {fact_name}")
                continue
                
            # FIXED: Enhanced business concept detection for better pipeline flow
            is_business_concept = False
            fact_instance = fact_data
            
            # Handle both single facts and fact lists
            if isinstance(fact_data, list) and fact_data:
                fact_instance = fact_data[0]
            
            if isinstance(fact_instance, dict):
                is_business_concept = fact_instance.get('is_business_concept', False)
                prefix = fact_instance.get('prefix', '')
                
                # Enhanced business concept patterns - more inclusive for FINREP
                business_prefixes = ['eba_', 'find', 'finrep', 'corep', 'met', 'dim', 'gb']
                if any(bp in prefix.lower() for bp in business_prefixes):
                    is_business_concept = True
                    logger.debug(f"✅ Business concept by prefix: {fact_name} (prefix: {prefix})")
                elif prefix.lower() not in ['xbrl', 'xml', 'xsi', 'link', 'xlink'] and ':' in fact_name:
                    is_business_concept = True
                    logger.debug(f"✅ Business concept by non-structural namespace: {fact_name}")
                
            if not is_business_concept:
                logger.debug(f"🚫 Skipping non-business concept: {fact_name}")
                continue
            
            # Only process actual XBRL business facts (with namespace prefixes)
            if ':' not in fact_name:
                logger.debug(f"🚫 Skipping non-namespaced element: {fact_name}")
                continue
            
            results['business_facts'] += 1
            
            # FIXED: Enhanced logging for concept resolution debugging
            logger.debug(f"🔎 Attempting to resolve concept: {fact_name}")
            
            resolution = concept_resolver.resolve_concept_from_dmp(fact_name)
            
            detail = {
                'fact_name': fact_name,
                'resolved': resolution is not None,
                'source_table': resolution.get('source') if resolution else None,
                'concept_code': resolution.get('ConceptCode') if resolution else None,
                'concept_type': resolution.get('ConceptType') if resolution else None
            }
            
            results['resolution_details'].append(detail)
            
            if resolution:
                results['resolved_facts'] += 1
                source = resolution.get('source', 'unknown')
                results['resolution_by_source'][source] = results['resolution_by_source'].get(source, 0) + 1
                logger.debug(f"✅ Resolved {fact_name} -> {resolution.get('ConceptCode')} (source: {source})")
            else:
                results['unresolved_facts'] += 1
                logger.debug(f"❌ Could not resolve: {fact_name}")
        
        # Calculate resolution rate based on business facts
        if results['business_facts'] > 0:
            resolution_rate = (results['resolved_facts'] / results['business_facts']) * 100
            results['resolution_rate'] = f"{resolution_rate:.1f}%"
        else:
            results['resolution_rate'] = "0%"
        
        # Enhanced logging for debugging pipeline issues
        logger.info(f"📊 Pipeline debugging:")
        logger.info(f"   📥 Input facts: {len(facts)}")
        logger.info(f"   🔄 Processed facts: {processed_facts}")
        logger.info(f"   🏢 Business facts identified: {results['business_facts']}")
        logger.info(f"   ✅ Concepts resolved: {results['resolved_facts']}")
        logger.info(f"   📈 Resolution rate: {results['resolution_rate']}")
        
        if results['business_facts'] == 0:
            logger.warning("⚠️ No business facts identified - check fact parsing and is_business_concept logic")
            # Sample some fact names for debugging
            sample_facts = list(facts.keys())[:10]
            logger.info(f"📝 Sample fact names: {sample_facts}")
        
        return results
    
    def _synthesize_results(self, stages: Dict[str, Any]) -> Dict[str, Any]:
        """Synthesize results from all validation stages including Arelle errors"""
        
        synthesis = {
            'validation_strategy': 'hybrid',
            'timestamp': datetime.now().isoformat(),
            'stage_summary': {},
            'validation_results': [],
            'total_errors': 0,
            'total_warnings': 0
        }
        
        # Summarize each stage
        for stage_name, stage_data in stages.items():
            if isinstance(stage_data, dict):
                synthesis['stage_summary'][stage_name] = stage_data.get('status', 'unknown')
        
        # CRITICAL FIX: Extract Arelle validation results 
        arelle_results = stages.get('arelle_validation', {})
        if isinstance(arelle_results, dict) and arelle_results.get('status') == 'completed':
            
            # Extract Arelle errors
            arelle_errors = arelle_results.get('errors', [])
            for error in arelle_errors:
                synthesis['validation_results'].append({
                    'type': 'business_rule_violation',
                    'severity': 'error', 
                    'message': error.get('message', 'Business rule validation error'),
                    'category': error.get('category', 'validation'),
                    'source': 'arelle_validation',
                    'line_number': error.get('line_number'),
                    'fact_name': error.get('fact_name', 'unknown')
                })
                synthesis['total_errors'] += 1
            
            # Extract Arelle warnings  
            arelle_warnings = arelle_results.get('warnings', [])
            for warning in arelle_warnings:
                synthesis['validation_results'].append({
                    'type': 'business_rule_warning',
                    'severity': 'warning',
                    'message': warning.get('message', 'Business rule validation warning'),
                    'category': warning.get('category', 'validation'), 
                    'source': 'arelle_validation',
                    'line_number': warning.get('line_number'),
                    'fact_name': warning.get('fact_name', 'unknown')
                })
                synthesis['total_warnings'] += 1
            
            logger.info(f"🎯 Extracted Arelle results: {len(arelle_errors)} errors, {len(arelle_warnings)} warnings")
        
        # Extract DMP validation results if available
        dmp_validation = stages.get('dmp_validation', {})
        if isinstance(dmp_validation, dict) and 'validation_results' in dmp_validation:
            dmp_results = dmp_validation.get('validation_results', [])
            synthesis['validation_results'].extend(dmp_results)
            synthesis['total_errors'] += len([r for r in dmp_results if r.get('severity') == 'error'])
            synthesis['total_warnings'] += len([r for r in dmp_results if r.get('severity') == 'warning'])
        
        # Calculate overall metrics
        dmp_resolution = stages.get('dmp_concept_resolution', {})
        resolution_rate = float(dmp_resolution.get('resolution_rate', '0%').replace('%', ''))
        
        # Determine overall status (updated to consider validation results)
        if synthesis['total_errors'] > 0:
            synthesis['overall_status'] = 'VALIDATION_FAILED'
            synthesis['recommendation'] = f"Validation failed with {synthesis['total_errors']} errors - review and fix issues"
        elif synthesis['total_warnings'] > 0:
            synthesis['overall_status'] = 'VALIDATION_WARNINGS' 
            synthesis['recommendation'] = f"Validation completed with {synthesis['total_warnings']} warnings - review recommended"
        elif resolution_rate >= 90:
            synthesis['overall_status'] = 'EXCELLENT'
            synthesis['recommendation'] = 'Outstanding DMP concept coverage - validation highly reliable'
        elif resolution_rate >= 75:
            synthesis['overall_status'] = 'VERY_GOOD'
            synthesis['recommendation'] = 'Very good DMP concept coverage - validation reliable'
        elif resolution_rate >= 60:
            synthesis['overall_status'] = 'GOOD'
            synthesis['recommendation'] = 'Good DMP concept coverage - most concepts validated'
        elif resolution_rate >= 40:
            synthesis['overall_status'] = 'PARTIAL'
            synthesis['recommendation'] = 'Partial coverage - consider updating DMP database or XBRL file'
        else:
            synthesis['overall_status'] = 'POOR'
            synthesis['recommendation'] = 'Low coverage - XBRL file may not be compatible with DMP 4.0'
        
        # Add key metrics
        synthesis['key_metrics'] = {
            'concept_resolution_rate': dmp_resolution.get('resolution_rate', '0%'),
            'total_facts_processed': dmp_resolution.get('total_facts', 0),
            'dmp_stages_completed': sum(1 for stage in ['dmp_concept_resolution', 'dmp_rule_validation', 'dmp_validation'] 
                                      if stages.get(stage, {}).get('status') == 'completed'),
            'arelle_available': stages.get('arelle_validation', {}).get('status') != 'skipped',
            'validation_errors_found': synthesis['total_errors'],
            'validation_warnings_found': synthesis['total_warnings']
        }
        
        # Add advantages of hybrid approach
        synthesis['hybrid_advantages'] = [
            f"✅ Fast DMP validation with {dmp_resolution.get('resolution_rate', '0%')} concept coverage",
            "✅ Multi-table concept resolution (tConcept, tDataPoint, tMember)",
            "✅ Native DMP rule validation",
            "✅ No dependency issues or network requirements"
        ]
        
        if stages.get('arelle_validation', {}).get('status') == 'completed':
            synthesis['hybrid_advantages'].append("✅ Full XBRL 2.1 specification compliance via Arelle")
            synthesis['hybrid_advantages'].append(f"✅ Business rule validation: {synthesis['total_errors']} errors, {synthesis['total_warnings']} warnings found")
        
        return synthesis
    
    def get_engine_status(self) -> Dict[str, Any]:
        """Get comprehensive status of the hybrid engine"""
        return {
            'engine_type': 'hybrid',
            'components': {
                'dmp_database': self.dmp_available,
                'arelle_runner': self.arelle_available,
                'fact_parser': True,
                'rule_engine': self.dmp_available
            },
            'dmp_info': dmp_db.test_connection() if self.dmp_available else None,
            'capabilities': {
                'concept_resolution': self.dmp_available,
                'rule_validation': self.dmp_available,
                'arelle_fallback': self.arelle_available,
                'fact_parsing': True
            }
        }

# Global instance - initialize with default architecture 2.0
try:
    hybrid_engine = HybridValidationEngine(architecture_version='arch_2_0')
except Exception as e:
    logger.error(f"Failed to initialize global hybrid engine: {e}")
    hybrid_engine = None