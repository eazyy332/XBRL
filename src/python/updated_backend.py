
import json
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import subprocess
import os
import xml.etree.ElementTree as ET
import zipfile
import time

# ✔️ Pad naar Arelle CLI - Updated path handling
ARELLE_PATH = r"C:\Users\berbe\Documents\AI\XBRL-validation\Arella\arella\Arelle\arelleCmdLine.exe"

# ✔️ Flask setup
app = Flask(__name__)
CORS(app)

# ✔️ Validation rules (optioneel)
try:
    with open("finrep_validation_rules.json", "r", encoding="utf-8") as f:
        FINREP_RULES = {entry["rule_id"]: entry for entry in json.load(f)}
except Exception:
    FINREP_RULES = {}

# ✔️ Cell mapping
try:
    with open("xbrl_cell_mappings.json", "r", encoding="utf-8") as f:
        CELL_MAPPING = json.load(f)
except Exception:
    CELL_MAPPING = []

@app.route("/health", methods=["GET"])
def health():
    return "OK", 200

def test_arelle_path():
    """Test if Arelle executable is accessible"""
    try:
        if not os.path.exists(ARELLE_PATH):
            return False, f"Arelle executable not found at: {ARELLE_PATH}"
        
        # Test Arelle with --help command
        result = subprocess.run([ARELLE_PATH, "--help"], 
                              stdout=subprocess.PIPE, 
                              stderr=subprocess.PIPE, 
                              text=True, 
                              timeout=10)
        
        if result.returncode == 0:
            return True, "Arelle is accessible"
        else:
            return False, f"Arelle test failed: {result.stderr}"
    except Exception as e:
        return False, f"Arelle test error: {str(e)}"

@app.route("/validate-enhanced", methods=["POST"])
def validate_enhanced():
    """Enhanced validation endpoint that matches frontend expectations"""
    try:
        start_time = time.time()
        
        # Check if required files are present
        if 'instance' not in request.files or 'taxonomy' not in request.files:
            return jsonify({
                'success': False,
                'error': 'Both instance and taxonomy files are required'
            }), 400

        instance_file = request.files["instance"]
        taxonomy_file = request.files["taxonomy"]

        # Test Arelle first
        arelle_ok, arelle_msg = test_arelle_path()
        if not arelle_ok:
            return jsonify({
                'success': False,
                'error': f'Arelle validation failed: {arelle_msg}',
                'troubleshooting': 'Please check Arelle installation path and permissions'
            }), 500

        os.makedirs("uploads", exist_ok=True)
        instance_path = os.path.join("uploads", instance_file.filename)
        taxonomy_path = os.path.join("uploads", taxonomy_file.filename)

        instance_file.save(instance_path)
        taxonomy_file.save(taxonomy_path)

        print(f"Processing files: {instance_path}, {taxonomy_path}")
        
        annotations = extract_annotations(taxonomy_path)

        # ✔️ Enhanced Arelle validation with timeout
        try:
            result = subprocess.run(
                [
                    ARELLE_PATH,
                    "--file", instance_path,
                    "--package", taxonomy_path,
                    "--validate",
                    "--logLevel", "info"
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=180  # 3 minutes timeout
            )
            
            print(f"Arelle return code: {result.returncode}")
            print(f"Arelle stdout: {result.stdout[:500]}...")
            print(f"Arelle stderr: {result.stderr[:500]}...")
            
        except subprocess.TimeoutExpired:
            return jsonify({
                'success': False,
                'error': 'Validation timeout after 3 minutes',
                'troubleshooting': 'Large files may require more processing time'
            }), 500
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Arelle execution failed: {str(e)}',
                'troubleshooting': 'Check Arelle path and file permissions'
            }), 500

        stdout_lines = result.stdout.strip().splitlines()
        stderr_lines = result.stderr.strip().splitlines()
        all_output = stdout_lines + stderr_lines

        # Enhanced DPM results processing
        dmp_results = []
        validation_stats = {
            'totalRules': 0,
            'passedRules': 0,
            'failedRules': 0,
            'formulasChecked': 0,
            'dimensionsValidated': 0
        }

        for line in all_output:
            if any(keyword in line.lower() for keyword in ["rule", "assertion", "formula", "error", "warning"]):
                concept = extract_concept_from_line(line)
                rule = extract_rule_from_line(line)
                
                # Determine status and severity
                is_error = any(err in line.lower() for err in ["error", "failed", "violation", "inconsistent"])
                is_warning = "warning" in line.lower()
                
                status = "Failed" if is_error else "Passed"
                severity = "error" if is_error else ("warning" if is_warning else "info")
                
                # Classify rule type
                rule_type = classify_rule_type(line)
                
                enriched = enrich_with_cell_mapping(concept)
                
                dmp_result = {
                    "concept": concept,
                    "rule": rule,
                    "status": status,
                    "message": line.strip(),
                    "annotation": annotations.get(concept, f"EBA validation rule for {concept}"),
                    "ruleType": rule_type,
                    "severity": severity,
                    **enriched
                }
                
                dmp_results.append(dmp_result)
                validation_stats['totalRules'] += 1
                
                if status == "Failed":
                    validation_stats['failedRules'] += 1
                else:
                    validation_stats['passedRules'] += 1
                    
                if rule_type == 'formula':
                    validation_stats['formulasChecked'] += 1
                elif rule_type == 'dimensional':
                    validation_stats['dimensionsValidated'] += 1

        # If no specific rules found, add general validation results
        if not dmp_results:
            has_errors = result.returncode != 0 or any("error" in line.lower() for line in all_output)
            
            dmp_results.append({
                "concept": "general",
                "rule": "XBRL-VALIDATION",
                "status": "Failed" if has_errors else "Passed", 
                "message": "General XBRL structure and taxonomy validation",
                "annotation": "Overall file validation using Arelle engine",
                "ruleType": "consistency",
                "severity": "error" if has_errors else "info"
            })
            
            validation_stats['totalRules'] = 1
            if has_errors:
                validation_stats['failedRules'] = 1
            else:
                validation_stats['passedRules'] = 1

        processing_time = time.time() - start_time
        is_valid = validation_stats['failedRules'] == 0

        return jsonify({
            'success': True,
            'status': 'valid' if is_valid else 'invalid',
            'result': {
                'isValid': is_valid,
                'status': 'valid' if is_valid else 'invalid',
                'errors': [
                    {
                        'message': r['message'],
                        'severity': r['severity'],
                        'code': r['rule'],
                        'concept': r['concept'],
                        'documentation': r['annotation']
                    }
                    for r in dmp_results if r['status'] == 'Failed'
                ],
                'dmpResults': dmp_results,  # Note: keeping original name for compatibility
                'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                'filesProcessed': {
                    'instanceFile': instance_file.filename,
                    'taxonomyFile': taxonomy_file.filename
                },
                'validationStats': validation_stats
            },
            'processingTime': processing_time,
            'validationEngine': 'Arelle with EBA Rules'
        }), 200

    except Exception as e:
        print("ENHANCED VALIDATION ERROR:", str(e))
        return jsonify({
            'success': False,
            'error': f'Enhanced validation failed: {str(e)}',
            'troubleshooting': 'Check file uploads and Arelle configuration'
        }), 500

@app.route("/validate", methods=["POST"])
def validate():
    """Original validation endpoint - kept for backward compatibility"""
    try:
        instance_file = request.files["instance"]
        taxonomy_file = request.files["taxonomy"]

        os.makedirs("uploads", exist_ok=True)
        instance_path = os.path.join("uploads", instance_file.filename)
        taxonomy_path = os.path.join("uploads", taxonomy_file.filename)

        instance_file.save(instance_path)
        taxonomy_file.save(taxonomy_path)

        annotations = extract_annotations(taxonomy_path)

        # Test Arelle first
        arelle_ok, arelle_msg = test_arelle_path()
        if not arelle_ok:
            return jsonify({
                "status": "invalid",
                "error": arelle_msg,
                "dmpResults": []
            }), 200

        # ✔️ Start Arelle validatie
        result = subprocess.run(
            [
                ARELLE_PATH,
                "--file", instance_path,
                "--package", taxonomy_path,
                "--validate"
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=120
        )

        stdout_lines = result.stdout.strip().splitlines()
        stderr_lines = result.stderr.strip().splitlines()
        all_output = stdout_lines + stderr_lines

        concept_results = []
        for line in all_output:
            if "rule" in line.lower() or "assertion" in line.lower():
                concept = extract_concept_from_line(line)
                rule = extract_rule_from_line(line)
                status = "failed" if any(err in line.lower() for err in ["error", "failed", "violation"]) else "passed"

                enriched = enrich_with_cell_mapping(concept)
                concept_results.append({
                    "concept": concept,
                    "rule": rule,
                    "status": status,
                    "message": line,
                    "annotation": annotations.get(concept, ""),
                    **enriched
                })

        return jsonify({
            "status": "invalid" if any(r["status"] == "failed" for r in concept_results) else "valid",
            "dmpResults": concept_results
        }), 200

    except subprocess.TimeoutExpired:
        return jsonify({
            "status": "invalid",
            "error": "Validation timeout",
            "dmpResults": []
        }), 200
    except Exception as e:
        print("BACKEND ERROR:", str(e))
        return jsonify({
            "status": "invalid", 
            "error": str(e),
            "dmpResults": []
        }), 200

def classify_rule_type(message):
    """Classify validation rule type based on message content"""
    message_lower = message.lower()
    
    if any(keyword in message_lower for keyword in ['formula', 'calculation', 'sum', 'total']):
        return 'formula'
    elif any(keyword in message_lower for keyword in ['dimension', 'member', 'domain', 'hypercube']):
        return 'dimensional'
    elif any(keyword in message_lower for keyword in ['required', 'mandatory', 'missing', 'completeness']):
        return 'completeness'
    else:
        return 'consistency'

@app.route("/annotate", methods=["POST"])
def annotate_xbrl():
    try:
        instance_file = request.files["instance"]
        original_path = os.path.join("uploads", instance_file.filename)
        annotated_path = os.path.join("uploads", "annotated-instance.xbrl")

        os.makedirs("uploads", exist_ok=True)
        instance_file.save(original_path)

        with open(original_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        annotated_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("<") and ":" in stripped and "contextRef" in stripped:
                concept = extract_concept_from_line(line)
                mapping = enrich_with_cell_mapping(concept)
                if mapping.get("table") and mapping.get("rowCode") and mapping.get("columnCode"):
                    comment = f"<!-- Datapoint {mapping['table']}.row_{mapping['rowCode']}.col_{mapping['columnCode']} -->"
                    annotated_lines.append(comment + "\n")
            annotated_lines.append(line)

        with open(annotated_path, "w", encoding="utf-8") as f:
            f.writelines(annotated_lines)

        return jsonify({
            "success": True,
            "downloadUrl": "http://localhost:5000/download/annotated-instance.xbrl"
        }), 200

    except Exception as e:
        print("ANNOTATE ERROR:", str(e))
        return jsonify({"success": False, "error": f"Annotatie mislukt: {str(e)}"}), 500

@app.route("/download/<path:filename>")
def download_file(filename):
    return send_file(os.path.join("uploads", filename), as_attachment=True)

# ✔️ Helpers
def enrich_with_cell_mapping(concept):
    for row in CELL_MAPPING:
        if row.get("cellCode") == concept or row.get("dataPointID") == concept:
            return {
                "cellCode": row.get("cellCode"),
                "table": row.get("table"),
                "rowCode": row.get("rowCode"),
                "rowLabel": row.get("rowLabel"),
                "columnCode": row.get("columnCode"),
                "columnLabel": row.get("columnLabel")
            }
    return {}

def extract_annotations(taxonomy_zip_path):
    annotations = {}
    try:
        with zipfile.ZipFile(taxonomy_zip_path, 'r') as zip_ref:
            zip_ref.extractall("temp_taxonomy")

        for root_dir, _, files in os.walk("temp_taxonomy"):
            for file in files:
                if file.endswith(".xml"):
                    file_path = os.path.join(root_dir, file)
                    try:
                        tree = ET.parse(file_path)
                        root = tree.getroot()
                        for elem in root.iter():
                            if "label" in elem.tag.lower() and elem.text:
                                annotations[elem.text.strip()] = elem.attrib.get("id", "")
                    except Exception:
                        continue
    except Exception:
        pass

    return annotations

def extract_concept_from_line(line):
    for word in line.split():
        if ":" in word and len(word.split(":")[-1]) > 2:
            return word.strip("[]:,()")
    return "unknown"

def extract_rule_from_line(line):
    for word in line.split():
        if "rule" in word.lower() or "eba:" in word.lower() or "esma:" in word.lower():
            return word.strip("[]:,()")
    return "unknown"

if __name__ == "__main__":
    print("Starting Flask server...")
    print(f"Arelle path: {ARELLE_PATH}")
    arelle_ok, arelle_msg = test_arelle_path()
    print(f"Arelle test: {'✓' if arelle_ok else '✗'} {arelle_msg}")
    app.run(debug=True, port=5000)
