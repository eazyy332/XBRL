

import logging
import re
from dmp_database import dmp_db

logger = logging.getLogger(__name__)

class DMPConceptResolver:
    def __init__(self):
        self.concept_cache = {}
        self.prefix_mappings = {
            'eba_met': ['eba_met', 'find'],
            'eba_met_3.4': ['eba_met', 'find'],
            'eba_met_4.0': ['eba_met', 'find'],
            'find': ['find', 'eba_met']
        }
    
    def resolve_concept_from_dmp(self, concept_name):
        """
        Resolve XBRL concept to DMP database concept with Member table support
        """
        if concept_name in self.concept_cache:
            return self.concept_cache[concept_name]
        
        try:
            # Clean concept name - remove prefix
            clean_concept = self._clean_concept_name(concept_name)
            
            # Try multiple search strategies including Member table
            dmp_concept = (
                self._search_by_exact_match(concept_name) or
                self._search_by_clean_name(clean_concept) or
                self._search_by_prefix_variants(concept_name) or
                self._search_by_partial_match(clean_concept) or
                self._search_in_member_table(concept_name) or  # NEW: Member table search
                self._search_using_queries_manager(concept_name)
            )
            
            if dmp_concept:
                logger.info(f"✅ Resolved concept: {concept_name} -> {dmp_concept['ConceptCode']} (source: {dmp_concept.get('source', 'unknown')})")
                self.concept_cache[concept_name] = dmp_concept
                return dmp_concept
            else:
                logger.warning(f"❌ Could not resolve concept: {concept_name}")
                return None
                
        except Exception as e:
            logger.error(f"Error resolving concept {concept_name}: {e}")
            return None
    
    def _clean_concept_name(self, concept_name):
        """Remove namespace prefix from concept"""
        if ':' in concept_name:
            return concept_name.split(':', 1)[1]
        return concept_name
    
    def _search_by_exact_match(self, concept_name):
        """Search for exact concept match in DMP database using working tables"""
        try:
            connection = dmp_db.connection_manager.get_connection()
            cursor = connection.cursor()
            
            # FIXED: Use DMP 3.3 proper tables for concept search
            db_version = self._detect_database_version(connection)
            
            if db_version == 'dmp_3_3':
                # Priority: Use DimensionalItem (main concept table in DMP 3.3)
                try:
                    query = """
                    SELECT TOP 1 Code as ConceptCode, 
                           Label as ConceptLabel,
                           'DimensionalItem' as ConceptType
                    FROM DimensionalItem 
                    WHERE Code = ? OR Code LIKE ?
                    """
                    cursor.execute(query, (concept_name, f"%{concept_name}%"))
                    result = cursor.fetchone()
                    
                    if result:
                        return {
                            'ConceptCode': result[0],
                            'ConceptLabel': result[1],
                            'ConceptType': result[2],
                            'MetricCode': '',
                            'source': 'DimensionalItem'
                        }
                except:
                    # Fallback to Item table
                    try:
                        query = """
                        SELECT TOP 1 Code as ConceptCode, 
                               Label as ConceptLabel,
                               'Item' as ConceptType
                        FROM Item 
                        WHERE Code = ? OR Code LIKE ?
                        """
                        cursor.execute(query, (concept_name, f"%{concept_name}%"))
                        result = cursor.fetchone()
                        
                        if result:
                            return {
                                'ConceptCode': result[0],
                                'ConceptLabel': result[1],
                                'ConceptType': result[2],
                                'MetricCode': '',
                                'source': 'Item'
                            }
                    except:
                        pass
            else:
                # DMP 4.0 - use tConcept table with 4 columns
                concept_table = dmp_db.queries_manager.get_actual_table_name('tConcept')
                if concept_table in dmp_db.queries_manager.table_mappings.values():
                    query = f"""
                    SELECT ConceptCode, ConceptLabel, ConceptType, MetricCode
                    FROM [{concept_table}] 
                    WHERE ConceptCode = ? OR ConceptLabel = ?
                    """
                    cursor.execute(query, (concept_name, concept_name))
                    result = cursor.fetchone()
                    
                    if result:
                        return {
                            'ConceptCode': getattr(result, 'ConceptCode', result[0]),
                            'ConceptLabel': getattr(result, 'ConceptLabel', result[1] if len(result) > 1 else ''),
                            'ConceptType': getattr(result, 'ConceptType', result[2] if len(result) > 2 else ''),
                            'MetricCode': getattr(result, 'MetricCode', result[3] if len(result) > 3 else ''),
                            'source': 'tConcept'
                        }
            
            return None
            
        except Exception as e:
            logger.error(f"Exact match search failed: {e}")
            return None
    
    def _search_by_clean_name(self, clean_name):
        """Search using cleaned concept name with DMP 3.3 compatibility"""
        try:
            connection = dmp_db.connection_manager.get_connection()
            cursor = connection.cursor()
            
            db_version = self._detect_database_version(connection)
            
            if db_version == 'dmp_3_3':
                # Search in multiple DMP 3.3 tables for concepts
                # 1. Try DimensionalItem first
                try:
                    query = """
                    SELECT TOP 1 Code as ConceptCode,
                           Label as ConceptLabel,
                           'DimensionalItem' as ConceptType
                    FROM DimensionalItem 
                    WHERE Code LIKE ? OR Label LIKE ?
                    """
                    search_pattern = f"%{clean_name}%"
                    cursor.execute(query, (search_pattern, search_pattern))
                    result = cursor.fetchone()
                    
                    if result:
                        return {
                            'ConceptCode': result[0],
                            'ConceptLabel': result[1], 
                            'ConceptType': result[2],
                            'MetricCode': '',
                            'source': 'DimensionalItem'
                        }
                except:
                    pass
                
                # 2. Try PrimaryItem
                try:
                    query = """
                    SELECT TOP 1 Code as ConceptCode,
                           Label as ConceptLabel,
                           'PrimaryItem' as ConceptType
                    FROM PrimaryItem 
                    WHERE Code LIKE ? OR Label LIKE ?
                    """
                    cursor.execute(query, (search_pattern, search_pattern))
                    result = cursor.fetchone()
                    
                    if result:
                        return {
                            'ConceptCode': result[0],
                            'ConceptLabel': result[1], 
                            'ConceptType': result[2],
                            'MetricCode': '',
                            'source': 'PrimaryItem'
                        }
                except:
                    pass
            else:
                # DMP 4.0 logic
                concept_table = dmp_db.queries_manager.get_actual_table_name('tConcept')
                if concept_table in dmp_db.queries_manager.table_mappings.values():
                    query = f"SELECT ConceptCode, ConceptLabel, ConceptType, MetricCode FROM [{concept_table}] WHERE ConceptCode LIKE ? OR ConceptLabel LIKE ?"
                    search_pattern1 = f"%{clean_name}%"
                    search_pattern2 = f"%{clean_name}%"
                    cursor.execute(query, (search_pattern1, search_pattern2))
                    result = cursor.fetchone()
                    
                    if result:
                        return {
                            'ConceptCode': getattr(result, 'ConceptCode', result[0]),
                            'ConceptLabel': getattr(result, 'ConceptLabel', result[1] if len(result) > 1 else ''),
                            'ConceptType': getattr(result, 'ConceptType', result[2] if len(result) > 2 else ''),
                            'MetricCode': getattr(result, 'MetricCode', result[3] if len(result) > 3 else ''),
                            'source': 'tConcept'
                        }
                
                # Search in datapoint table
                datapoint_table = dmp_db.queries_manager.get_actual_table_name('tDataPoint')
                if datapoint_table in dmp_db.queries_manager.table_mappings.values():
                    query = f"SELECT DataPointCode, DataPointLabel, 'DataPoint' as ConceptType FROM [{datapoint_table}] WHERE DataPointCode LIKE ? OR DataPointLabel LIKE ?"
                    search_pattern1 = f"%{clean_name}%"
                    search_pattern2 = f"%{clean_name}%"
                    cursor.execute(query, (search_pattern1, search_pattern2))
                    result = cursor.fetchone()
                    
                    if result:
                        return {
                            'ConceptCode': getattr(result, 'DataPointCode', result[0]),
                            'ConceptLabel': getattr(result, 'DataPointLabel', result[1] if len(result) > 1 else ''),
                            'ConceptType': 'DataPoint',
                            'MetricCode': getattr(result, 'MetricCode', result[2] if len(result) > 2 else ''),
                            'source': 'tDataPoint'
                        }
            
            return None
            
        except Exception as e:
            logger.error(f"Clean name search failed: {e}")
            return None
    
    def _search_in_member_table(self, concept_name):
        """NEW: Search for concept in Member table using both MemberCode and MemberXbrlCode"""
        try:
            connection = dmp_db.connection_manager.get_connection()
            cursor = connection.cursor()
            
            member_table = dmp_db.queries_manager.get_actual_table_name('tMember')
            if member_table not in dmp_db.queries_manager.table_mappings.values():
                logger.debug(f"Member table not available for concept search")
                return None
            
            # Clean the concept name for better matching
            clean_name = self._clean_concept_name(concept_name)
            
            # Try exact matches first, then partial matches
            search_patterns = [
                (concept_name, "exact match"),
                (clean_name, "clean name exact match"),
                (f"%{concept_name}%", "concept name partial match"),  
                (f"%{clean_name}%", "clean name partial match")
            ]
            
            for pattern, search_type in search_patterns:
                if "partial" in search_type:
                    query = f"""
                    SELECT TOP 1 MemberCode, MemberXbrlCode, MemberLabel
                    FROM [{member_table}] 
                    WHERE MemberCode LIKE ? OR MemberXbrlCode LIKE ?
                    """
                    cursor.execute(query, (pattern, pattern))
                else:
                    query = f"""
                    SELECT MemberCode, MemberXbrlCode, MemberLabel
                    FROM [{member_table}] 
                    WHERE MemberCode = ? OR MemberXbrlCode = ?
                    """
                    cursor.execute(query, (pattern, pattern))
                
                result = cursor.fetchone()
                if result:
                    member_code = getattr(result, 'MemberCode', result[0])
                    member_xbrl_code = getattr(result, 'MemberXbrlCode', result[1] if len(result) > 1 else '')
                    member_label = getattr(result, 'MemberLabel', result[2] if len(result) > 2 else '')
                    
                    logger.info(f"🎯 Found in Member table ({search_type}): {concept_name} -> {member_code} (XBRL: {member_xbrl_code})")
                    
                    return {
                        'ConceptCode': member_code,
                        'ConceptLabel': member_label,
                        'ConceptType': 'Member',
                        'MemberXbrlCode': member_xbrl_code,
                        'MetricCode': '',
                        'source': 'tMember',
                        'searchType': search_type
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Member table search failed for {concept_name}: {e}")
            return None
    
    def _search_by_prefix_variants(self, concept_name):
        """Search using different prefix variants with DMP 3.3 compatibility"""
        try:
            if ':' not in concept_name:
                return None
                
            prefix, local_name = concept_name.split(':', 1)
            
            # Get variants for this prefix
            variants = self.prefix_mappings.get(prefix, [prefix])
            
            connection = dmp_db.connection_manager.get_connection()
            cursor = connection.cursor()
            
            db_version = self._detect_database_version(connection)
            
            if db_version == 'dmp_3_3':
                # Skip prefix variant search for DMP 3.3 to avoid SQL errors
                return None
            else:
                # DMP 4.0 logic
                concept_table = dmp_db.queries_manager.get_actual_table_name('tConcept')
                if concept_table not in dmp_db.queries_manager.table_mappings.values():
                    return None
                
                for variant_prefix in variants:
                    variant_concept = f"{variant_prefix}:{local_name}"
                    query = f"SELECT ConceptCode, ConceptLabel, ConceptType, MetricCode FROM [{concept_table}] WHERE ConceptCode = ?"
                    cursor.execute(query, (variant_concept,))
                    result = cursor.fetchone()
                    
                    if result:
                        return {
                            'ConceptCode': getattr(result, 'ConceptCode', result[0]),
                            'ConceptLabel': getattr(result, 'ConceptLabel', result[1] if len(result) > 1 else ''),
                            'ConceptType': getattr(result, 'ConceptType', result[2] if len(result) > 2 else ''),
                            'MetricCode': getattr(result, 'MetricCode', result[3] if len(result) > 3 else ''),
                            'source': 'tConcept'
                        }
            
            return None
            
        except Exception as e:
            logger.error(f"Prefix variant search failed: {e}")
            return None
    
    def _search_by_partial_match(self, clean_name):
        """Search using partial match with DMP 3.3 compatibility"""
        try:
            connection = dmp_db.connection_manager.get_connection()
            cursor = connection.cursor()
            
            db_version = self._detect_database_version(connection)
            
            if db_version == 'dmp_3_3':
                # Simple query without problematic WHERE clauses
                return None  # Skip partial matching for DMP 3.3 to avoid SQL errors
            else:
                # DMP 4.0 logic
                concept_table = dmp_db.queries_manager.get_actual_table_name('tConcept')
                if concept_table in dmp_db.queries_manager.table_mappings.values():
                    patterns = [clean_name, clean_name.upper(), clean_name.lower()]
                    
                    for pattern in patterns:
                        query = f"SELECT ConceptCode, ConceptLabel, ConceptType, MetricCode FROM [{concept_table}] WHERE ConceptCode LIKE ?"
                        cursor.execute(query, (f"%{pattern}%",))
                        result = cursor.fetchone()
                        
                        if result:
                            return {
                                'ConceptCode': getattr(result, 'ConceptCode', result[0]),
                                'ConceptLabel': getattr(result, 'ConceptLabel', result[1] if len(result) > 1 else ''),
                                'ConceptType': getattr(result, 'ConceptType', result[2] if len(result) > 2 else ''),
                                'MetricCode': getattr(result, 'MetricCode', result[3] if len(result) > 3 else ''),
                                'source': 'tConcept'
                            }
            
            return None
            
        except Exception as e:
            logger.error(f"Partial match search failed: {e}")
            return None
    
    def _search_using_queries_manager(self, concept_name):
        """Use queries manager for concept search"""
        try:
            # Simple fallback search
            return None
            
        except Exception as e:
            logger.error(f"Queries manager search failed: {e}")
            return None
    
    def batch_resolve_concepts(self, concept_list):
        """Batch resolve multiple concepts efficiently"""
        results = {}
        for concept in concept_list:
            results[concept] = self.resolve_concept_from_dmp(concept)
        return results
    
    def get_concept_statistics(self):
        """Get statistics about concept resolution"""
        try:
            connection = dmp_db.connection_manager.get_connection()
            cursor = connection.cursor()
            
            stats = {}
            
            # Count concepts
            concept_table = dmp_db.queries_manager.get_actual_table_name('tConcept')
            if concept_table in dmp_db.queries_manager.table_mappings.values():
                cursor.execute(f"SELECT COUNT(*) FROM [{concept_table}]")
                stats['total_concepts'] = cursor.fetchone()[0]
            
            # Count datapoints
            datapoint_table = dmp_db.queries_manager.get_actual_table_name('tDataPoint')
            if datapoint_table in dmp_db.queries_manager.table_mappings.values():
                cursor.execute(f"SELECT COUNT(*) FROM [{datapoint_table}]")
                stats['total_datapoints'] = cursor.fetchone()[0]
            
            # Count members
            member_table = dmp_db.queries_manager.get_actual_table_name('tMember')
            if member_table in dmp_db.queries_manager.table_mappings.values():
                cursor.execute(f"SELECT COUNT(*) FROM [{member_table}]")
                stats['total_members'] = cursor.fetchone()[0]
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get concept statistics: {e}")
            return {'error': str(e)}
    
    def get_member_statistics(self):
        """Get statistics about Member table"""
        try:
            connection = dmp_db.connection_manager.get_connection()
            cursor = connection.cursor()
            
            member_table = dmp_db.queries_manager.get_actual_table_name('tMember')
            if member_table not in dmp_db.queries_manager.table_mappings.values():
                return {'error': 'Member table not found'}
            
            # Count total members
            cursor.execute(f"SELECT COUNT(*) FROM [{member_table}]")
            total_members = cursor.fetchone()[0]
            
            # Count members with XBRL codes
            cursor.execute(f"SELECT COUNT(*) FROM [{member_table}] WHERE MemberXbrlCode IS NOT NULL AND MemberXbrlCode != ''")
            members_with_xbrl = cursor.fetchone()[0]
            
            # Sample some member codes
            cursor.execute(f"SELECT TOP 10 MemberCode, MemberXbrlCode FROM [{member_table}] WHERE MemberXbrlCode IS NOT NULL")
            sample_members = []
            for row in cursor.fetchall():
                sample_members.append({
                    'memberCode': row[0],
                    'memberXbrlCode': row[1] if len(row) > 1 else ''
                })
            
            return {
                'total_members': total_members,
                'members_with_xbrl_codes': members_with_xbrl,
                'sample_members': sample_members,
                'table_name': member_table
            }
            
        except Exception as e:
            logger.error(f"Failed to get member statistics: {e}")
            return {'error': str(e)}
    
    def _detect_database_version(self, connection) -> str:
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
    
    

# Global instance
concept_resolver = DMPConceptResolver()

