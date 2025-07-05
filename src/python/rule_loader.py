"""
DMP Rule Loader
==============
Handles loading and caching of validation rules from DMP database.
Supports both DMP 3.3 and DMP 4.0 database schemas.
"""

import logging
from typing import Dict, Any
from dmp_database import dmp_db

logger = logging.getLogger(__name__)

class DMPRuleLoader:
    """
    Handles loading validation rules from DMP database with version detection
    """
    
    def __init__(self):
        self.rules_cache = {}
        self.rule_categories = {}
    
    def load_validation_rules(self) -> Dict[str, Any]:
        """Load validation rules from DMP database"""
        try:
            connection = dmp_db.connection_manager.get_connection()
            cursor = connection.cursor()
            
            # Determine database version first
            db_version = self._detect_database_version(connection)
            logger.info(f"🔍 Using database version: {db_version}")
            
            rules_cache = {}
            rule_categories = {}
            
            if db_version == 'dmp_3_3':
                # DMP 3.3: Use ValidationRuleSet table (working table with 197k rows)
                try:
                    cursor.execute("SELECT * FROM [ValidationRuleSet]")
                    columns = [desc[0] for desc in cursor.description]
                    
                    for row in cursor.fetchall():
                        rule_dict = dict(zip(columns, row))
                        
                        # Map ValidationRuleSet columns to expected format
                        rule_id = rule_dict.get('ValidationRuleId')
                        if rule_id:
                            processed_rule = {
                                'RuleCode': f"Rule_{rule_id}",
                                'RuleLabel': f"ValidationRule_{rule_id}",
                                'RuleType': 'ValidationSet',
                                'Expression': f"Rule_{rule_id}",
                                'TableCode': f"Module_{rule_dict.get('ModuleID', '')}",
                                'ErrorSeverity': rule_dict.get('Severity') or 'ERROR',
                                'ValidationRuleId': rule_id,
                                'ModuleID': rule_dict.get('ModuleID'),
                                'ValidationRuleSetCode': rule_dict.get('ValidationRuleSetCode')
                            }
                            
                            rule_code = processed_rule['RuleCode']
                            rules_cache[rule_code] = processed_rule
                            
                            # Categorize rule
                            rule_type = processed_rule.get('RuleType', 'General')
                            if rule_type not in rule_categories:
                                rule_categories[rule_type] = []
                            rule_categories[rule_type].append(rule_code)
                    
                    logger.info(f"✅ Loaded {len(rules_cache)} DMP 3.3 validation rules from ValidationRuleSet")
                    
                except Exception as e:
                    logger.warning(f"⚠️ Failed to load from ValidationRuleSet: {e}")
                    return {}
            else:
                # DMP 4.0: Use ValidationRule table
                try:
                    rules_table = dmp_db.queries_manager.get_actual_table_name('tValidationRule')
                    if rules_table not in dmp_db.queries_manager.table_mappings.values():
                        logger.warning("ValidationRule table not found - rule validation disabled")
                        return {}
                    
                    query = f"""
                    SELECT RuleCode, RuleLabel, RuleType, Expression, TableCode, 
                           ErrorSeverity, ErrorMessage, RuleDescription
                    FROM [{rules_table}] 
                    WHERE RuleCode IS NOT NULL
                    ORDER BY RuleCode
                    """
                    
                    logger.debug(f"📝 Executing query: {query}")
                    cursor.execute(query)
                    columns = [desc[0] for desc in cursor.description]
                    
                    for row in cursor.fetchall():
                        rule_dict = dict(zip(columns, row))
                        rule_code = rule_dict.get('RuleCode')
                        
                        if rule_code:
                            # Store raw rule data
                            rules_cache[rule_code] = rule_dict
                            
                            # Categorize rule
                            rule_type = rule_dict.get('RuleType', 'General')
                            if rule_type not in rule_categories:
                                rule_categories[rule_type] = []
                            rule_categories[rule_type].append(rule_code)
                    
                    logger.info(f"✅ Loaded {len(rules_cache)} DMP 4.0 validation rules")
                    
                except Exception as e:
                    logger.error(f"❌ Failed to load DMP 4.0 validation rules: {e}")
                    return {}
            
            logger.info(f"📊 Rule categories: {dict((k, len(v)) for k, v in rule_categories.items())}")
            
            return {
                'rules_cache': rules_cache,
                'rule_categories': rule_categories
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to load validation rules: {e}")
            return {}
    
    def _detect_database_version(self, connection) -> str:
        """Detect whether this is DMP 3.3 or DMP 4.0 database"""
        try:
            cursor = connection.cursor()
            
            # Check for ValidationRuleSet table (DMP 3.3 indicator)
            try:
                cursor.execute("SELECT TOP 1 * FROM [ValidationRuleSet]")
                logger.debug("✅ Detected DMP 3.3 database - ValidationRuleSet table found")
                return 'dmp_3_3'
            except:
                # ValidationRuleSet not found, try ValidationRule table for DMP 4.0
                try:
                    rules_table = dmp_db.queries_manager.get_actual_table_name('tValidationRule')
                    cursor.execute(f"SELECT TOP 1 * FROM [{rules_table}]")
                    columns = [desc[0] for desc in cursor.description]
                    
                    # DMP 4.0 has more columns including ErrorSeverity, ErrorMessage, etc.
                    if 'ErrorSeverity' in columns and 'ErrorMessage' in columns:
                        logger.debug(f"✅ Detected DMP 4.0 database - ValidationRule table with {len(columns)} columns")
                        return 'dmp_4_0'
                    else:
                        logger.debug(f"✅ Detected DMP 3.3 database - ValidationRule table with {len(columns)} columns")
                        return 'dmp_3_3'
                except:
                    logger.warning("⚠️ No ValidationRule or ValidationRuleSet table found, defaulting to DMP 3.3")
                    return 'dmp_3_3'
                    
        except Exception as e:
            logger.warning(f"⚠️ Database version detection failed: {e}, defaulting to DMP 3.3")
            return 'dmp_3_3'
    
    def get_loader_info(self) -> Dict[str, Any]:
        """Get information about the rule loader status"""
        return {
            'total_rules_loaded': len(self.rules_cache),
            'rule_categories': {cat: len(rules) for cat, rules in self.rule_categories.items()}
        }