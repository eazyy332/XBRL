
import os
import time
import json
import logging
from werkzeug.utils import secure_filename
from enhanced_validation_engine import EnhancedValidationEngine
from config import FINREP_RULES

logger = logging.getLogger(__name__)

def validate_request_files(validation_mode='basic'):
    """Validate that required files are present in request and process them"""
    from flask import request, jsonify
    
    if 'instance' not in request.files:
        return jsonify({
            'success': False,
            'error': 'Instance file is required'
        }), 400
    
    instance_file = request.files['instance']
    taxonomy_file = request.files.get('taxonomy')
    table_code = request.form.get('table_code')
    
    if instance_file.filename == '':
        return jsonify({
            'success': False,
            'error': 'Instance file must have a valid filename'
        }), 400
    
    # Process the validation
    result = validate_files_core(instance_file, taxonomy_file, table_code, validation_mode == 'enhanced')
    
    if result.get('success'):
        return jsonify(result), 200
    else:
        return jsonify(result), 500

def validate_files_core(instance_file, taxonomy_file, table_code=None, enhanced_mode=True):
    """ENHANCED: Core validation logic with architecture detection and hybrid validation"""
    start_time = time.time()
    
    try:
        # Setup file paths
        os.makedirs("uploads", exist_ok=True)
        instance_filename = secure_filename(instance_file.filename)
        instance_path = os.path.join("uploads", instance_filename)
        
        # Save instance file
        logger.info(f"Saving instance file: {instance_filename}")
        instance_file.save(instance_path)
        
        # Handle taxonomy file if provided
        taxonomy_path = None
        if taxonomy_file and taxonomy_file.filename:
            taxonomy_filename = secure_filename(taxonomy_file.filename)
            taxonomy_path = os.path.join("uploads", taxonomy_filename)
            logger.info(f"Saving taxonomy file: {taxonomy_filename}")
            taxonomy_file.save(taxonomy_path)
        
        # Initialize hybrid validation engine with auto-detection
        from hybrid_validation_engine import HybridValidationEngine
        validation_engine = HybridValidationEngine()
        
        # Run hybrid validation with automatic architecture detection
        logger.info("Starting hybrid validation with automatic architecture detection...")
        validation_result = validation_engine.validate_hybrid(
            instance_path, taxonomy_path, auto_detect_architecture=True
        )
        
        # Extract results from hybrid validation
        final_report = validation_result.get('final_report', {})
        stages = validation_result.get('stages', {})
        
        # Enhanced DMP integration with architecture-specific database
        if table_code and enhanced_mode:
            architecture_version = validation_result.get('architecture_version', 'arch_2_0')
            db_name = validation_result.get('dmp_database', 'DMP 4.0')
            logger.info(f"Enhancing with {db_name} database context for table: {table_code}")
            try:
                from dmp_database import dmp_db
                dmp_context = dmp_db.get_table_concepts(table_code)
                final_report['dmpContext'] = dmp_context[:50]  # Limit for performance
                final_report['dmpEnhanced'] = True
                final_report['selectedTable'] = table_code
                logger.info(f"Added {len(dmp_context)} DMP concept definitions")
            except Exception as dmp_error:
                logger.warning(f"DMP enhancement failed: {str(dmp_error)}")
                final_report['dmpEnhanced'] = False
        
        processing_time = time.time() - start_time
        logger.info(f"Hybrid validation completed in {processing_time:.2f} seconds")
        
        # FIXED: Extract validation results from synthesis (includes Arelle results)
        dmp_resolution = stages.get('dmp_concept_resolution', {})
        dmp_validation = stages.get('dmp_validation', {})
        
        # Get all validation results including Arelle errors/warnings
        all_validation_results = final_report.get('validation_results', [])
        total_errors = final_report.get('total_errors', 0)
        total_warnings = final_report.get('total_warnings', 0)
        
        response_data = {
            'success': True,
            'result': {
                'isValid': total_errors == 0,  # Updated: Consider validation errors
                'status': final_report.get('overall_status', 'UNKNOWN'),
                'errors': all_validation_results,  # Now includes Arelle results!
                'dmpResults': all_validation_results,  # For backwards compatibility
                'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                'filesProcessed': {
                    'instanceFile': instance_filename,
                    'taxonomyFile': taxonomy_file.filename if taxonomy_file else None
                },
                'validationStats': {
                    'totalRules': len(all_validation_results),
                    'passedRules': 0,  # Updated for Arelle-based validation
                    'failedRules': len([r for r in all_validation_results if r.get('severity') == 'error']),
                    'warningRules': len([r for r in all_validation_results if r.get('severity') == 'warning']),
                    'totalErrorsDetected': total_errors,
                    'totalWarningsDetected': total_warnings,
                    'conceptResolutionRate': dmp_resolution.get('resolution_rate', '0%'),
                    'dmpResolvedConcepts': dmp_resolution.get('resolved_facts', 0)
                },
                'architectureDetection': {
                    'detectedArchitecture': validation_result.get('architecture_version', 'unknown'),
                    'databaseUsed': validation_result.get('dmp_database', 'unknown'),
                    'taxonomyUsed': validation_result.get('taxonomy_used', 'none')
                },
                'conceptMapping': dmp_resolution,
                'arelleValidation': {
                    'enabled': stages.get('arelle_validation', {}).get('status') == 'completed',
                    'errors_found': len([r for r in all_validation_results if r.get('source') == 'arelle_validation' and r.get('severity') == 'error']),
                    'warnings_found': len([r for r in all_validation_results if r.get('source') == 'arelle_validation' and r.get('severity') == 'warning'])
                }
            },
            'processingTime': processing_time,
            'validationEngine': f'Hybrid Validation Engine v4.1 (Architecture: {validation_result.get("architecture_version", "unknown")})',
            'databaseFile': validation_result.get('dmp_database', 'unknown')
        }
        
        logger.info(f"Returning enhanced validation response with {len(response_data['result']['dmpResults'])} results")
        return response_data
        
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Enhanced validation failed after {processing_time:.2f} seconds: {str(e)}")
        
        return {
            'success': False,
            'error': f'Enhanced validation processing failed: {str(e)}',
            'processingTime': processing_time,
            'troubleshooting': 'Check file format, taxonomy processing, and DMP database connectivity'
        }
