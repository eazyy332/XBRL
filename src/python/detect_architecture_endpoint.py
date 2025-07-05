"""
Architecture Detection Endpoint
===============================
Standalone endpoint for detecting EBA DPM architecture version from XBRL files.
Useful for debugging and testing architecture detection logic.
"""

import os
import logging
from flask import request, jsonify
from werkzeug.utils import secure_filename
from hybrid_validation_engine import detect_architecture_version, ARCHITECTURES

logger = logging.getLogger(__name__)

def register_detect_architecture_routes(app, upload_folder):
    """Register architecture detection routes"""
    
    @app.route("/detect-architecture", methods=["POST"])
    def detect_architecture():
        """
        Debug endpoint: Detect DPM architecture version from uploaded XBRL instance
        
        Returns detailed information about:
        - Detected architecture version
        - Namespaces found in XBRL file
        - Database and taxonomy paths for detected version
        - Architecture comparison table
        """
        try:
            logger.info("🔍 Architecture detection request received")
            
            # Check for uploaded file
            if 'instance' not in request.files:
                return jsonify({
                    'success': False,
                    'error': 'Instance file is required for architecture detection'
                }), 400
            
            instance_file = request.files['instance']
            
            if instance_file.filename == '':
                return jsonify({
                    'success': False,
                    'error': 'Instance file must have a valid filename'
                }), 400
            
            # Save file temporarily
            instance_filename = secure_filename(instance_file.filename)
            instance_path = os.path.join(upload_folder, instance_filename)
            instance_file.save(instance_path)
            
            # Detect architecture
            detected_version = detect_architecture_version(instance_path)
            
            # Get detailed namespace information
            import xml.etree.ElementTree as ET
            try:
                tree = ET.parse(instance_path)
                root = tree.getroot()
                
                # Extract all namespaces
                namespaces = {}
                for key, value in root.attrib.items():
                    if key.startswith('xmlns:'):
                        prefix = key.replace('xmlns:', '')
                        namespaces[prefix] = value
                    elif key == 'xmlns':
                        namespaces['default'] = value
                
            except Exception as ns_error:
                namespaces = {'error': f"Failed to parse namespaces: {ns_error}"}
            
            # Build response
            detection_result = {
                'success': True,
                'file_info': {
                    'filename': instance_filename,
                    'file_size': os.path.getsize(instance_path)
                },
                'detection_result': {
                    'detected_architecture': detected_version,
                    'architecture_name': ARCHITECTURES.get(detected_version, {}).get('name', 'Unknown'),
                    'confidence': 'high' if detected_version != 'unknown' else 'none'
                },
                'namespaces_found': namespaces,
                'architecture_details': {}
            }
            
            # Add details for each architecture
            for arch_key, arch_config in ARCHITECTURES.items():
                detection_result['architecture_details'][arch_key] = {
                    'name': arch_config['name'],
                    'expected_namespaces': arch_config['namespaces'],
                    'database_path': arch_config['dmp_db_path'],
                    'database_exists': os.path.exists(arch_config['dmp_db_path']),
                    'taxonomy_folder': arch_config['taxonomy_folder'],
                    'selected': arch_key == detected_version
                }
            
            # Add recommendation
            if detected_version != 'unknown':
                config = ARCHITECTURES[detected_version]
                detection_result['recommendation'] = {
                    'message': f"Use {config['name']} for validation",
                    'database_file': os.path.basename(config['dmp_db_path']),
                    'taxonomy_folder': config['taxonomy_folder']
                }
            else:
                detection_result['recommendation'] = {
                    'message': "Architecture could not be detected - consider using Architecture 2.0 as default",
                    'suggestion': "Check if XBRL file contains standard EBA namespaces"
                }
            
            logger.info(f"✅ Architecture detection completed: {detected_version}")
            
            # Clean up temporary file
            try:
                os.remove(instance_path)
            except:
                pass
            
            return jsonify(detection_result), 200
            
        except Exception as e:
            logger.error(f"❌ Architecture detection failed: {e}")
            
            # Clean up on error
            try:
                if 'instance_path' in locals():
                    os.remove(instance_path)
            except:
                pass
            
            return jsonify({
                'success': False,
                'error': str(e),
                'suggestion': 'Ensure XBRL file is valid and contains standard namespaces'
            }), 500
    
    @app.route("/architectures", methods=["GET"])
    def list_architectures():
        """
        List all supported DPM architectures with availability status
        """
        try:
            architectures_info = {
                'supported_architectures': {},
                'total_architectures': len(ARCHITECTURES)
            }
            
            for arch_key, arch_config in ARCHITECTURES.items():
                architectures_info['supported_architectures'][arch_key] = {
                    'name': arch_config['name'],
                    'database_path': arch_config['dmp_db_path'],
                    'database_available': os.path.exists(arch_config['dmp_db_path']),
                    'taxonomy_folder': arch_config['taxonomy_folder'],
                    'detection_namespaces': arch_config['namespaces']
                }
            
            return jsonify({
                'success': True,
                'architectures': architectures_info
            }), 200
            
        except Exception as e:
            logger.error(f"Failed to list architectures: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500