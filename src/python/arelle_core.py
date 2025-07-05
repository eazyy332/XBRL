
import subprocess
import os
import logging
from config import ARELLE_PATH

logger = logging.getLogger(__name__)

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

def run_basic_arelle_validation(instance_path, extracted_schemas=None):
    """Run basic Arelle validation with optional extracted schemas"""
    try:
        logger.info(f"🔧 Running basic XBRL validation for: {instance_path}")
        
        # FIXED: Basic Arelle command with MINIMAL options to prevent errors
        arelle_cmd = [
            ARELLE_PATH,
            "--file", instance_path,
            "--validate",
            "--logLevel", "INFO",
            "--logFormat", "[%(levelname)s] %(asctime)s - %(message)s"
        ]
        
        # Add extracted schemas if available
        if extracted_schemas:
            logger.info(f"Adding {len(extracted_schemas)} extracted schemas")
            for schema in extracted_schemas[:50]:  # Limit to prevent command line overflow
                if schema.endswith('.xsd'):
                    arelle_cmd.extend(["--import", schema])
        
        logger.info(f"🔧 Basic Arelle command: {' '.join(arelle_cmd[:8])}... (with {len(extracted_schemas) if extracted_schemas else 0} schemas)")
        
        # Execute with timeout
        result = subprocess.run(
            arelle_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=300
        )
        
        logger.info(f"✅ Basic validation completed with return code: {result.returncode}")
        return result
        
    except subprocess.TimeoutExpired:
        logger.error("⚠️ Validation timeout after 5 minutes")
        raise Exception('Validation timeout after 5 minutes - file may be too complex')
    except Exception as e:
        logger.error(f"❌ Basic validation failed: {str(e)}")
        raise Exception(f'Validation failed: {str(e)}')

def build_enhanced_arelle_command(instance_path, extracted_schemas, prioritized_packages):
    """Build enhanced Arelle command with all available schemas and packages"""
    arelle_cmd = [ARELLE_PATH]
    
    # Basic validation flags
    arelle_cmd.extend([
        "--file", instance_path,
        "--validate",
        "--calcDecimals", 
        "--calcPrecision",
        "--logLevel", "info",
        "--logFormat", "%(message)s"
    ])
    
    # EBA plugin configuration
    arelle_cmd.extend([
        "--plugins", "validate/EBA",
        "--disclosureSystem", "EBA"
    ])
    
    # Import extracted schemas
    if extracted_schemas:
        for schema in extracted_schemas[:100]:  # Limit for performance
            if schema.endswith('.xsd'):
                arelle_cmd.extend(["--import", schema])
    
    # Import prioritized packages
    if prioritized_packages:
        for package in prioritized_packages[:50]:
            if package.endswith('.xsd'):
                arelle_cmd.extend(["--import", package])
            elif package.endswith('.zip') or os.path.isdir(package):
                arelle_cmd.extend(["--packages", package])
    
    # Connectivity options
    arelle_cmd.extend([
        "--internetConnectivity", "offline"
    ])
    
    return arelle_cmd
