
import logging
import os
from dmp_connection import DMPConnection
from dmp_discovery import DMPDiscovery
from dmp_queries import DMPQueries

logger = logging.getLogger(__name__)

class DMPDatabase:
    def __init__(self, architecture_version=None):
        # Select database based on architecture version
        self.dmp_4_0_path = r"C:\Users\berbe\Documents\AI\XBRL-validation\DPM\DPM_Database_v4_0_20241218.accdb"
        self.dmp_3_3_path = r"C:\Users\berbe\Documents\AI\XBRL-validation\DPM\DPM_Database_3.3.phase3.accdb"
        
        # FIXED: Handle both string formats consistently
        if architecture_version in ["arch_1_0", "Architecture 1.0"]:
            self.db_path = self.dmp_3_3_path
            logger.info("🔄 Using DMP 3.3 database for Architecture 1.0 (FINREP)")
        elif architecture_version in ["arch_2_0", "Architecture 2.0"]:
            self.db_path = self.dmp_4_0_path
            logger.info("🔄 Using DMP 4.0 database for Architecture 2.0")
        else:
            # Default to DMP 4.0 for unknown/None architectures
            self.db_path = self.dmp_4_0_path
            logger.info(f"🔄 Using DMP 4.0 database (default for architecture: {architecture_version})")
        
        # Initialize components
        self.connection_manager = DMPConnection(self.db_path)
        self.discovery_manager = DMPDiscovery(self.connection_manager)
        self.queries_manager = DMPQueries(self.connection_manager, self.discovery_manager)
    
    def switch_database(self, architecture_version):
        """Switch database based on architecture version with consistent parameter mapping"""
        old_path = self.db_path
        
        # FIXED: Handle both string formats consistently
        if architecture_version in ["arch_1_0", "Architecture 1.0"]:
            self.db_path = self.dmp_3_3_path
            logger.info("🔄 Switching to DMP 3.3 database for Architecture 1.0 (FINREP)")
        elif architecture_version in ["arch_2_0", "Architecture 2.0"]:
            self.db_path = self.dmp_4_0_path
            logger.info("🔄 Switching to DMP 4.0 database for Architecture 2.0")
        else:
            # Default to DMP 4.0 for unknown architectures
            self.db_path = self.dmp_4_0_path
            logger.info(f"🔄 Switching to DMP 4.0 database (default for unknown architecture: {architecture_version})")
        
        if old_path != self.db_path:
            # Reinitialize components with new database
            self.connection_manager.close_connection()
            self.connection_manager = DMPConnection(self.db_path)
            self.discovery_manager = DMPDiscovery(self.connection_manager)
            self.queries_manager = DMPQueries(self.connection_manager, self.discovery_manager)
            logger.info(f"✅ Database components reinitialized with {os.path.basename(self.db_path)}")
        else:
            logger.info("ℹ️ No database switch needed - already using correct database")
    
    def test_connection(self):
        """Test database connection with detailed diagnostics"""
        return self.discovery_manager.get_enhanced_connection_status()
    
    def discover_tables(self):
        """Discover available tables in the database"""
        return self.discovery_manager.discover_tables()
    
    def get_dmp_tables(self):
        """Get list of DMP tables using actual database structure"""
        return self.queries_manager.get_dmp_tables()
    
    def get_table_concepts(self, table_code):
        """Get concepts for a specific table using actual database structure"""
        return self.queries_manager.get_table_concepts(table_code)
    
    def get_validation_rules(self, table_code):
        """Get validation rules for a specific table"""
        return self.queries_manager.get_validation_rules(table_code)
    
    def get_dimensional_info(self, datapoint_code):
        """Get dimensional information for a datapoint"""
        return self.queries_manager.get_dimensional_info(datapoint_code)
    
    def close_connection(self):
        """Close database connection"""
        self.connection_manager.close_connection()

# Global instance
dmp_db = DMPDatabase()
