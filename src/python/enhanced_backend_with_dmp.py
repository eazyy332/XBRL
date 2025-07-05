import json
from flask import Flask, request, jsonify
from flask_cors import CORS
import time
from datetime import datetime
from dmp_database import dmp_db
from config import FINREP_RULES
from arelle_core import test_arelle_path
from validation_endpoints import validate_files_core, validate_request_files
from dmp_direct_validation import DMPDirectValidator
from taxonomy_dependency_manager import EBATaxonomyDependencyManager
from dmp_concept_resolver import concept_resolver
from taxonomy_version_detector import get_taxonomy_recommendations
import logging
import os
from pathlib import Path

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Setup logging with more efficient configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Flask setup
app = Flask(__name__)
CORS(app)

# Initialize dependency manager
dependency_manager = EBATaxonomyDependencyManager()

# Test endpoint for connectivity
@app.route("/test", methods=["GET"])
def test_connection():
    """Simple test endpoint to verify backend connectivity"""
    return jsonify({
        "status": "success",
        "message": "Backend is running",
        "timestamp": datetime.now().isoformat()
    }), 200

@app.route("/", methods=["GET"])
def root():
    """Root endpoint"""
    return jsonify({
        "status": "Enhanced XBRL Validation Server",
        "version": "2.1",
        "endpoints": [
            "/test",
            "/analyze-taxonomy-requirements",
            "/validate-enhanced",
            "/validate-dmp-direct"
        ]
    }), 200

@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint with backend status"""
    try:
        # Test database connection
        db_status = "unknown"
        try:
            connection_status = dmp_db.test_connection()
            db_status = "connected" if connection_status.get('connected') else "disconnected"
        except Exception as e:
            db_status = f"error: {str(e)}"
        
        # Test concept resolver
        resolver_status = "unknown"
        try:
            stats = concept_resolver.get_concept_statistics()
            resolver_status = "working" if not stats.get('error') else f"error: {stats.get('error')}"
        except Exception as e:
            resolver_status = f"error: {str(e)}"
        
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "database": db_status,
                "concept_resolver": resolver_status,
                "upload_folder": os.path.exists(UPLOAD_FOLDER)
            },
            "endpoints_available": [
                "/test",
                "/health", 
                "/analyze-taxonomy-requirements",
                "/validate-enhanced",
                "/validate-dmp-direct"
            ]
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

# Register architecture detection routes
try:
    from detect_architecture_endpoint import register_detect_architecture_routes
    register_detect_architecture_routes(app, UPLOAD_FOLDER)
    logger.info("✅ Architecture detection routes registered")
except Exception as e:
    logger.error(f"❌ Failed to register architecture routes: {e}")

# Register architecture detection routes
try:
    from detect_architecture_endpoint import register_detect_architecture_routes
    register_detect_architecture_routes(app, UPLOAD_FOLDER)
    logger.info("✅ Architecture detection routes registered")
except Exception as e:
    logger.error(f"❌ Failed to register architecture routes: {e}")

@app.route('/debug/validation-fix-test', methods=['GET'])
def debug_validation_fix_test():
    """Test the validation fixes"""
    try:
        extracted_dir = "C:\\Users\\berbe\\Documents\\AI\\XBRL-validation\\taxonomies\\EBA\\extracted"
        
        # Test fixed discovery
        entry_points = dependency_manager.discover_comprehensive_entry_points(extracted_dir)
        
        # Test fixed validation 
        valid_packages, invalid_packages = dependency_manager.verify_package_integrity(entry_points)
        
        return jsonify({
            "status": "fix_test_complete",
            "entry_points_found": len(entry_points),
            "valid_packages": len(valid_packages),
            "invalid_packages": len(invalid_packages),
            "sample_valid": [os.path.basename(p) for p in valid_packages[:5]],
            "sample_invalid": [{"file": os.path.basename(p[0]), "error": p[1]} for p in invalid_packages[:3]],
            "fix_status": "✅ XSD validation fixed" if valid_packages else "❌ Still issues",
            "next_action": "Test with actual XBRL validation" if valid_packages else "Check file paths"
        })
        
    except Exception as e:
        return jsonify({"status": "fix_test_error", "error": str(e)}), 500

@app.route('/debug/xbrl-intelligence-test', methods=['POST'])
def debug_xbrl_intelligence_test():
    """Test XBRL-intelligent validation"""
    try:
        # Test with your FINREP file
        xbrl_file = "uploads/DUMMYLEI123456789012_GB_FINREP020400_FINREP9INDGAAP_2021-06-30_20201218154748000.xbrl"
        
        # Analyze XBRL file
        xbrl_analysis = dependency_manager.analyze_xbrl_file_requirements(xbrl_file)
        
        # Get packages
        extracted_dir = "C:\\Users\\berbe\\Documents\\AI\\XBRL-validation\\taxonomies\\EBA\\extracted"
        all_packages = dependency_manager.discover_comprehensive_entry_points(extracted_dir)
        valid_packages, _ = dependency_manager.verify_package_integrity(all_packages)
        
        # Test prioritization
        prioritized = dependency_manager.prioritize_packages_by_xbrl_requirements(valid_packages, xbrl_analysis)
        
        return jsonify({
            "status": "xbrl_intelligence_test_complete",
            "xbrl_framework": xbrl_analysis['framework'],
            "accounting_standard": xbrl_analysis['accounting_standard'],
            "consolidation": xbrl_analysis['consolidation'],
            "required_modules_count": len(xbrl_analysis['required_modules']),
            "total_packages": len(valid_packages),
            "prioritized_packages": len(prioritized),
            "top_priority_packages": [os.path.basename(p) for p in prioritized[:10]],
            "expected_improvement": "Should reduce missing concepts from 128 to <20 by loading correct FINREP modules first",
            "framework_match": "FINREP" in xbrl_analysis['framework']
        })
        
    except Exception as e:
        return jsonify({"status": "test_error", "error": str(e)}), 500

@app.route('/debug/metadata-discovery', methods=['GET'])
def debug_metadata_discovery():
    """Test EBA metadata discovery"""
    try:
        extracted_dir = "C:\\Users\\berbe\\Documents\\AI\\XBRL-validation\\taxonomies\\EBA\\extracted"
        
        # Find metadata packages specifically
        metadata_packages = []
        for pattern in ["**/eba_met*.xsd", "**/find*.xsd", "**/metadata*.xsd"]:
            matches = list(Path(extracted_dir).glob(pattern))
            metadata_packages.extend([str(m) for m in matches])
        
        return jsonify({
            "status": "metadata_discovery_complete",
            "metadata_packages_found": len(metadata_packages),
            "sample_metadata_packages": [os.path.basename(p) for p in metadata_packages[:10]],
            "search_patterns_used": ["**/eba_met*.xsd", "**/find*.xsd", "**/metadata*.xsd"],
            "expected_result": "Should find EBA metadata files containing eba_met: concepts",
            "next_step": "If 0 packages found, check if EBA metadata taxonomy is in the ZIP file"
        })
        
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route('/debug/eba-metadata-check', methods=['GET'])
def debug_eba_metadata_check():
    """Controleer specifiek EBA metadata discovery"""
    try:
        extracted_dir = "C:\\Users\\berbe\\Documents\\AI\\XBRL-validation\\taxonomies\\EBA\\extracted"
        
        # Zoek naar EBA metadata bestanden
        eba_patterns = ["**/eba_met*.xsd", "**/dict/**/*.xsd", "**/metadata*.xsd"]
        found_files = []
        
        for pattern in eba_patterns:
            matches = list(Path(extracted_dir).glob(pattern))
            found_files.extend([str(m) for m in matches])
        
        # Controleer inhoud van gevonden bestanden
        eba_concepts_check = []
        for file_path in found_files[:5]:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                has_eba_met = 'eba_met:' in content
                has_namespace = 'eba.europa.eu' in content
                
                eba_concepts_check.append({
                    "file": os.path.basename(file_path),
                    "has_eba_met_concepts": has_eba_met,
                    "has_eba_namespace": has_namespace,
                    "file_size": len(content)
                })
            except:
                continue
        
        return jsonify({
            "status": "eba_metadata_check_complete",
            "total_metadata_files_found": len(found_files),
            "sample_files": [os.path.basename(f) for f in found_files[:10]],
            "content_analysis": eba_concepts_check,
            "diagnosis": "Als has_eba_met_concepts = false voor alle bestanden, dan mist de EBA metadata taxonomy",
            "next_steps": [
                "Check if EBA metadata taxonomy is in the ZIP file",
                "Look for files containing eba_met: namespace definitions",
                "Consider downloading complete EBA 4.0 taxonomy package"
            ]
        })
        
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route('/debug/dmp-compatibility', methods=['POST'])
def debug_dmp_compatibility():
    """Test DPM version compatibility"""
    try:
        xbrl_file = "uploads/DUMMYLEI123456789012_GB_FINREP020400_FINREP9INDGAAP_2021-06-30_20201218154748000.xbrl"
        
        # Import validation logic for compatibility analysis
        from validation_logic import ValidationProcessor
        validator = ValidationProcessor()
        
        compatibility = validator.analyze_xbrl_dmp_version_compatibility(xbrl_file)
        suggestions = validator.suggest_compatibility_fixes(compatibility) if compatibility else []
        
        return jsonify({
            "status": "dmp_compatibility_check_complete",
            "compatibility_analysis": compatibility,
            "compatibility_suggestions": suggestions,
            "diagnosis": "Version mismatch could explain missing concepts",
            "recommended_action": "Use DPM 4.0 compatible XBRL sample or enable backwards compatibility"
        })
        
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route('/debug/concept-resolution', methods=['POST'])
def debug_concept_resolution():
    """Test DMP concept resolution for XBRL concepts"""
    try:
        
        # Get test concepts from request or use defaults
        test_concepts = request.json.get('concepts', [
            'eba_met:qFAF',
            'eba_met:m1',
            'find:LCR_1_1',
            'eba_met_3.4:x123',
            'nonexistent:concept'
        ]) if request.is_json else [
            'eba_met:qFAF',
            'eba_met:m1', 
            'find:LCR_1_1'
        ]
        
        logger.info(f"🔍 Testing concept resolution for {len(test_concepts)} concepts")
        
        # Test concept resolution
        resolution_results = {}
        for concept in test_concepts:
            result = concept_resolver.resolve_concept_from_dmp(concept)
            resolution_results[concept] = {
                'resolved': result is not None,
                'dmp_concept': result,
                'status': 'found' if result else 'missing'
            }
        
        # Get concept statistics
        stats = concept_resolver.get_concept_statistics()
        
        return jsonify({
            "status": "concept_resolution_test_complete",
            "test_concepts": test_concepts,
            "resolution_results": resolution_results,
            "resolution_rate": f"{sum(1 for r in resolution_results.values() if r['resolved']) * 100 // len(test_concepts)}%",
            "dmp_database_stats": stats,
            "diagnosis": "This shows which eba_met concepts can be resolved against DMP 4.0 database",
            "next_steps": [
                "If resolution rate is low, check tConcept and tDataPoint tables",
                "If concepts are found, the taxonomy loading issue is isolated",
                "Update validation logic to use resolved concepts"
            ]
        })
        
    except Exception as e:
        return jsonify({"status": "concept_resolution_error", "error": str(e)}), 500

@app.route('/debug/comprehensive-validation-test', methods=['POST'])
def debug_comprehensive_validation_test():
    """Test the new comprehensive validation system"""
    try:
        # Test with your FINREP file
        xbrl_file = "uploads/DUMMYLEI123456789012_GB_FINREP020400_FINREP9INDGAAP_2021-06-30_20201218154748000.xbrl"
        
        if not os.path.exists(xbrl_file):
            return jsonify({
                "status": "error",
                "message": "Test XBRL file not found. Please upload a file first."
            }), 400
        
        # Test comprehensive validation
        from enhanced_validation_engine import EnhancedValidationEngine
        validation_engine = EnhancedValidationEngine()
        
        # Mock taxonomy file path (if available)
        taxonomy_path = None
        if os.path.exists("uploads/taxonomy.zip"):
            taxonomy_path = "uploads/taxonomy.zip"
        
        logger.info("🧪 Testing comprehensive validation system")
        return_code, stdout, stderr, metadata = validation_engine.run_comprehensive_validation(
            xbrl_file, taxonomy_path
        )
        
        processed_results = metadata.get('processed_results', {})
        
        return jsonify({
            "status": "comprehensive_validation_test_complete",
            "validation_mode": metadata.get('validation_mode'),
            "arelle_return_code": return_code,
            "taxonomy_processed": metadata.get('taxonomy_processed', False),
            "schemas_extracted": metadata.get('schemas_extracted', 0),
            "packages_found": metadata.get('packages_found', 0),
            "generated_schema": metadata.get('generated_schema', False),
            "concept_mapping": metadata.get('concept_mapping', {}),
            "validation_results": {
                "is_valid": processed_results.get('isValid', False),
                "total_errors": len([e for e in processed_results.get('errors', []) if e.get('severity') == 'error']),
                "total_warnings": len([e for e in processed_results.get('errors', []) if e.get('severity') == 'warning']),
                "dmp_results_count": len(processed_results.get('dmpResults', [])),
                "concept_resolution_rate": processed_results.get('conceptMapping', {}).get('resolutionRate', 0)
            },
            "expected_improvements": [
                "Taxonomy ZIP should be automatically extracted",
                "Missing eba_met concepts should be resolved from DMP database",
                "Generated schema should fill gaps between taxonomy and DMP",
                "Concept resolution rate should be >80%",
                "Errors should be reduced to warnings for DMP-available concepts"
            ]
        })
        
    except Exception as e:
        return jsonify({"status": "test_error", "error": str(e)}), 500

@app.route('/debug/taxonomy-verification', methods=['POST'])
def debug_taxonomy_verification():
    """Verify taxonomy contents and concept availability"""
    try:
        # Check if taxonomy ZIP exists
        taxonomy_files = [f for f in os.listdir("uploads") if f.endswith('.zip')]
        
        if not taxonomy_files:
            return jsonify({
                "status": "no_taxonomy_found",
                "message": "No taxonomy ZIP files found in uploads directory",
                "suggestion": "Upload the EBA taxonomy ZIP file from the provided URL"
            })
        
        # Process the first taxonomy file found
        from taxonomy_processor import TaxonomyProcessor
        processor = TaxonomyProcessor()
        
        taxonomy_path = os.path.join("uploads", taxonomy_files[0])
        logger.info(f"🔍 Verifying taxonomy: {taxonomy_path}")
        
        # Extract and process taxonomy
        extracted_schemas, all_packages, extraction_dir = processor.process_taxonomy_file(taxonomy_path)
        
        # Verify specific concepts
        test_concepts = ['eba_met:qCEF', 'eba_met:qAOF', 'eba_met:qFAF', 'find:LCR_1_1']
        found_concepts = processor.verify_taxonomy_concepts(extracted_schemas, test_concepts)
        
        return jsonify({
            "status": "taxonomy_verification_complete",
            "taxonomy_file": taxonomy_files[0],
            "extraction_dir": extraction_dir,
            "schemas_extracted": len(extracted_schemas),
            "packages_found": len(all_packages),
            "concept_verification": {
                "test_concepts": test_concepts,
                "found_concepts": found_concepts,
                "missing_concepts": [c for c in test_concepts if c not in found_concepts],
                "coverage_rate": len(found_concepts) * 100 // len(test_concepts)
            },
            "sample_schemas": [os.path.basename(s) for s in extracted_schemas[:10]],
            "diagnosis": "If coverage_rate < 100%, taxonomy may be incomplete or concepts use different naming"
        })
        
    except Exception as e:
        return jsonify({"status": "verification_error", "error": str(e)}), 500

@app.route("/validation-modes", methods=["GET"])
def validation_modes():
    """Get available validation modes"""
    try:
        modes = [
            {
                "mode": "fast",
                "name": "DMP-Direct (Fast)",
                "description": "Fast validation using DMP 4.0 database without taxonomy file",
                "requiresTaxonomy": False,
                "features": ["Direct database access", "203,924 validation rules", "Enhanced error detection"],
                "processingTime": "5-15 seconds",
                "recommended": True
            },
            {
                "mode": "comprehensive", 
                "name": "Professional (Comprehensive)",
                "description": "Full validation with taxonomy file and Arelle engine + dependency resolution",
                "requiresTaxonomy": True,
                "features": ["Complete EBA validation", "Formula validation", "Business rules", "Dependency resolution", "Missing concept detection"],
                "processingTime": "30-120 seconds",
                "recommended": False
            },
            {
                "mode": "enhanced",
                "name": "DMP-Enhanced (Premium)",
                "description": "Combines Arelle validation with DMP 4.0 database enhancement + dependency management",
                "requiresTaxonomy": True,
                "features": ["Best of both worlds", "Maximum accuracy", "Professional reporting", "Automatic dependency resolution"],
                "processingTime": "45-180 seconds",
                "recommended": False
            }
        ]
        
        return jsonify({
            "success": True,
            "modes": modes,
            "defaultMode": "comprehensive",
            "dmpDatabaseStatus": "active",
            "totalValidationRules": 203924,
            "dependencyManagementEnabled": True
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get validation modes: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route("/dmp/status", methods=["GET"])
def dmp_status():
    """Enhanced DMP 4.0 database status check with dependency information"""
    try:
        # Initialize dependency manager
        dep_manager = EBATaxonomyDependencyManager()
        dependency_status, available_packages = dep_manager.auto_resolve_dependencies()
        
        status = {
            "status": "active",
            "message": "DMP 4.0 Enhanced Validation with Dependency Management Available",
            "timestamp": time.strftime('%Y-%m-%dT%H:%M:%SZ'),
            "backend_version": "DMP 4.0 Enhanced Mode v2.0",
            "features": {
                "dmp_4_0_database": True,
                "validation_rules_support": True,
                "business_rules_engine": True,
                "dmp_direct_validation": True,
                "taxonomy_optional": True,
                "fast_mode": True,
                "comprehensive_mode": True,
                "dependency_resolution": True,
                "missing_concept_detection": True,
                "automatic_package_management": True,
                "dmp_version_compatibility": True
            },
            "dependency_management": {
                "status": "resolved" if dependency_status else "incomplete",
                "available_packages": len(available_packages),
                "total_packages_checked": 3,
                "taxonomy_directories": {
                    "eba": str(dep_manager.eba_dir),
                    "eurofiling": str(dep_manager.eurofiling_dir),
                    "xbrl_org": str(dep_manager.xbrl_org_dir)
                }
            }
        }
        
        # Test DMP 4.0 database connectivity with enhanced diagnostics
        try:
            dmp_status_result = dmp_db.test_connection()
            
            # Get comprehensive health check
            health_check = dmp_db.queries_manager.get_comprehensive_health_check()
            
            status["dmp_database"] = {
                **dmp_status_result,
                "health_check": health_check,
                "validation_rules_count": health_check.get("total_validation_rules", 0),
                "concepts_count": health_check.get("total_concepts", 0),
                "tables_count": health_check.get("total_tables", 0)
            }
            
            # Enhanced status message based on validation rules availability
            if health_check.get("total_validation_rules", 0) > 0:
                status["message"] = f"DMP 4.0 Ready - {health_check['total_validation_rules']} validation rules + dependency management + version compatibility"
                status["features"]["enhanced_error_detection"] = True
            
        except Exception as dmp_error:
            logger.error(f"DMP 4.0 status error: {str(dmp_error)}")
            status["dmp_database"] = {
                "status": "error",
                "message": str(dmp_error),
                "troubleshooting": "Check DPM_Database_v4_0_20241218.accdb file path and permissions"
            }
        
        return jsonify(status), 200
        
    except Exception as e:
        logger.error(f"DMP status check failed: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"DMP status check failed: {str(e)}"
        }), 500

@app.route("/dmp/tables", methods=["GET"])
def dmp_tables():
    """Get available DMP 4.0 tables"""
    try:
        tables = dmp_db.get_dmp_tables()
        
        return jsonify({
            "success": True,
            "tables": tables,
            "count": len(tables),
            "database_version": "DMP 4.0"
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get DMP tables: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route("/dmp/dependencies", methods=["GET"])
def dmp_dependencies():
    """Check taxonomy dependency status"""
    try:
        dep_manager = EBATaxonomyDependencyManager()
        dependency_status, available_packages = dep_manager.auto_resolve_dependencies()
        
        return jsonify({
            "success": True,
            "dependency_status": "resolved" if dependency_status else "incomplete",
            "available_packages": len(available_packages),
            "package_details": [
                {
                    "name": "EBA Framework 4.0",
                    "path": str(dep_manager.eba_dir / "taxo_package_4.0_errata5.zip"),
                    "available": (dep_manager.eba_dir / "taxo_package_4.0_errata5.zip").exists()
                },
                {
                    "name": "Eurofiling Filing Indicators",
                    "path": str(dep_manager.eurofiling_dir / "filing-indicators.zip"),
                    "available": (dep_manager.eurofiling_dir / "filing-indicators.zip").exists()
                },
                {
                    "name": "XBRL Base",
                    "path": str(dep_manager.xbrl_org_dir / "xbrl-base.zip"),
                    "available": (dep_manager.xbrl_org_dir / "xbrl-base.zip").exists()
                }
            ],
            "message": "All packages available" if dependency_status else "Some packages missing - validation will detect and provide download instructions"
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to check dependencies: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route("/validate-basic", methods=["POST"])
def validate_basic():
    """Basic XBRL validation endpoint"""
    return validate_request_files('basic')

@app.route("/analyze-taxonomy-requirements", methods=["POST"])
def analyze_taxonomy_requirements():
    """Analyzeert XBRL bestand om taxonomy versie requirements te bepalen"""
    try:
        logger.info(f"🔍 Starting taxonomy analysis request...")
        
        # Ensure upload folder exists
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        logger.info(f"📁 Upload folder ready: {UPLOAD_FOLDER}")
        
        if 'instance' not in request.files:
            logger.error("❌ No instance file in request")
            return jsonify({
                'success': False,
                'error': 'XBRL instance file is required'
            }), 400
        
        instance_file = request.files['instance']
        logger.info(f"📄 Received file: {instance_file.filename}")
        
        if instance_file.filename == '':
            logger.error("❌ Empty filename")
            return jsonify({
                'success': False, 
                'error': 'Invalid instance file'
            }), 400
        
        # Save file temporarily 
        from werkzeug.utils import secure_filename
        instance_filename = secure_filename(instance_file.filename)
        instance_path = os.path.join(UPLOAD_FOLDER, instance_filename)
        logger.info(f"💾 Saving to: {instance_path}")
        
        instance_file.save(instance_path)
        logger.info(f"✅ File saved successfully")
        
        # Analyze taxonomy requirements
        logger.info(f"🔍 Calling get_taxonomy_recommendations...")
        analysis_result = get_taxonomy_recommendations(instance_path)
        logger.info(f"📊 Analysis result type: {type(analysis_result)}")
        
        # Clean up temporary file
        try:
            os.remove(instance_path)
            logger.info(f"🗑️ Temporary file cleaned up")
        except Exception as cleanup_error:
            logger.warning(f"⚠️ Could not clean up temporary file: {cleanup_error}")
        
        if 'error' in analysis_result:
            logger.error(f"❌ Analysis returned error: {analysis_result['error']}")
            return jsonify({
                'success': False,
                'error': analysis_result['error'],
                'suggestions': analysis_result.get('suggestions', [])
            }), 400
        
        logger.info(f"✅ Taxonomy analysis completed: {analysis_result.get('detected_version', 'unknown')}")
        
        return jsonify({
            'success': True,
            'taxonomy_analysis': analysis_result
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Taxonomy analysis failed with exception: {e}")
        logger.error(f"Exception type: {type(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': f'Taxonomy analysis failed: {str(e)}'
        }), 500

@app.route("/validate-enhanced", methods=["POST"])
def validate_enhanced():
    """Enhanced validation with automatic architecture detection and hybrid validation"""
    logger.info("🚀 Hybrid validation endpoint called with architecture detection")
    
    try:
        if 'instance' not in request.files or 'taxonomy' not in request.files:
            return jsonify({
                'success': False,
                'error': 'Both instance and taxonomy files are required'
            }), 400
        
        instance_file = request.files['instance']
        taxonomy_file = request.files['taxonomy']
        table_code = request.form.get('table_code')
        
        if instance_file.filename == '' or taxonomy_file.filename == '':
            return jsonify({
                'success': False,
                'error': 'Invalid files provided'
            }), 400
        
        logger.info(f"Processing enhanced validation with dependency resolution: {instance_file.filename} + {taxonomy_file.filename}")
        if table_code:
            logger.info(f"Table code: {table_code}")
        
        # Use the hybrid validation system with architecture detection
        result = validate_files_core(instance_file, taxonomy_file, table_code, enhanced_mode=True)
        
        if result.get('success'):
            logger.info("✅ Enhanced validation with dependency resolution completed successfully")
            return jsonify(result), 200
        else:
            logger.error(f"❌ Enhanced validation failed: {result.get('error')}")
            return jsonify(result), 500
        
    except Exception as e:
        logger.error(f"Enhanced validation endpoint failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Enhanced validation failed: {str(e)}',
            'troubleshooting': 'Check file uploads, dependency availability, and validation system'
        }), 500

@app.route("/validate-dmp-direct", methods=["POST"])
def validate_dmp_direct():
    """FIXED: Enhanced DMP 4.0 direct validation with comprehensive dependency resolution"""
    logger.info("🚀 DMP 4.0 Direct validation endpoint called with dependency management")
    
    try:
        if 'instance' not in request.files:
            return jsonify({
                'success': False,
                'error': 'Instance file is required'
            }), 400
        
        instance_file = request.files['instance']
        validation_mode = request.form.get('validation_mode', 'comprehensive')
        table_code = request.form.get('table_code')
        
        if instance_file.filename == '':
            return jsonify({
                'success': False,
                'error': 'Invalid instance file'
            }), 400
        
        logger.info(f"Processing DMP 4.0 validation with dependency resolution: {instance_file.filename}")
        logger.info(f"Validation mode: {validation_mode}")
        logger.info(f"Expected: Missing concept resolution + comprehensive validation")
        if table_code:
            logger.info(f"Table code: {table_code}")
        
        # Use enhanced DMP 4.0 validation service with dependency resolution
        validator = DMPDirectValidator()
        result = validator.validate_dmp_direct(instance_file, validation_mode, table_code)
        
        if result.get('success'):
            logger.info("✅ DMP 4.0 validation with dependency resolution completed successfully")
            dmp_results = result.get('result', {}).get('dmpResults', [])
            logger.info(f"Generated {len(dmp_results)} DMP results")
            
            # CRITICAL FIX: Ensure dmpResults field is correctly named for frontend
            if 'result' in result and 'dmpResults' in result['result']:
                # Also add legacy field name for backward compatibility
                result['result']['dpmResults'] = result['result']['dmpResults']
                logger.info(f"✅ Added dpmResults field for frontend compatibility")
            
            return jsonify(result), 200
        else:
            logger.error(f"❌ DMP 4.0 validation failed: {result.get('error')}")
            return jsonify(result), 500
        
    except Exception as e:
        logger.error(f"DMP 4.0 validation endpoint failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Validation failed: {str(e)}',
            'troubleshooting': 'Check DMP 4.0 database connectivity, dependency availability, and file permissions'
        }), 500

@app.route("/debug/resolve-concept/<concept_code>", methods=["GET"])
def debug_resolve_concept(concept_code):
    """Debug endpoint to test concept resolution"""
    try:
        logger.info(f"🔍 DEBUG: Resolving concept {concept_code}")
        
        # Get detailed resolution info
        resolution = concept_resolver.resolve_concept_from_dmp(concept_code)
        
        # Also try Member table specifically
        member_results = dmp_db.queries_manager.search_member_concepts(concept_code, limit=5)
        
        # Get Member table stats
        member_stats = concept_resolver.get_member_statistics()
        
        debug_info = {
            "concept_code": concept_code,
            "resolution": resolution,
            "member_search_results": member_results,
            "member_table_stats": member_stats,
            "cache_hit": concept_code in concept_resolver.concept_cache,
            "search_strategies_used": [
                "exact_match",
                "clean_name",
                "prefix_variants", 
                "partial_match",
                "member_table",  # NEW
                "queries_manager"
            ]
        }
        
        if resolution:
            logger.info(f"✅ DEBUG: Successfully resolved {concept_code}")
        else:
            logger.warning(f"❌ DEBUG: Could not resolve {concept_code}")
            
        return jsonify(debug_info)
        
    except Exception as e:
        logger.error(f"Debug concept resolution failed: {e}")
        return jsonify({
            "concept_code": concept_code,
            "error": str(e),
            "resolution": None
        }), 500

@app.route("/validate-hybrid", methods=["POST"])
def validate_hybrid():
    """
    ENHANCED: Hybrid validation with dual architecture support
    
    Strategy:
    1. Auto-detect DPM architecture version (1.0 vs 2.0)
    2. Use correct DMP database and taxonomy for detected version
    3. Primary: Fast DMP database validation (concept resolution + rule checking)
    4. Secondary: Arelle validation with correct taxonomy (if provided)
    5. Synthesize results with architecture metadata
    """
    try:
        logger.info("🚀 Hybrid validation with dual architecture support")
        
        # Get uploaded files
        if 'instance' not in request.files:
            return jsonify({'success': False, 'error': 'Instance file is required'}), 400
        
        instance_file = request.files['instance']
        taxonomy_file = request.files.get('taxonomy')  # Optional for hybrid mode
        
        if instance_file.filename == '':
            return jsonify({'success': False, 'error': 'Instance file must have a valid filename'}), 400
        
        # Save instance file
        from werkzeug.utils import secure_filename
        instance_filename = secure_filename(instance_file.filename)
        instance_path = os.path.join(UPLOAD_FOLDER, instance_filename)
        instance_file.save(instance_path)
        
        # Auto-detect architecture version
        from hybrid_validation_engine import detect_architecture_version, HybridValidationEngine, ARCHITECTURES
        detected_architecture = detect_architecture_version(instance_path)
        
        if detected_architecture == 'unknown':
            logger.warning("⚠️ Architecture detection failed - defaulting to Architecture 2.0")
            detected_architecture = 'arch_2_0'
        
        logger.info(f"🎯 Detected architecture: {ARCHITECTURES[detected_architecture]['name']}")
        
        # Initialize engine with detected architecture
        hybrid_engine = HybridValidationEngine(
            architecture_version=detected_architecture,
            dmp_db_path=ARCHITECTURES[detected_architecture]['dmp_db_path']
        )
        
        # Save taxonomy file if provided
        taxonomy_path = None
        if taxonomy_file and taxonomy_file.filename:
            taxonomy_filename = secure_filename(taxonomy_file.filename)
            taxonomy_path = os.path.join(UPLOAD_FOLDER, taxonomy_filename)
            taxonomy_file.save(taxonomy_path)
            logger.info(f"📦 Taxonomy provided: {taxonomy_filename}")
        else:
            logger.info(f"📦 No taxonomy provided - will use {ARCHITECTURES[detected_architecture]['taxonomy_folder']} if needed")
        
        # Execute hybrid validation with architecture detection disabled (already detected)
        validation_results = hybrid_engine.validate_hybrid(
            instance_path, 
            taxonomy_path, 
            auto_detect_architecture=False
        )
        
        # Add processing metadata
        validation_results['metadata'] = {
            'validation_engine': 'Hybrid_Dual_Architecture_Engine_v2.1',
            'architecture_detected': ARCHITECTURES[detected_architecture]['name'],
            'files_processed': {
                'instance_file': instance_filename,
                'taxonomy_file': taxonomy_file.filename if taxonomy_file else f"Default: {ARCHITECTURES[detected_architecture]['taxonomy_folder']}"
            },
            'processing_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'backend_version': '2.1_dual_architecture'
        }
        
        # Log completion
        overall_status = validation_results.get('final_report', {}).get('overall_status', 'UNKNOWN')
        architecture = validation_results.get('architecture_version', 'unknown')
        logger.info(f"✅ Hybrid validation completed - Architecture: {architecture}, Status: {overall_status}")
        
        return jsonify({
            'success': True,
            'result': validation_results
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Hybrid validation failed: {e}")
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc(),
            'suggestion': 'Check XBRL instance format and DMP database availability for detected architecture'
        }), 500

@app.route("/resolve-concept", methods=["GET"])
def resolve_concept_endpoint():
    """Debug endpoint: /resolve-concept?q=eba_met:qCEF"""
    try:
        concept_query = request.args.get('q')
        if not concept_query:
            return jsonify({"success": False, "error": "Missing 'q' parameter"}), 400
        
        resolution = concept_resolver.resolve_concept_from_dmp(concept_query)
        
        return jsonify({
            "success": True,
            "concept_query": concept_query,
            "resolution": resolution,
            "resolved": resolution is not None
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/resolve-all", methods=["POST"])
def resolve_all_concepts():
    """Resolve all concepts from uploaded XBRL file"""
    try:
        if 'xbrlFile' not in request.files:
            return jsonify({"success": False, "error": "No XBRL file provided"}), 400
        
        xbrl_file = request.files['xbrlFile']
        
        import tempfile
        with tempfile.TemporaryDirectory() as temp_dir:
            xbrl_path = os.path.join(temp_dir, xbrl_file.filename)
            xbrl_file.save(xbrl_path)
            
            from fact_parser import XBRLFactParser
            parser = XBRLFactParser()
            parsing_result = parser.parse_xbrl_instance(xbrl_path)
            
            if 'error' in parsing_result:
                return jsonify({"success": False, "error": parsing_result['error']}), 400
            
            facts = parsing_result['facts']
            resolution_results = {}
            
            for fact_name in facts.keys():
                resolution = concept_resolver.resolve_concept_from_dmp(fact_name)
                resolution_results[fact_name] = {
                    'resolved': resolution is not None,
                    'resolution': resolution
                }
            
            total_facts = len(facts)
            resolved_facts = sum(1 for r in resolution_results.values() if r['resolved'])
            resolution_rate = (resolved_facts / total_facts * 100) if total_facts > 0 else 0
            
            return jsonify({
                "success": True,
                "file_name": xbrl_file.filename,
                "total_facts": total_facts,
                "resolved_facts": resolved_facts,
                "resolution_rate": f"{resolution_rate:.1f}%",
                "parsing_statistics": parsing_result.get('parsing_statistics', {}),
                "resolution_results": resolution_results
            })
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/debug/rule-engine", methods=["GET"])
def debug_rule_engine():
    """Debug endpoint for DMP rule engine status"""
    try:
        from rule_engine import DMPRuleEngine
        rule_engine = DMPRuleEngine()
        return jsonify({"success": True, "rule_engine_info": rule_engine.get_rule_engine_info()})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/debug/hybrid-engine-status", methods=["GET"])  
def debug_hybrid_engine_status():
    """Debug endpoint: Get comprehensive hybrid engine status for both architectures"""
    try:
        from hybrid_validation_engine import ARCHITECTURES, HybridValidationEngine
        
        status_report = {
            'architectures_available': {},
            'timestamp': datetime.now().isoformat()
        }
        
        # Test each architecture
        for arch_key, arch_config in ARCHITECTURES.items():
            try:
                # Test database availability
                db_available = os.path.exists(arch_config['dmp_db_path'])
                
                # Create temporary engine to test
                if db_available:
                    temp_engine = HybridValidationEngine(
                        architecture_version=arch_key,
                        dmp_db_path=arch_config['dmp_db_path']
                    )
                    engine_status = temp_engine.get_engine_status()
                    
                    status_report['architectures_available'][arch_key] = {
                        'name': arch_config['name'],
                        'database_path': arch_config['dmp_db_path'],
                        'database_available': db_available,
                        'taxonomy_folder': arch_config['taxonomy_folder'],
                        'engine_status': engine_status,
                        'status': 'available'
                    }
                else:
                    status_report['architectures_available'][arch_key] = {
                        'name': arch_config['name'],
                        'database_path': arch_config['dmp_db_path'],
                        'database_available': False,
                        'taxonomy_folder': arch_config['taxonomy_folder'],
                        'status': 'database_missing'
                    }
                    
            except Exception as arch_error:
                status_report['architectures_available'][arch_key] = {
                    'name': arch_config['name'],
                    'status': 'error',
                    'error': str(arch_error)
                }
        
        return jsonify({
            'success': True,
            'dual_architecture_status': status_report
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get hybrid engine status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route("/debug/member-table-info", methods=["GET"])
def debug_member_table_info():
    """Debug endpoint to check Member table availability and sample data"""
    try:
        stats = concept_resolver.get_member_statistics()
        
        # Try to find some EBA concepts
        test_concepts = ['qCEF', 'qFBB', 'qAOF', 'eba_met:qCEF', 'eba_met:qFBB']
        test_results = {}
        
        for concept in test_concepts:
            member_results = dmp_db.queries_manager.search_member_concepts(concept, limit=3)
            test_results[concept] = member_results
        
        return jsonify({
            "member_table_stats": stats,
            "test_concept_searches": test_results,
            "table_mappings": dmp_db.queries_manager.table_mappings
        })
        
    except Exception as e:
        logger.error(f"Member table debug failed: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # Print startup information
    print("🚀 Starting Enhanced XBRL Validation Server with DMP Integration")
    print(f"📁 Upload folder: {UPLOAD_FOLDER}")
    print(f"🗄️  Using database: {os.path.basename(dmp_db.db_path)}")
    
    # Test Arelle integration
    try:
        arelle_ok, arelle_msg = test_arelle_path()
        print(f"Arelle test: {'✓' if arelle_ok else '✗'} {arelle_msg}")
    except Exception as e:
        print(f"Arelle test: ✗ {str(e)}")
    
    # Test DMP database connection
    try:
        connection_status = dmp_db.test_connection()
        print(f"DMP Database: {'✓' if connection_status.get('connected') else '✗'} {connection_status.get('message', 'Unknown')}")
    except Exception as e:
        print(f"DMP Database: ✗ {str(e)}")
    
    # Test concept resolver
    try:
        stats = concept_resolver.get_concept_statistics() 
        print(f"Concept Resolver: {'✓' if not stats.get('error') else '✗'} {stats}")
    except Exception as e:
        print(f"Concept Resolver: ✗ {str(e)}")
    
    # Test dependency management
    try:
        dependency_manager = EBATaxonomyDependencyManager()
        available_packages = dependency_manager.get_available_packages()
        dependency_status = len(available_packages) > 0
        print(f"Dependency Management: {'✓' if dependency_status else '⚠️'} {len(available_packages)} packages available")
        if not dependency_status:
            print("💡 Missing packages will be detected during validation with download instructions")
    except Exception as e:
        print(f"Dependency Management: ✗ {str(e)}")
    
    print("🎯 Server optimized for comprehensive XBRL validation")
    print("📊 Enhanced features: ValidationRules, dependency resolution, missing concept detection, DMP version compatibility")
    print("🆕 Endpoints: /dmp/status, /dmp/dependencies, /validate-dmp-direct, /validate-enhanced, /validation-modes, /debug/*")
    print("🔄 NEW: /debug/dmp-compatibility - Test DMP version compatibility")
    print("🔄 NEW: /debug/concept-resolution - Test DMP concept resolution for XBRL concepts")
    print("🔄 NEW: /debug/comprehensive-validation-test - Test the new comprehensive validation system")
    print("🔄 NEW: /debug/taxonomy-verification - Verify taxonomy contents and concept availability")
    print("🔄 NEW: /debug/resolve-concept/<concept_code> - Debug endpoint to test concept resolution")
    print("🔄 NEW: /debug/member-table-info - Debug endpoint to check Member table availability and sample data")
    print("🔄 NEW: /analyze-taxonomy-requirements - Analyze XBRL files for taxonomy version requirements")
    app.run(debug=True, port=5000, threaded=True)
