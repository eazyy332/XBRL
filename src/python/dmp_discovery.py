
import logging

logger = logging.getLogger(__name__)

class DMPDiscovery:
    def __init__(self, connection_manager):
        self.connection_manager = connection_manager
        self.dmp_4_0_tables = [
            'Table', 'TableVersion', 'TableVersionCell', 'Concept', 'Domain', 
            'Member', 'Metric', 'Axis', 'ValidationRules', 'BusinessRules',
            'DataPoint', 'Hierarchy', 'DimensionalStructure'
        ]
    
    def discover_tables(self):
        """Discover available tables in the database"""
        try:
            connection = self.connection_manager.get_connection()
            cursor = connection.cursor()
            
            # Get all table names
            tables = []
            for table_info in cursor.tables(tableType='TABLE'):
                table_name = table_info.table_name
                if not table_name.startswith('MSys'):  # Skip system tables
                    tables.append(table_name)
            
            logger.info(f"Discovered {len(tables)} tables in DMP 4.0 database")
            return tables
            
        except Exception as e:
            logger.error(f"Failed to discover tables: {str(e)}")
            return []
    
    def identify_dmp_4_0_structure(self):
        """Identify which DMP 4.0 tables are available"""
        available_tables = self.discover_tables()
        dmp_tables_found = {}
        
        for expected_table in self.dmp_4_0_tables:
            # Check exact match first
            if expected_table in available_tables:
                dmp_tables_found[expected_table] = expected_table
            else:
                # Check for similar names (case variations, prefixes, etc.)
                for table in available_tables:
                    if expected_table.lower() in table.lower():
                        dmp_tables_found[expected_table] = table
                        break
        
        logger.info(f"DMP 4.0 structure analysis: {len(dmp_tables_found)} standard tables found")
        return dmp_tables_found, available_tables
    
    def get_table_structure(self, table_name):
        """Get column structure for a specific table"""
        try:
            connection = self.connection_manager.get_connection()
            cursor = connection.cursor()
            
            columns = []
            for column in cursor.columns(table=table_name):
                columns.append({
                    'name': column.column_name,
                    'type': column.type_name,
                    'size': column.column_size,
                    'nullable': column.nullable
                })
            
            return columns
            
        except Exception as e:
            logger.error(f"Failed to get structure for table {table_name}: {str(e)}")
            return []
    
    def get_enhanced_connection_status(self):
        """Get enhanced connection status with DMP 4.0 structure analysis"""
        base_status = self.connection_manager.test_connection()
        
        if base_status["status"] == "connected":
            try:
                # Analyze DMP 4.0 structure
                dmp_tables_found, all_tables = self.identify_dmp_4_0_structure()
                
                # Test key tables
                connection = self.connection_manager.get_connection()
                cursor = connection.cursor()
                
                table_info = []
                
                # Test ValidationRules table specifically
                if 'ValidationRules' in dmp_tables_found:
                    try:
                        actual_table = dmp_tables_found['ValidationRules']
                        cursor.execute(f"SELECT COUNT(*) FROM [{actual_table}]")
                        count = cursor.fetchone()[0]
                        table_info.append({"table": "ValidationRules", "rows": count, "status": "available"})
                        logger.info(f"✅ ValidationRules table found with {count} rules")
                    except Exception as e:
                        table_info.append({"table": "ValidationRules", "rows": 0, "status": "error", "error": str(e)})
                
                # Test other key tables
                for table_type, actual_table in list(dmp_tables_found.items())[:5]:
                    if table_type != 'ValidationRules':
                        try:
                            cursor.execute(f"SELECT COUNT(*) FROM [{actual_table}]")
                            count = cursor.fetchone()[0]
                            table_info.append({"table": table_type, "rows": count, "status": "available"})
                        except Exception as e:
                            table_info.append({"table": table_type, "rows": 0, "status": "error"})
                
                base_status.update({
                    "message": f"Connected to DMP 4.0 database with {len(dmp_tables_found)} standard tables",
                    "dmp_tables": len(all_tables),
                    "dmp_4_0_tables": len(dmp_tables_found),
                    "sample_tables": table_info,
                    "available_tables": list(dmp_tables_found.keys()),
                    "database_version": "DMP 4.0 (December 2024)",
                    "validation_rules_available": 'ValidationRules' in dmp_tables_found
                })
                    
            except Exception as query_error:
                base_status.update({
                    "status": "limited",
                    "message": f"Connected but limited access: {str(query_error)}",
                    "troubleshooting": "Database connected but some queries may fail due to permissions or structure"
                })
        
        return base_status
