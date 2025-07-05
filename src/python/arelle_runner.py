"""
Arelle Integration Module
========================
Handles Arelle-based XBRL validation as fallback strategy.
Includes taxonomy ZIP processing, caching, and offline support.
"""

import logging
import subprocess
import os
import zipfile
import tempfile
import shutil
from typing import Dict, Any, Optional, List
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class ArelleRunner:
    """
    Manages Arelle validation as fallback strategy with enhanced features:
    - Automatic taxonomy ZIP extraction
    - Validation caching
    - Offline mode support
    - Enhanced error parsing
    """
    
    def __init__(self):
        self.cache_dir = os.path.join(tempfile.gettempdir(), 'arelle_cache')
        self.taxonomy_cache_dir = os.path.join(self.cache_dir, 'taxonomies')
        self.result_cache_dir = os.path.join(self.cache_dir, 'results')
        
        # Create cache directories
        os.makedirs(self.taxonomy_cache_dir, exist_ok=True)
        os.makedirs(self.result_cache_dir, exist_ok=True)
        
        # Check Arelle availability
        self.arelle_available = self._check_arelle_installation()
        logger.info(f"🔧 Arelle runner initialized - Available: {self.arelle_available}")
    
    def _check_arelle_installation(self) -> bool:
        """Check if Arelle is properly installed and accessible"""
        try:
            # Try module approach first
            result = subprocess.run(
                ['python', '-m', 'arelle.CmdLine', '--help'], 
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                logger.info("✅ Arelle available via python module")
                return True
        except Exception as e:
            logger.warning(f"Module check failed: {e}")
        
        # Fallback: Use existing arelle_core.py infrastructure
        try:
            from config import ARELLE_PATH
            from arelle_core import test_arelle_path
            success, message = test_arelle_path()
            if success:
                logger.info(f"✅ Arelle available via arelle_core: {message}")
                self.arelle_executable = ARELLE_PATH  # Store for later use
                return True
            else:
                logger.warning(f"Arelle test failed: {message}")
        except Exception as e:
            logger.warning(f"Arelle core check failed: {e}")
        
        return False
    
    def validate_with_arelle(self, xbrl_path: str, taxonomy_path: str) -> Dict[str, Any]:
        """
        Execute Arelle validation with enhanced taxonomy processing
        
        Args:
            xbrl_path: Path to XBRL instance file
            taxonomy_path: Path to taxonomy file or ZIP
            
        Returns:
            Comprehensive Arelle validation results
        """
        
        if not self.arelle_available:
            return {
                'method': 'arelle_fallback',
                'status': 'unavailable',
                'message': 'Arelle is not installed or accessible'
            }
        
        try:
            validation_result = {
                'method': 'arelle_fallback',
                'status': 'running',
                'timestamp': datetime.now().isoformat(),
                'files': {
                    'xbrl_file': os.path.basename(xbrl_path),
                    'taxonomy_file': os.path.basename(taxonomy_path)
                }
            }
            
            # STEP 1: Process taxonomy (extract if ZIP)
            logger.info(f"📦 Processing taxonomy: {os.path.basename(taxonomy_path)}")
            processed_taxonomy = self._process_taxonomy(taxonomy_path)
            
            if not processed_taxonomy['success']:
                validation_result['status'] = 'error'
                validation_result['error'] = processed_taxonomy['error']
                return validation_result
            
            taxonomy_entry_point = processed_taxonomy['entry_point']
            validation_result['taxonomy_processing'] = processed_taxonomy
            
            # STEP 2: Check cache for existing results
            cache_key = self._generate_cache_key(xbrl_path, taxonomy_entry_point)
            cached_result = self._get_cached_result(cache_key)
            
            if cached_result:
                logger.info("💾 Using cached Arelle validation result")
                cached_result['cache_hit'] = True
                return cached_result
            
            # STEP 3: Execute Arelle validation
            logger.info("🔍 Executing Arelle validation...")
            arelle_result = self._execute_arelle_validation(xbrl_path, taxonomy_entry_point)
            validation_result.update(arelle_result)
            
            # STEP 4: Cache results for future use
            if validation_result.get('status') == 'completed':
                self._cache_result(cache_key, validation_result)
            
            return validation_result
            
        except Exception as e:
            logger.error(f"❌ Arelle validation failed: {e}")
            return {
                'method': 'arelle_fallback',
                'status': 'error',
                'error': str(e)
            }
    
    def _process_taxonomy(self, taxonomy_path: str) -> Dict[str, Any]:
        """
        Process taxonomy file - extract ZIP if needed, validate structure
        
        Returns:
            Dictionary with processing results and entry point
        """
        
        try:
            result = {
                'success': False,
                'original_path': taxonomy_path,
                'is_zip': False,
                'entry_point': None,
                'extraction_path': None
            }
            
            # Check if taxonomy is a ZIP file
            if taxonomy_path.lower().endswith('.zip'):
                result['is_zip'] = True
                logger.info("📂 Extracting taxonomy ZIP file...")
                
                # Create extraction directory
                extraction_dir = os.path.join(self.taxonomy_cache_dir, 
                                            f"taxonomy_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
                os.makedirs(extraction_dir, exist_ok=True)
                
                # Extract ZIP
                with zipfile.ZipFile(taxonomy_path, 'r') as zip_ref:
                    zip_ref.extractall(extraction_dir)
                
                result['extraction_path'] = extraction_dir
                
                # Find entry point (look for main taxonomy files)
                entry_point = self._find_taxonomy_entry_point(extraction_dir)
                if not entry_point:
                    result['error'] = "Could not find taxonomy entry point in ZIP"
                    return result
                
                result['entry_point'] = entry_point
                result['success'] = True
                
                logger.info(f"✅ Taxonomy extracted - Entry point: {os.path.basename(entry_point)}")
                
            else:
                # Direct taxonomy file
                if os.path.exists(taxonomy_path):
                    result['entry_point'] = taxonomy_path
                    result['success'] = True
                else:
                    result['error'] = f"Taxonomy file not found: {taxonomy_path}"
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Taxonomy processing failed: {str(e)}"
            }
    
    def _find_taxonomy_entry_point(self, taxonomy_dir: str) -> Optional[str]:
        """
        Find the correct EBA FINREP entry point for the XBRL instance
        PRIORITY: Look for FINREP GAAP specific entry points first
        """
        
        import glob
        
        # Ensure directory has proper permissions
        self._ensure_directory_permissions(taxonomy_dir)
        
        # PRIORITY 1: Look for FINREP GAAP specific entry points first
        finrep_patterns = [
            '**/finrep*gaap*.xsd',          # FINREP GAAP specific schemas (HIGHEST PRIORITY)
            '**/finrep*.xsd',               # Any FINREP schemas
            '**/met.xsd',                   # Metadata entry points
            '**/dim.xsd',                   # Dimension entry points
            '**/eba_met.xsd'                # EBA metadata schema
        ]
        
        for pattern in finrep_patterns:
            matches = glob.glob(os.path.join(taxonomy_dir, pattern), recursive=True)
            if matches:
                logger.info(f"📁 Found EBA FINREP entry point: {os.path.basename(matches[0])}")
                return matches[0]
        
        # PRIORITY 2: Fallback - try to find any EBA-related XSD
        logger.info("🔍 Searching for fallback EBA schemas...")
        all_xsd = glob.glob(os.path.join(taxonomy_dir, '**/*.xsd'), recursive=True)
        eba_xsd = [f for f in all_xsd if 'eba' in f.lower() or 'finrep' in f.lower()]
        
        if eba_xsd:
            logger.info(f"📁 Found fallback EBA schema: {os.path.basename(eba_xsd[0])}")
            return eba_xsd[0]
        
        # PRIORITY 3: Last resort - use taxonomy directory itself
        logger.warning(f"⚠️ Using taxonomy directory as entry point: {taxonomy_dir}")
        return taxonomy_dir
    
    def _execute_arelle_validation(self, xbrl_path: str, taxonomy_entry_point: str) -> Dict[str, Any]:
        """Execute the actual Arelle validation command with FIXED parameter syntax"""
        
        try:
            # STEP 1-3: Build MINIMAL working Arelle command for EBA FINREP validation
            base_cmd = []
            
            if hasattr(self, 'arelle_executable'):
                # Use direct executable path (arelle_core.py approach)
                base_cmd = [self.arelle_executable]
            else:
                # Use module approach
                base_cmd = ['python', '-m', 'arelle.CmdLine']
            
            # FIXED COMMAND - Use OFFLINE mode with local taxonomy cache
            cmd = base_cmd + [
                '--file', xbrl_path,
                '--import', taxonomy_entry_point,
                '--validate',
                '--plugins', 'validate/EBA',
                '--disclosureSystem', 'eba',
                '--internetConnectivity', 'offline',  # OFFLINE to force local files
                '--utrUrl', '',  # Disable external UTR lookups
                '--logLevel', 'INFO',
                '--logFormat', '[%(levelname)s] %(message)s'
            ]
            
            # DEBUG: Verifieer dat 'online' echt in command staat
            cmd_str = ' '.join(cmd)
            if 'offline' in cmd_str:
                logger.error("❌ STILL USING OFFLINE MODE!")
            if 'online' in cmd_str:
                logger.info("✅ Using online mode correctly")
            
            # ENHANCED CONNECTIVITY - Allow online access for EBA schemas
            # This enables downloading missing schemas from EBA website
            logger.info("🌐 Enhanced Arelle command - allowing online schema downloads for EBA")
            
            logger.info("🌐 Enhanced Arelle command - allowing online schema downloads")
            
            logger.info(f"🔧 Arelle command: {' '.join(cmd)}")
            
            # Execute with timeout
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            # Parse Arelle output
            parsed_output = self._parse_arelle_output(result.stdout, result.stderr, result.returncode)
            
            arelle_result = {
                'status': 'completed',
                'return_code': result.returncode,
                'execution_time': datetime.now().isoformat(),
                'validation_successful': result.returncode == 0,
                **parsed_output
            }
            
            logger.info(f"✅ Arelle completed - Return code: {result.returncode}, "
                       f"Errors: {len(arelle_result.get('errors', []))}, "
                       f"Warnings: {len(arelle_result.get('warnings', []))}")
            
            return arelle_result
            
        except subprocess.TimeoutExpired:
            logger.error("❌ Arelle validation timed out after 120 seconds")
            return {
                'status': 'timeout',
                'error': 'Arelle validation timed out after 120 seconds'
            }
        except Exception as e:
            logger.error(f"❌ Arelle execution failed: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _parse_arelle_output(self, stdout: str, stderr: str, return_code: int) -> Dict[str, Any]:
        """
        Enhanced Arelle output parser to extract EBA FINREP business rule results
        
        Returns:
            Structured validation results with errors, warnings, and business rule insights
        """
        
        combined_output = stdout + stderr
        lines = combined_output.split('\n')
        
        errors = []
        warnings = []
        info_messages = []
        business_rules_processed = 0
        
        # Enhanced categories for EBA FINREP business rules
        error_categories = {}
        warning_categories = {}
        business_rule_patterns = [
            'eba_v', 'eba_validation', 'business rule', 'finrep', 'corep', 
            'calculation', 'formula', 'constraint', 'consistency'
        ]
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # ENHANCED: Detect business rule processing
            if any(pattern in line.lower() for pattern in business_rule_patterns):
                business_rules_processed += 1
                logger.debug(f"🔍 Business rule detected: {line[:100]}...")
            
            # Parse different message types with enhanced patterns
            if any(keyword in line.upper() for keyword in ['[ERROR]', 'ERROR:', 'EXCEPTION', 'FATAL']):
                error_info = self._categorize_arelle_message(line, 'error')
                errors.append(error_info)
                
                category = error_info.get('category', 'general')
                error_categories[category] = error_categories.get(category, 0) + 1
                
            elif any(keyword in line.upper() for keyword in ['[WARNING]', 'WARNING:', 'INCONSISTENCY']):
                warning_info = self._categorize_arelle_message(line, 'warning')
                warnings.append(warning_info)
                
                category = warning_info.get('category', 'general')
                warning_categories[category] = warning_categories.get(category, 0) + 1
                
            elif any(keyword in line.upper() for keyword in ['[INFO]', 'INFO:', 'VALIDATION']):
                info_messages.append(line)
                # Extract business rule information from INFO messages
                if any(pattern in line.lower() for pattern in ['rule', 'validation', 'check']):
                    logger.debug(f"📋 Validation info: {line}")
        
        # Enhanced summary with business rule detection
        summary = {
            'total_errors': len(errors),
            'total_warnings': len(warnings),
            'business_rules_detected': business_rules_processed,
            'error_categories': error_categories,
            'warning_categories': warning_categories,
            'validation_passed': return_code == 0 and len(errors) == 0,
            'return_code': return_code
        }
        
        # Log enhanced results for debugging
        logger.info(f"📊 Enhanced Arelle parsing results:")
        logger.info(f"   🔴 Errors: {len(errors)}")
        logger.info(f"   🟡 Warnings: {len(warnings)}")
        logger.info(f"   📋 Business rules detected: {business_rules_processed}")
        logger.info(f"   📄 Info messages: {len(info_messages)}")
        logger.info(f"   🎯 Return code: {return_code}")
        
        return {
            'errors': errors,
            'warnings': warnings,
            'info_messages': info_messages,
            'summary': summary,
            'business_rules_processed': business_rules_processed,
            'raw_output': {
                'stdout': stdout,
                'stderr': stderr
            }
        }
    
    def _categorize_arelle_message(self, message: str, message_type: str) -> Dict[str, Any]:
        """Enhanced categorization for EBA FINREP business rule messages"""
        
        message_info = {
            'type': message_type,
            'message': message,
            'category': 'general',
            'is_business_rule': False
        }
        
        # Enhanced categories for EBA FINREP business rules
        categories = {
            'business_rule': ['eba_v', 'finrep', 'corep', 'business rule', 'constraint', 'consistency'],
            'calculation': ['calculation', 'summation', 'numeric', 'arithmetic', 'balance'],
            'formula': ['formula', 'expression', 'assertion'],
            'schema': ['schema', 'xsd', 'element', 'type', 'definition'],
            'instance': ['instance', 'fact', 'context', 'unit', 'entity'],
            'dimension': ['dimension', 'domain', 'member', 'axis', 'hierarchy'],
            'linkbase': ['linkbase', 'link', 'arc', 'label', 'reference'],
            'namespace': ['namespace', 'prefix', 'uri', 'import'],
            'validation': ['validation', 'rule', 'check', 'verify']
        }
        
        message_lower = message.lower()
        
        # Enhanced business rule detection
        business_rule_indicators = [
            'eba_v', 'finrep', 'corep', 'business rule', 'constraint violation',
            'consistency check', 'validation rule', 'regulatory rule'
        ]
        
        if any(indicator in message_lower for indicator in business_rule_indicators):
            message_info['is_business_rule'] = True
            message_info['category'] = 'business_rule'
        else:
            # Standard categorization
            for category, keywords in categories.items():
                if any(keyword in message_lower for keyword in keywords):
                    message_info['category'] = category
                    break
        
        # Extract specific details with enhanced patterns
        import re
        
        # Line number extraction
        line_match = re.search(r'line\s+(\d+)', message_lower)
        if line_match:
            message_info['line_number'] = int(line_match.group(1))
        
        # Extract fact/concept name if present
        fact_match = re.search(r'fact\s+([a-zA-Z_:][a-zA-Z0-9_:]*)', message_lower)
        if fact_match:
            message_info['fact_name'] = fact_match.group(1)
        
        # Extract rule code if present (e.g., eba_v1234_c)
        rule_match = re.search(r'(eba_v\d+_[a-z])', message_lower)
        if rule_match:
            message_info['rule_code'] = rule_match.group(1)
            message_info['is_business_rule'] = True
        
        # Extract element names
        element_match = re.search(r'element\s+([a-zA-Z_:][a-zA-Z0-9_:]*)', message_lower)
        if element_match:
            message_info['element_name'] = element_match.group(1)
        
        return message_info
    
    def _generate_cache_key(self, xbrl_path: str, taxonomy_path: str) -> str:
        """Generate a cache key for validation results"""
        import hashlib
        
        # Use file paths and modification times for cache key
        xbrl_mtime = os.path.getmtime(xbrl_path) if os.path.exists(xbrl_path) else 0
        taxonomy_mtime = os.path.getmtime(taxonomy_path) if os.path.exists(taxonomy_path) else 0
        
        cache_input = f"{xbrl_path}_{xbrl_mtime}_{taxonomy_path}_{taxonomy_mtime}"
        return hashlib.md5(cache_input.encode()).hexdigest()
    
    def _get_cached_result(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached validation result if available"""
        try:
            cache_file = os.path.join(self.result_cache_dir, f"{cache_key}.json")
            if os.path.exists(cache_file):
                with open(cache_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to read cache: {e}")
        return None
    
    def _cache_result(self, cache_key: str, result: Dict[str, Any]) -> None:
        """Cache validation result for future use"""
        try:
            cache_file = os.path.join(self.result_cache_dir, f"{cache_key}.json")
            
            # Remove raw output to save space
            cached_result = result.copy()
            if 'raw_output' in cached_result:
                del cached_result['raw_output']
            
            with open(cache_file, 'w') as f:
                json.dump(cached_result, f, indent=2)
                
            logger.info(f"💾 Cached Arelle result: {cache_key}")
        except Exception as e:
            logger.warning(f"Failed to cache result: {e}")
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get information about Arelle cache"""
        try:
            cache_files = os.listdir(self.result_cache_dir) if os.path.exists(self.result_cache_dir) else []
            taxonomy_dirs = os.listdir(self.taxonomy_cache_dir) if os.path.exists(self.taxonomy_cache_dir) else []
            
            return {
                'cache_directory': self.cache_dir,
                'cached_results': len([f for f in cache_files if f.endswith('.json')]),
                'cached_taxonomies': len(taxonomy_dirs),
                'arelle_available': self.arelle_available
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _ensure_directory_permissions(self, directory_path: str) -> bool:
        """Ensure directory has proper read/write permissions"""
        try:
            if os.path.exists(directory_path):
                os.chmod(directory_path, 0o755)  # Read/write/execute permissions
                logger.info(f"✅ Fixed permissions for: {directory_path}")
                
                # Also fix permissions for all files in the directory
                for root, dirs, files in os.walk(directory_path):
                    for d in dirs:
                        try:
                            os.chmod(os.path.join(root, d), 0o755)
                        except Exception:
                            pass  # Ignore permission errors on individual files
                    for f in files:
                        try:
                            os.chmod(os.path.join(root, f), 0o644)
                        except Exception:
                            pass  # Ignore permission errors on individual files
            return True
        except Exception as e:
            logger.error(f"❌ Could not fix permissions for {directory_path}: {e}")
            return False
    
    def clear_cache(self) -> Dict[str, Any]:
        """Clear Arelle cache"""
        try:
            if os.path.exists(self.cache_dir):
                shutil.rmtree(self.cache_dir)
                os.makedirs(self.taxonomy_cache_dir, exist_ok=True)
                os.makedirs(self.result_cache_dir, exist_ok=True)
            
            return {
                'status': 'success',
                'message': 'Arelle cache cleared successfully'
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Failed to clear cache: {str(e)}'
            }