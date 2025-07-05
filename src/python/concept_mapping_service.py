
import logging
from dmp_concept_resolver import concept_resolver

logger = logging.getLogger(__name__)

class ConceptMappingService:
    def __init__(self):
        self.concept_resolver = concept_resolver
        self.mapping_cache = {}
    
    def pre_validate_concepts(self, xbrl_file_path, taxonomy_concepts=None):
        """
        Pre-validate concepts by mapping XBRL concepts to DMP database BEFORE Arelle validation
        """
        try:
            logger.info("🔍 Starting pre-validation concept mapping")
            
            # Extract concepts from XBRL file
            xbrl_concepts = self._extract_concepts_from_xbrl(xbrl_file_path)
            logger.info(f"📄 Extracted {len(xbrl_concepts)} concepts from XBRL")
            
            # Map concepts to DMP database
            mapping_results = {
                'resolved': {},
                'unresolved': [],
                'taxonomy_missing': [],
                'dmp_available': []
            }
            
            for concept in xbrl_concepts:
                # Check if concept exists in taxonomy (if provided)
                in_taxonomy = taxonomy_concepts and concept in taxonomy_concepts
                
                # Try to resolve in DMP database
                dmp_concept = self.concept_resolver.resolve_concept_from_dmp(concept)
                
                if dmp_concept:
                    mapping_results['resolved'][concept] = dmp_concept
                    if not in_taxonomy:
                        mapping_results['dmp_available'].append(concept)
                        logger.info(f"🎯 DMP AVAILABLE: {concept} -> {dmp_concept['ConceptCode']}")
                else:
                    mapping_results['unresolved'].append(concept)
                    if not in_taxonomy:
                        mapping_results['taxonomy_missing'].append(concept)
                        logger.warning(f"❌ MISSING EVERYWHERE: {concept}")
            
            logger.info(f"🎯 Pre-validation mapping results:")
            logger.info(f"   ✅ Resolved in DMP: {len(mapping_results['resolved'])}")
            logger.info(f"   ❌ Unresolved: {len(mapping_results['unresolved'])}")
            logger.info(f"   📦 Available in DMP but missing from taxonomy: {len(mapping_results['dmp_available'])}")
            logger.info(f"   🚫 Missing everywhere: {len(mapping_results['taxonomy_missing'])}")
            
            return mapping_results
            
        except Exception as e:
            logger.error(f"❌ Pre-validation concept mapping failed: {str(e)}")
            return {'resolved': {}, 'unresolved': [], 'taxonomy_missing': [], 'dmp_available': []}
    
    def _extract_concepts_from_xbrl(self, xbrl_file_path):
        """Extract EBA concepts from XBRL instance file"""
        concepts = set()
        
        try:
            with open(xbrl_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Look for EBA concept patterns
            import re
            patterns = [
                r'\b(eba_met[^:\s]*:[A-Za-z][A-Za-z0-9_]*)\b',
                r'\b(find:[A-Za-z][A-Za-z0-9_]*)\b',
                r'<([^>\s]+:[A-Za-z][A-Za-z0-9_]+)[>\s]'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, tuple):
                        match = match[0] if match[0] else match[1]
                    if ':' in match and len(match) > 5:
                        concepts.add(match)
            
            return list(concepts)
            
        except Exception as e:
            logger.error(f"❌ Failed to extract concepts from XBRL: {str(e)}")
            return []
    
    def generate_missing_schema_elements(self, dmp_available_concepts):
        """Generate XSD schema elements for concepts available in DMP but missing from taxonomy"""
        try:
            if not dmp_available_concepts:
                return None
            
            logger.info(f"🔧 Generating schema elements for {len(dmp_available_concepts)} DMP concepts")
            
            schema_elements = []
            for concept_name in dmp_available_concepts:
                dmp_concept = self.concept_resolver.resolve_concept_from_dmp(concept_name)
                if dmp_concept:
                    element = self._create_xsd_element(concept_name, dmp_concept)
                    schema_elements.append(element)
            
            if schema_elements:
                # Create temporary XSD file
                temp_schema_path = self._create_temporary_schema(schema_elements)
                logger.info(f"✅ Generated temporary schema: {temp_schema_path}")
                return temp_schema_path
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to generate missing schema elements: {str(e)}")
            return None
    
    def _create_xsd_element(self, concept_name, dmp_concept):
        """Create XSD element definition for DMP concept"""
        prefix, local_name = concept_name.split(':', 1) if ':' in concept_name else ('', concept_name)
        
        element = f'''
    <xs:element name="{local_name}" type="xbrli:monetaryItemType" substitutionGroup="xbrli:item" 
                id="{concept_name}" nillable="true">
        <xs:annotation>
            <xs:documentation xml:lang="en">
                {dmp_concept.get('ConceptLabel', local_name)} (Generated from DMP 4.0 Database)
            </xs:documentation>
        </xs:annotation>
    </xs:element>'''
        
        return element
    
    def _create_temporary_schema(self, schema_elements):
        """Create temporary XSD schema file with generated elements"""
        import tempfile
        
        schema_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
           xmlns:xbrli="http://www.xbrl.org/2003/instance"
           xmlns:eba_met="http://www.eba.europa.eu/xbrl/crr/dict/met"
           xmlns:find="http://www.eurofiling.info/xbrl/ext/filing-indicators"
           targetNamespace="http://www.eba.europa.eu/xbrl/crr/dict/met"
           elementFormDefault="qualified">
           
    <xs:import namespace="http://www.xbrl.org/2003/instance" 
               schemaLocation="http://www.xbrl.org/2003/xbrl-instance-2003-12-31.xsd"/>
    
    <!-- Generated elements from DMP 4.0 Database -->
    {"".join(schema_elements)}
    
</xs:schema>'''
        
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.xsd', delete=False, encoding='utf-8')
        temp_file.write(schema_content)
        temp_file.close()
        
        return temp_file.name
