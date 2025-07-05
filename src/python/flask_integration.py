
"""
Flask integration module for XBRL error enrichment.
Add this to your existing Flask server to enable error enrichment.
"""

from flask import Flask, request, jsonify
from xbrl_error_enricher import enrich_validation_errors, XBRLErrorEnricher
import json

def add_enrichment_routes(app: Flask):
    """
    Add enrichment routes to existing Flask app.
    Call this function in your main Flask server file.
    """
    
    @app.route('/enrich-errors', methods=['POST'])
    def enrich_errors_endpoint():
        """
        Endpoint to enrich validation errors.
        Expects validation result JSON in request body.
        """
        try:
            validation_result = request.get_json()
            
            if not validation_result:
                return jsonify({
                    'success': False,
                    'error': 'No validation result provided'
                }), 400
            
            # Enrich the validation result
            enriched_result = enrich_validation_errors(validation_result)
            
            return jsonify({
                'success': True,
                'result': enriched_result
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Error enriching validation result: {str(e)}'
            }), 500

    @app.route('/validate-enriched', methods=['POST'])
    def validate_with_enrichment():
        """
        Combined validation and enrichment endpoint.
        Performs validation and immediately enriches errors.
        """
        try:
            # Get uploaded files
            if 'instance' not in request.files or 'taxonomy' not in request.files:
                return jsonify({
                    'success': False,
                    'error': 'Both instance and taxonomy files are required'
                }), 400
            
            instance_file = request.files['instance']
            taxonomy_file = request.files['taxonomy']
            
            # Here you would call your existing validation logic
            # For now, this is a placeholder that shows the integration pattern
            
            # TODO: Replace this with your actual XBRL validation logic
            # validation_result = your_xbrl_validator.validate(instance_file, taxonomy_file)
            
            # Sample validation result for demonstration
            sample_validation_result = {
                'isValid': False,
                'errors': [
                    {
                        'message': f'Context reference error in {instance_file.filename}',
                        'line': 42,
                        'column': 15,
                        'severity': 'error',
                        'xpath': '//finrep:Assets[@contextRef="ctx_F-01.01_2023"]'
                    }
                ],
                'filesProcessed': {
                    'instanceFile': instance_file.filename,
                    'taxonomyFile': taxonomy_file.filename
                }
            }
            
            # Enrich the validation result
            enriched_result = enrich_validation_errors(sample_validation_result)
            
            return jsonify({
                'success': True,
                'status': enriched_result['status'],
                'result': enriched_result
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Validation with enrichment failed: {str(e)}'
            }), 500


# Example of how to integrate with your existing server
def integrate_with_existing_server():
    """
    Example integration code - add this to your xbrl_generator_server.py
    """
    integration_code = '''
# Add this import at the top of your xbrl_generator_server.py
from flask_integration import add_enrichment_routes

# Add this line after creating your Flask app
app = Flask(__name__)
add_enrichment_routes(app)  # Add this line

# Your existing routes continue as normal...
'''
    
    print("Integration code:")
    print(integration_code)


if __name__ == "__main__":
    integrate_with_existing_server()
