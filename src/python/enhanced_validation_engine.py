
import logging
import subprocess
from arelle_core import build_enhanced_arelle_command
from arelle_runner import ArelleRunner  # FIXED: Use ArelleRunner instead of old arelle_core
from taxonomy_processor import TaxonomyProcessor
from concept_mapping_service import ConceptMappingService
from validation_logic import ValidationProcessor

logger = logging.getLogger(__name__)

class EnhancedValidationEngine:
    def __init__(self):
        self.taxonomy_processor = TaxonomyProcessor()
        self.concept_mapper = ConceptMappingService()
        self.validation_processor = ValidationProcessor()
        self.arelle_runner = ArelleRunner()  # FIXED: Use enhanced ArelleRunner
    
    def run_comprehensive_validation(self, instance_path, taxonomy_path=None):
        """
        Run comprehensive validation with taxonomy processing and concept mapping
        """
        try:
            logger.info("🚀 Starting comprehensive validation with taxonomy processing")
            
            # Step 1: Process taxonomy file if provided
            extracted_schemas = []
            all_packages = []
            extraction_dir = None
            
            if taxonomy_path:
                logger.info(f"📦 Processing taxonomy: {taxonomy_path}")
                extracted_schemas, all_packages, extraction_dir = self.taxonomy_processor.process_taxonomy_file(taxonomy_path)
                
                # Verify taxonomy contains expected concepts
                taxonomy_concepts = self.taxonomy_processor.verify_taxonomy_concepts(extracted_schemas)
            else:
                logger.info("⚠️ No taxonomy provided, using basic validation")
                taxonomy_concepts = {}
            
            # Step 2: Pre-validate concepts against DMP database
            logger.info("🔍 Pre-validating concepts against DMP database")
            concept_mapping = self.concept_mapper.pre_validate_concepts(instance_path, taxonomy_concepts)
            
            # Step 3: Generate missing schema elements if needed
            generated_schema = None
            if concept_mapping['dmp_available']:
                logger.info(f"🔧 Generating schema for {len(concept_mapping['dmp_available'])} DMP-available concepts")
                generated_schema = self.concept_mapper.generate_missing_schema_elements(concept_mapping['dmp_available'])
                if generated_schema:
                    extracted_schemas.append(generated_schema)
            
            # Step 4: Run Arelle validation with all available schemas
            if extracted_schemas or all_packages:
                logger.info("🔧 Running enhanced Arelle validation with extracted schemas")
                arelle_result = self._run_enhanced_arelle_validation(instance_path, extracted_schemas, all_packages)
            else:
                logger.info("🔧 Running enhanced ArelleRunner validation")
                arelle_result = self.arelle_runner.validate_with_arelle(instance_path, "dummy_taxonomy.zip")
                # Convert ArelleRunner result to subprocess format for compatibility
                arelle_result = self._convert_arelle_runner_result(arelle_result)
            
            # Step 5: Process results with enhanced concept resolution
            logger.info("📊 Processing validation results with enhanced concept resolution")
            processed_results = self.validation_processor.process_arelle_output(arelle_result, enhanced_mode=True)
            
            # Step 6: Enhance results with pre-validation mapping
            processed_results = self._enhance_results_with_mapping(processed_results, concept_mapping)
            
            logger.info("✅ Comprehensive validation completed")
            
            return arelle_result.returncode, arelle_result.stdout, arelle_result.stderr, {
                'validation_mode': 'comprehensive_enhanced',
                'taxonomy_processed': taxonomy_path is not None,
                'schemas_extracted': len(extracted_schemas),
                'packages_found': len(all_packages),
                'concept_mapping': concept_mapping,
                'generated_schema': generated_schema is not None,
                'processed_results': processed_results
            }
            
        except Exception as e:
            logger.error(f"❌ Comprehensive validation failed: {str(e)}")
            # Fallback to enhanced ArelleRunner
            arelle_result = self.arelle_runner.validate_with_arelle(instance_path, "dummy_taxonomy.zip")
            arelle_result = self._convert_arelle_runner_result(arelle_result)
            processed_results = self.validation_processor.process_arelle_output(arelle_result, enhanced_mode=False)
            
            return arelle_result.returncode, arelle_result.stdout, arelle_result.stderr, {
                'validation_mode': 'fallback_basic',
                'error': str(e),
                'processed_results': processed_results
            }
    
    def _run_enhanced_arelle_validation(self, instance_path, extracted_schemas, all_packages):
        """Run Arelle validation with all available schemas and packages"""
        try:
            # Prioritize packages based on XBRL requirements
            if all_packages:
                xbrl_analysis = self.taxonomy_processor.dependency_manager.analyze_xbrl_file_requirements(instance_path)
                prioritized_packages = self.taxonomy_processor.dependency_manager.prioritize_packages_by_xbrl_requirements(all_packages, xbrl_analysis)
            else:
                prioritized_packages = []
            
            # Build enhanced Arelle command
            arelle_cmd = build_enhanced_arelle_command(instance_path, extracted_schemas, prioritized_packages)
            
            logger.info(f"🔧 Enhanced Arelle command with {len(extracted_schemas)} schemas and {len(prioritized_packages)} packages")
            
            # Execute validation
            result = subprocess.run(
                arelle_cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            logger.info(f"✅ Enhanced Arelle validation completed with return code: {result.returncode}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Enhanced Arelle validation failed: {str(e)}")
            # Fallback to ArelleRunner
            arelle_result = self.arelle_runner.validate_with_arelle(instance_path, "dummy_taxonomy.zip")
            return self._convert_arelle_runner_result(arelle_result)
    
    def _enhance_results_with_mapping(self, processed_results, concept_mapping):
        """Enhance validation results with pre-validation concept mapping information"""
        try:
            # Update error messages for concepts that were found in DMP
            if 'errors' in processed_results:
                enhanced_errors = []
                for error in processed_results['errors']:
                    if error.get('concept') in concept_mapping['resolved']:
                        dmp_concept = concept_mapping['resolved'][error['concept']]
                        error['severity'] = 'warning'
                        error['message'] = f"Concept exists in DMP 4.0 database: {error['concept']} -> {dmp_concept['ConceptCode']}"
                        error['dmp_resolved'] = True
                    enhanced_errors.append(error)
                processed_results['errors'] = enhanced_errors
            
            # Add concept mapping summary to results
            processed_results['conceptMapping'] = {
                'totalConcepts': len(concept_mapping['resolved']) + len(concept_mapping['unresolved']),
                'dmpResolved': len(concept_mapping['resolved']),
                'dmpAvailableButMissingFromTaxonomy': len(concept_mapping['dmp_available']),
                'completelyMissing': len(concept_mapping['taxonomy_missing']),
                'resolutionRate': len(concept_mapping['resolved']) * 100 // max(len(concept_mapping['resolved']) + len(concept_mapping['unresolved']), 1)
            }
            
            # Recalculate validation status
            real_errors = [e for e in processed_results.get('errors', []) if e.get('severity') == 'error']
            processed_results['isValid'] = len(real_errors) == 0
            processed_results['status'] = 'valid' if processed_results['isValid'] else 'invalid'
            
            return processed_results
            
        except Exception as e:
            logger.error(f"❌ Failed to enhance results with mapping: {str(e)}")
            return processed_results
    
    def _convert_arelle_runner_result(self, arelle_result):
        """Convert ArelleRunner result format to subprocess.CompletedProcess format"""
        if arelle_result.get('status') == 'completed':
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
