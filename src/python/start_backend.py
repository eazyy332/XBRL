#!/usr/bin/env python3
"""
Backend Startup Script with Diagnostics
========================================
Use this script to start the Flask backend with comprehensive diagnostics.
"""

import os
import sys
import traceback
from pathlib import Path

def check_imports():
    """Check if all required imports are available"""
    print("🔍 Checking imports...")
    
    required_modules = [
        'flask',
        'flask_cors', 
        'pyodbc',
        'xml.etree.ElementTree',
        'zipfile',
        'logging'
    ]
    
    missing_modules = []
    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError as e:
            print(f"❌ {module} - {e}")
            missing_modules.append(module)
    
    if missing_modules:
        print(f"\n⚠️ Missing modules: {missing_modules}")
        print("Install with: pip install flask flask-cors pyodbc")
        return False
    
    return True

def check_files():
    """Check if required files exist"""
    print("\n🔍 Checking required files...")
    
    backend_file = Path(__file__).parent / "enhanced_backend_with_dmp.py"
    if not backend_file.exists():
        print(f"❌ Backend file not found: {backend_file}")
        return False
    print(f"✅ Backend file: {backend_file}")
    
    # Check database files
    dmp_3_3_path = r"C:\Users\berbe\Documents\AI\XBRL-validation\DPM\DPM_Database_3.3.phase3.accdb"
    dmp_4_0_path = r"C:\Users\berbe\Documents\AI\XBRL-validation\DPM\DPM_Database_v4_0_20241218.accdb"
    
    if os.path.exists(dmp_3_3_path):
        print(f"✅ DMP 3.3 Database: {dmp_3_3_path}")
    else:
        print(f"❌ DMP 3.3 Database not found: {dmp_3_3_path}")
    
    if os.path.exists(dmp_4_0_path):
        print(f"✅ DMP 4.0 Database: {dmp_4_0_path}")
    else:
        print(f"❌ DMP 4.0 Database not found: {dmp_4_0_path}")
    
    return True

def test_basic_imports():
    """Test importing key backend modules"""
    print("\n🔍 Testing backend module imports...")
    
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        
        print("Testing dmp_database...")
        from dmp_database import dmp_db
        print("✅ dmp_database imported")
        
        print("Testing concept resolver...")
        from dmp_concept_resolver import concept_resolver  
        print("✅ concept_resolver imported")
        
        print("Testing taxonomy detector...")
        from taxonomy_version_detector import get_taxonomy_recommendations
        print("✅ taxonomy_version_detector imported")
        
        print("Testing enhanced backend...")
        import enhanced_backend_with_dmp
        print("✅ enhanced_backend_with_dmp imported")
        
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        print("\nFull traceback:")
        traceback.print_exc()
        return False

def start_backend():
    """Start the Flask backend"""
    print("\n🚀 Starting Flask backend...")
    
    try:
        # Import and run the backend
        sys.path.insert(0, str(Path(__file__).parent))
        import enhanced_backend_with_dmp
        
        print("Backend should now be running on http://localhost:5000")
        print("Test endpoints:")
        print("  - http://localhost:5000/test")
        print("  - http://localhost:5000/analyze-taxonomy-requirements")
        print("  - http://localhost:5000/health")
        
    except Exception as e:
        print(f"❌ Failed to start backend: {e}")
        traceback.print_exc()
        return False

def main():
    """Main startup function"""
    print("🔧 Backend Startup Diagnostics")
    print("=" * 40)
    
    # Step 1: Check imports
    if not check_imports():
        print("\n❌ Import check failed. Fix missing modules first.")
        return 1
    
    # Step 2: Check files
    if not check_files():
        print("\n❌ File check failed. Check file paths.")
        return 1
    
    # Step 3: Test module imports
    if not test_basic_imports():
        print("\n❌ Module import test failed. Check dependencies.")
        return 1
    
    # Step 4: Start backend
    print("\n✅ All checks passed. Starting backend...")
    start_backend()
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)