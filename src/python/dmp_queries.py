import logging
import pyodbc

logger = logging.getLogger(__name__)

class DMPQueries:
    def __init__(self, connection_manager, discovery_manager):
        self.connection_manager = connection_manager
        self.discovery_manager = discovery_manager
        self.table_mappings = {}
        self._discover_table_mappings()
    
    def _discover_table_mappings(self):
        """Discover actual table names in the database"""
        try:
            available_tables = self.discovery_manager.discover_tables()
            
            # Map expected table names to actual table names with DMP 3.3 support
            expected_tables = {
                'tConcept': ['tConcept', 'DimensionalItem', 'Item', 'PrimaryItem', 'Concept', 'concepts', 'tbl_Concept'],
                'tDataPoint': ['tDataPoint', 'TableItem', 'Cell', 'DataPoint', 'datapoints', 'tbl_DataPoint'],
                'tValidationRule': ['tValidationRule', 'ValidationRuleSet', 'HierarchyValidationRule', 'ValidationRule', 'validation_rules', 'tbl_ValidationRule'],
                'tTable': ['tTable', 'Table', 'tables', 'tbl_Table'],
                'tDimension': ['tDimension', 'Axis', 'Dimension', 'dimensions', 'tbl_Dimension'],
                'tMember': ['tMember', 'Member', 'members', 'tbl_Member']
            }
            
            for expected_name, possible_names in expected_tables.items():
                actual_name = None
                for possible_name in possible_names:
                    if any(possible_name.lower() == table.lower() for table in available_tables):
                        actual_name = next(table for table in available_tables if table.lower() == possible_name.lower())
                        break
                
                if actual_name:
                    self.table_mappings[expected_name] = actual_name
                    logger.info(f"✅ Mapped {expected_name} -> {actual_name}")
                else:
                    logger.warning(f"❌ Table {expected_name} not found in database")
            
        except Exception as e:
            logger.error(f"Failed to discover table mappings: {e}")
    
    def get_actual_table_name(self, expected_name):
        """Get the actual table name for an expected table name"""
        return self.table_mappings.get(expected_name, expected_name)
    
    def get_dmp_tables(self):
        """Get list of DMP tables using actual database structure"""
        try:
            connection = self.connection_manager.get_connection()
            cursor = connection.cursor()
            
            table_name = self.get_actual_table_name('tTable')
            if table_name not in self.table_mappings.values():
                logger.warning(f"Table {table_name} not found, using available tables")
                return self.discovery_manager.discover_tables()
            
            query = f"SELECT TableCode, TableLabel FROM [{table_name}] ORDER BY TableCode"
            cursor.execute(query)
            
            tables = []
            for row in cursor.fetchall():
                tables.append({
                    'code': getattr(row, 'TableCode', row[0]),
                    'label': getattr(row, 'TableLabel', row[1] if len(row) > 1 else row[0])
                })
            
            logger.info(f"Retrieved {len(tables)} DMP tables")
            return tables
            
        except Exception as e:
            logger.error(f"Failed to get DMP tables: {e}")
            # Fallback to discovery
            return [{'code': table, 'label': table} for table in self.discovery_manager.discover_tables()]
    
    def get_table_concepts(self, table_code):
        """Get concepts for a specific table using actual database structure"""
        try:
            connection = self.connection_manager.get_connection()
            cursor = connection.cursor()
            
            # Try multiple approaches to find concepts
            concept_results = []
            
            # Approach 1: Direct concept table
            concept_table = self.get_actual_table_name('tConcept')
            if concept_table in self.table_mappings.values():
                try:
                    query = f"SELECT TOP 100 ConceptCode, ConceptLabel, ConceptType FROM [{concept_table}]"
                    cursor.execute(query)
                    
                    for row in cursor.fetchall():
                        concept_results.append({
                            'conceptCode': getattr(row, 'ConceptCode', row[0]),
                            'conceptLabel': getattr(row, 'ConceptLabel', row[1] if len(row) > 1 else row[0]),
                            'conceptType': getattr(row, 'ConceptType', row[2] if len(row) > 2 else 'Unknown')
                        })
                except Exception as e:
                    logger.warning(f"Failed to query concept table: {e}")
            
            # Approach 2: DataPoint table
            datapoint_table = self.get_actual_table_name('tDataPoint')
            if datapoint_table in self.table_mappings.values():
                try:
                    query = f"SELECT TOP 100 DataPointCode, DataPointLabel FROM [{datapoint_table}]"
                    cursor.execute(query)
                    
                    for row in cursor.fetchall():
                        concept_results.append({
                            'conceptCode': getattr(row, 'DataPointCode', row[0]),
                            'conceptLabel': getattr(row, 'DataPointLabel', row[1] if len(row) > 1 else row[0]),
                            'conceptType': 'DataPoint'
                        })
                except Exception as e:
                    logger.warning(f"Failed to query datapoint table: {e}")
            
            logger.info(f"Retrieved {len(concept_results)} concepts for table {table_code}")
            return concept_results
            
        except Exception as e:
            logger.error(f"Failed to get table concepts: {e}")
            return []
    
    def search_concepts(self, search_term, limit=10):
        """Search for concepts across all available tables including DMP 3.3 support"""
        try:
            connection = self.connection_manager.get_connection()
            cursor = connection.cursor()
            
            results = []
            
            # Detect database version for appropriate table selection
            db_version = self._detect_database_version(connection)
            
            # Search in concept table (version-aware)
            concept_table = self.get_actual_table_name('tConcept')
            if concept_table in self.table_mappings.values():
                try:
                    if db_version == 'dmp_3_3':
                        # DMP 3.3: Use DimensionalItem or Item table
                        if concept_table == 'DimensionalItem':
                            query = f"""
                            SELECT TOP {limit} Code, Label, 'DimensionalItem' as Type 
                            FROM [{concept_table}] 
                            WHERE Code LIKE ? OR Label LIKE ?
                            """
                        elif concept_table == 'Item':
                            query = f"""
                            SELECT TOP {limit} Code, Label, 'Item' as Type 
                            FROM [{concept_table}] 
                            WHERE Code LIKE ? OR Label LIKE ?
                            """
                        else:
                            query = f"""
                            SELECT TOP {limit} Code, Label, 'Concept' as Type 
                            FROM [{concept_table}] 
                            WHERE Code LIKE ? OR Label LIKE ?
                            """
                    else:
                        # DMP 4.0: Use standard tConcept structure
                        query = f"""
                        SELECT TOP {limit} ConceptCode, ConceptLabel, ConceptType 
                        FROM [{concept_table}] 
                        WHERE ConceptCode LIKE ? OR ConceptLabel LIKE ?
                        """
                    
                    cursor.execute(query, f"%{search_term}%", f"%{search_term}%")
                    
                    for row in cursor.fetchall():
                        if db_version == 'dmp_3_3':
                            results.append({
                                'conceptCode': getattr(row, 'Code', row[0]),
                                'conceptLabel': getattr(row, 'Label', row[1] if len(row) > 1 else row[0]),
                                'conceptType': getattr(row, 'Type', row[2] if len(row) > 2 else 'Concept'),
                                'source': concept_table
                            })
                        else:
                            results.append({
                                'conceptCode': getattr(row, 'ConceptCode', row[0]),
                                'conceptLabel': getattr(row, 'ConceptLabel', row[1] if len(row) > 1 else row[0]),
                                'conceptType': getattr(row, 'ConceptType', row[2] if len(row) > 2 else 'Concept'),
                                'source': 'tConcept'
                            })
                except Exception as e:
                    logger.warning(f"Failed to search concept table: {e}")
            
            # Search in datapoint table (version-aware)
            datapoint_table = self.get_actual_table_name('tDataPoint')
            if datapoint_table in self.table_mappings.values():
                try:
                    if db_version == 'dmp_3_3':
                        # DMP 3.3: Use TableItem or Cell table
                        if datapoint_table == 'TableItem':
                            query = f"""
                            SELECT TOP {limit} Code, Label 
                            FROM [{datapoint_table}] 
                            WHERE Code LIKE ? OR Label LIKE ?
                            """
                        else:
                            query = f"""
                            SELECT TOP {limit} Code, Code 
                            FROM [{datapoint_table}] 
                            WHERE Code LIKE ?
                            """
                            cursor.execute(query, f"%{search_term}%")
                    else:
                        # DMP 4.0: Use standard tDataPoint structure
                        query = f"""
                        SELECT TOP {limit} DataPointCode, DataPointLabel 
                        FROM [{datapoint_table}] 
                        WHERE DataPointCode LIKE ? OR DataPointLabel LIKE ?
                        """
                        cursor.execute(query, f"%{search_term}%", f"%{search_term}%")
                    
                    if db_version == 'dmp_3_3' and datapoint_table != 'TableItem':
                        for row in cursor.fetchall():
                            results.append({
                                'conceptCode': getattr(row, 'Code', row[0]),
                                'conceptLabel': getattr(row, 'Code', row[0]),
                                'conceptType': 'DataPoint',
                                'source': datapoint_table
                            })
                    else:
                        for row in cursor.fetchall():
                            if db_version == 'dmp_3_3':
                                results.append({
                                    'conceptCode': getattr(row, 'Code', row[0]),
                                    'conceptLabel': getattr(row, 'Label', row[1] if len(row) > 1 else row[0]),
                                    'conceptType': 'DataPoint',
                                    'source': datapoint_table
                                })
                            else:
                                results.append({
                                    'conceptCode': getattr(row, 'DataPointCode', row[0]),
                                    'conceptLabel': getattr(row, 'DataPointLabel', row[1] if len(row) > 1 else row[0]),
                                    'conceptType': 'DataPoint',
                                    'source': 'tDataPoint'
                                })
                except Exception as e:
                    logger.warning(f"Failed to search datapoint table: {e}")
            
            # Search in Member table (works for both versions)
            member_table = self.get_actual_table_name('tMember')
            if member_table in self.table_mappings.values():
                try:
                    query = f"""
                    SELECT TOP {limit} MemberCode, MemberXbrlCode, MemberLabel 
                    FROM [{member_table}] 
                    WHERE MemberCode LIKE ? OR MemberXbrlCode LIKE ? OR MemberLabel LIKE ?
                    """
                    cursor.execute(query, f"%{search_term}%", f"%{search_term}%", f"%{search_term}%")
                    
                    for row in cursor.fetchall():
                        results.append({
                            'conceptCode': getattr(row, 'MemberCode', row[0]),
                            'conceptXbrlCode': getattr(row, 'MemberXbrlCode', row[1] if len(row) > 1 else ''),
                            'conceptLabel': getattr(row, 'MemberLabel', row[2] if len(row) > 2 else row[0]),
                            'conceptType': 'Member',
                            'source': 'tMember'
                        })
                except Exception as e:
                    logger.warning(f"Failed to search member table: {e}")
            
            logger.info(f"Found {len(results)} concepts matching '{search_term}' (DB version: {db_version})")
            return results
            
        except Exception as e:
            logger.error(f"Failed to search concepts: {e}")
            return []
    
    def _detect_database_version(self, connection):
        """Detect whether this is DMP 3.3 or DMP 4.0 database"""
        try:
            cursor = connection.cursor()
            
            # Check for DimensionalItem table (DMP 3.3 indicator)
            try:
                cursor.execute("SELECT TOP 1 * FROM [DimensionalItem]")
                logger.debug("✅ Detected DMP 3.3 database - DimensionalItem table found")
                return 'dmp_3_3'
            except:
                # DimensionalItem not found, try tConcept table for DMP 4.0
                try:
                    cursor.execute(f"SELECT TOP 1 * FROM [tConcept]")
                    logger.debug("✅ Detected DMP 4.0 database - tConcept table found")
                    return 'dmp_4_0'
                except:
                    logger.warning("⚠️ No DimensionalItem or tConcept table found, defaulting to DMP 3.3")
                    return 'dmp_3_3'
                    
        except Exception as e:
            logger.warning(f"⚠️ Database version detection failed: {e}, defaulting to DMP 3.3")
            return 'dmp_3_3'
    
    def search_member_concepts(self, search_term, limit=10):
        """Dedicated search for Member table concepts"""
        try:
            connection = self.connection_manager.get_connection()
            cursor = connection.cursor()
            
            member_table = self.get_actual_table_name('tMember')
            if member_table not in self.table_mappings.values():
                logger.warning(f"Member table not found")
                return []
            
            # Search both MemberCode and MemberXbrlCode
            query = f"""
            SELECT TOP {limit} MemberCode, MemberXbrlCode, MemberLabel, DimensionCode
            FROM [{member_table}] 
            WHERE MemberCode LIKE ? OR MemberXbrlCode LIKE ? OR MemberCode = ? OR MemberXbrlCode = ?
            ORDER BY 
                CASE 
                    WHEN MemberCode = ? THEN 1
                    WHEN MemberXbrlCode = ? THEN 2
                    WHEN MemberCode LIKE ? THEN 3
                    WHEN MemberXbrlCode LIKE ? THEN 4
                    ELSE 5
                END
            """
            
            exact_term = search_term
            like_term = f"%{search_term}%"
            
            cursor.execute(query, like_term, like_term, exact_term, exact_term, 
                          exact_term, exact_term, like_term, like_term)
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'memberCode': getattr(row, 'MemberCode', row[0]),
                    'memberXbrlCode': getattr(row, 'MemberXbrlCode', row[1] if len(row) > 1 else ''),
                    'memberLabel': getattr(row, 'MemberLabel', row[2] if len(row) > 2 else ''),
                    'dimensionCode': getattr(row, 'DimensionCode', row[3] if len(row) > 3 else ''),
                    'source': 'tMember'
                })
            
            logger.info(f"Found {len(results)} member concepts for '{search_term}'")
            return results
            
        except Exception as e:
            logger.error(f"Failed to search member concepts: {e}")
            return []
    
    def get_comprehensive_health_check(self):
        """Get comprehensive health check of the database"""
        try:
            connection = self.connection_manager.get_connection()
            cursor = connection.cursor()
            
            health_check = {
                'available_tables': self.discovery_manager.discover_tables(),
                'table_mappings': self.table_mappings,
                'total_concepts': 0,
                'total_datapoints': 0,
                'total_validation_rules': 0,
                'total_tables': 0
            }
            
            # Count concepts
            concept_table = self.get_actual_table_name('tConcept')
            if concept_table in self.table_mappings.values():
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM [{concept_table}]")
                    health_check['total_concepts'] = cursor.fetchone()[0]
                except:
                    pass
            
            # Count datapoints
            datapoint_table = self.get_actual_table_name('tDataPoint')
            if datapoint_table in self.table_mappings.values():
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM [{datapoint_table}]")
                    health_check['total_datapoints'] = cursor.fetchone()[0]
                except:
                    pass
            
            # Count validation rules
            validation_table = self.get_actual_table_name('tValidationRule')
            if validation_table in self.table_mappings.values():
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM [{validation_table}]")
                    health_check['total_validation_rules'] = cursor.fetchone()[0]
                except:
                    pass
            
            # Count tables
            table_table = self.get_actual_table_name('tTable')
            if table_table in self.table_mappings.values():
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM [{table_table}]")
                    health_check['total_tables'] = cursor.fetchone()[0]
                except:
                    pass
            
            logger.info(f"Health check completed: {health_check['total_concepts']} concepts, {health_check['total_datapoints']} datapoints")
            return health_check
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                'error': str(e),
                'available_tables': [],
                'table_mappings': {},
                'total_concepts': 0,
                'total_datapoints': 0,
                'total_validation_rules': 0,
                'total_tables': 0
            }
    
    def get_validation_rules(self, table_code):
        """Get validation rules for a specific table"""
        try:
            connection = self.connection_manager.get_connection()
            cursor = connection.cursor()
            
            validation_table = self.get_actual_table_name('tValidationRule')
            if validation_table not in self.table_mappings.values():
                logger.warning(f"Validation rules table not found")
                return []
            
            query = f"""
            SELECT TOP 50 RuleCode, RuleLabel, RuleType, Expression 
            FROM [{validation_table}] 
            WHERE TableCode = ? OR TableCode IS NULL
            ORDER BY RuleCode
            """
            
            cursor.execute(query, table_code)
            
            rules = []
            for row in cursor.fetchall():
                rules.append({
                    'ruleCode': getattr(row, 'RuleCode', row[0]),
                    'ruleLabel': getattr(row, 'RuleLabel', row[1] if len(row) > 1 else row[0]),
                    'ruleType': getattr(row, 'RuleType', row[2] if len(row) > 2 else 'Unknown'),
                    'expression': getattr(row, 'Expression', row[3] if len(row) > 3 else '')
                })
            
            logger.info(f"Retrieved {len(rules)} validation rules for table {table_code}")
            return rules
            
        except Exception as e:
            logger.error(f"Failed to get validation rules: {e}")
            return []
    
    def get_dimensional_info(self, datapoint_code):
        """Get dimensional information for a datapoint"""
        try:
            connection = self.connection_manager.get_connection()
            cursor = connection.cursor()
            
            dimension_table = self.get_actual_table_name('tDimension')
            if dimension_table not in self.table_mappings.values():
                logger.warning(f"Dimension table not found")
                return []
            
            query = f"""
            SELECT TOP 20 DimensionCode, DimensionLabel, DimensionType 
            FROM [{dimension_table}] 
            WHERE DataPointCode = ? OR DataPointCode IS NULL
            ORDER BY DimensionCode
            """
            
            cursor.execute(query, datapoint_code)
            
            dimensions = []
            for row in cursor.fetchall():
                dimensions.append({
                    'dimensionCode': getattr(row, 'DimensionCode', row[0]),
                    'dimensionLabel': getattr(row, 'DimensionLabel', row[1] if len(row) > 1 else row[0]),
                    'dimensionType': getattr(row, 'DimensionType', row[2] if len(row) > 2 else 'Unknown')
                })
            
            logger.info(f"Retrieved {len(dimensions)} dimensions for datapoint {datapoint_code}")
            return dimensions
            
        except Exception as e:
            logger.error(f"Failed to get dimensional info: {e}")
            return []
    
    def search_concept(self, concept_name):
        """Search for a concept in the DMP database"""
        try:
            connection = self.connection_manager.get_connection()
            cursor = connection.cursor()
            
            concept_table = self.get_actual_table_name('tConcept')
            if concept_table not in self.table_mappings.values():
                return None
            
            query = f"SELECT ConceptCode, ConceptLabel, ConceptType FROM [{concept_table}] WHERE ConceptCode = ? OR ConceptLabel = ?"
            cursor.execute(query, (concept_name, concept_name))
            result = cursor.fetchone()
            
            if result:
                return {
                    'ConceptCode': getattr(result, 'ConceptCode', result[0]),
                    'ConceptLabel': getattr(result, 'ConceptLabel', result[1] if len(result) > 1 else ''),
                    'ConceptType': getattr(result, 'ConceptType', result[2] if len(result) > 2 else ''),
                    'MetricCode': getattr(result, 'MetricCode', result[3] if len(result) > 3 else '')
                }
            return None
            
        except Exception as e:
            logger.error(f"Concept search failed: {e}")
            return None
