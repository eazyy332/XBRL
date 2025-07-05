
import pyodbc
import os
import logging

logger = logging.getLogger(__name__)

class DMPConnection:
    def __init__(self, db_path):
        self.db_path = db_path
        self.connection = None
        
    def get_connection_string(self):
        """Get the connection string for the Access database"""
        return (
            f"DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};"
            f"DBQ={self.db_path};"
            f"ExtendedAnsiSQL=1;"
            f"ReadOnly=1;"  # Try read-only mode to avoid permission issues
        )
    
    def get_connection(self):
        """Get database connection"""
        if self.connection is None:
            conn_str = self.get_connection_string()
            self.connection = pyodbc.connect(conn_str)
        return self.connection
    
    def test_connection(self):
        """Test database connection with detailed diagnostics"""
        try:
            if not os.path.exists(self.db_path):
                return {
                    "status": "error",
                    "message": f"Database file not found at {self.db_path}",
                    "database_path": self.db_path,
                    "troubleshooting": "Check if database file exists and path is correct"
                }
            
            # Try to connect with read-only mode
            conn_str = self.get_connection_string()
            connection = pyodbc.connect(conn_str)
            connection.close()
            
            return {
                "status": "connected",
                "message": "Successfully connected to DMP 4.0 database",
                "database_path": self.db_path
            }
                
        except pyodbc.Error as e:
            error_msg = str(e)
            if "no read permission" in error_msg.lower():
                return {
                    "status": "permission_error",
                    "message": "Database connected but has permission restrictions",
                    "database_path": self.db_path,
                    "troubleshooting": "Try running as administrator or check database permissions"
                }
            else:
                return {
                    "status": "error",
                    "message": f"Database connection failed: {error_msg}",
                    "database_path": self.db_path,
                    "troubleshooting": "Check database drivers and file permissions"
                }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Unexpected error: {str(e)}",
                "database_path": self.db_path,
                "troubleshooting": "Check database installation and Access drivers"
            }
    
    def close_connection(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            self.connection = None
