"""
XBRL Fact Parser Module
======================
Advanced XBRL instance file parser that extracts facts, contexts, and units
with support for complex dimensional structures and EBA-specific patterns.
"""

import logging
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional, Tuple
import re

logger = logging.getLogger(__name__)

class XBRLFactParser:
    """
    Advanced XBRL fact parser with support for:
    - Multi-namespace fact extraction
    - Context and unit parsing
    - Dimensional analysis
    - EBA-specific patterns
    - Fact relationship discovery
    """
    
    def __init__(self):
        # Skip these namespaces during fact extraction
        self.skip_namespaces = {
            'http://www.xbrl.org/2003/instance',
            'http://www.w3.org/2001/XMLSchema-instance', 
            'http://www.xbrl.org/2003/linkbase',
            'http://www.w3.org/1999/xlink',
            'http://www.w3.org/2001/XMLSchema'
        }
        
        # Common EBA namespace patterns
        self.eba_namespace_patterns = [
            'eba_',
            'corep',
            'finrep',
            'find',
            'met'
        ]
        
        logger.info("📄 XBRL Fact Parser initialized")
    
    def parse_xbrl_instance(self, xbrl_path: str) -> Dict[str, Any]:
        """
        Parse XBRL instance file and extract comprehensive fact information
        
        Args:
            xbrl_path: Path to XBRL instance file
            
        Returns:
            Dictionary containing facts, contexts, units, and metadata
        """
        
        try:
            logger.info(f"📖 Parsing XBRL instance: {xbrl_path}")
            
            # Parse XML
            tree = ET.parse(xbrl_path)
            root = tree.getroot()
            
            # Extract namespaces
            namespaces = self._extract_namespaces(root)
            
            # Parse main components
            facts = self._parse_facts(root, namespaces)
            contexts = self._parse_contexts(root, namespaces)
            units = self._parse_units(root, namespaces)
            
            # Enrich facts with context and unit information
            enriched_facts = self._enrich_facts_with_context(facts, contexts, units)
            
            # Generate parsing statistics
            parsing_stats = self._generate_parsing_statistics(enriched_facts, namespaces, contexts, units)
            
            result = {
                'facts': enriched_facts,
                'contexts': contexts,
                'units': units,
                'namespaces': namespaces,
                'parsing_statistics': parsing_stats,
                'file_path': xbrl_path
            }
            
            logger.info(f"✅ Parsed {len(enriched_facts)} facts from {len(namespaces)} namespaces")
            return result
            
        except ET.ParseError as e:
            logger.error(f"❌ XML parsing error: {e}")
            return {'error': f'XML parsing failed: {str(e)}', 'facts': {}}
        except Exception as e:
            logger.error(f"❌ XBRL parsing failed: {e}")
            return {'error': f'XBRL parsing failed: {str(e)}', 'facts': {}}
    
    def _extract_namespaces(self, root: ET.Element) -> Dict[str, str]:
        """Extract namespace mappings from XBRL root element with enhanced detection"""
        
        namespaces = {}
        
        # Extract from root attributes
        for key, value in root.attrib.items():
            if key.startswith('xmlns:'):
                prefix = key.replace('xmlns:', '')
                namespaces[prefix] = value
                logger.debug(f"Found namespace prefix: {prefix} -> {value}")
            elif key == 'xmlns':
                namespaces['default'] = value
                logger.debug(f"Found default namespace: {value}")
        
        # ENHANCED: Also check for namespaces in document tree if root has none
        if not namespaces or len(namespaces) < 3:
            logger.warning("⚠️ Few/no namespaces in root, scanning document...")
            # Scan more elements for namespace declarations
            for i, element in enumerate(root.iter()):
                for key, value in element.attrib.items():
                    if key.startswith('xmlns:'):
                        prefix = key.replace('xmlns:', '')
                        if prefix not in namespaces:
                            namespaces[prefix] = value
                            logger.debug(f"Found namespace in element {i}: {prefix} -> {value}")
                    elif key == 'xmlns' and 'default' not in namespaces:
                        namespaces['default'] = value
                        logger.debug(f"Found default namespace in element {i}: {value}")
                
                # Stop scanning after finding sufficient namespaces or after 100 elements
                if len(namespaces) > 10 or i > 100:
                    break
        
        # Enhanced logging for debugging
        eba_namespaces = {prefix: uri for prefix, uri in namespaces.items() 
                         if any(pattern in prefix.lower() for pattern in self.eba_namespace_patterns)}
        
        logger.info(f"📊 Total namespaces found: {len(namespaces)}")
        if eba_namespaces:
            logger.info(f"🎯 Found {len(eba_namespaces)} EBA-related namespaces: {list(eba_namespaces.keys())}")
        
        if namespaces:
            # Show all namespaces for debugging
            namespace_sample = dict(list(namespaces.items())[:10])
            logger.info(f"📝 Namespace sample: {namespace_sample}")
            
            # Log architecture-relevant namespaces
            arch_relevant = {prefix: uri for prefix, uri in namespaces.items() 
                           if any(pattern in uri.lower() for pattern in ['dpm', 'eba', 'finrep', 'corep', 'crr'])}
            if arch_relevant:
                logger.info(f"🏗️ Architecture-relevant namespaces: {arch_relevant}")
        else:
            logger.warning("⚠️ No namespaces found in XBRL document - architecture detection will fail")
        
        return namespaces
    
    def _parse_facts(self, root: ET.Element, namespaces: Dict[str, str]) -> Dict[str, Any]:
        """Extract business facts from XBRL instance, filtering structural elements"""
        
        facts = {}
        elements_processed = 0
        facts_found = 0
        business_facts_found = 0
        structural_elements_skipped = 0
        
        # ENHANCED: Skip structural elements that are not business concepts
        structural_elements = {
            'facts', 'contexts', 'units', 'namespaces', 'parsing_statistics', 'file_path',
            'context', 'unit', 'schemaRef', 'linkbaseRef', 'roleRef', 'arcroleRef'
        }
        
        for element in root:
            elements_processed += 1
            if not element.tag or not element.tag.startswith('{'):
                continue
            
            # Parse namespace and local name
            namespace_info = self._parse_element_namespace(element.tag)
            if not namespace_info:
                continue
            
            namespace_uri, local_name = namespace_info
            
            # Skip XBRL infrastructure namespaces
            if namespace_uri in self.skip_namespaces:
                continue
            
            # ENHANCED: Skip structural elements
            if local_name.lower() in structural_elements:
                structural_elements_skipped += 1
                logger.debug(f"🚫 Skipped structural element: {local_name}")
                continue
            
            # Find namespace prefix
            prefix = self._find_namespace_prefix(namespace_uri, namespaces)
            if not prefix:
                # Try to create a temporary prefix for unknown namespaces
                prefix = f"ns{len([p for p in namespaces.keys() if p.startswith('ns')])}"
                namespaces[prefix] = namespace_uri
                logger.debug(f"🔧 Created temporary prefix '{prefix}' for namespace: {namespace_uri}")
            
            facts_found += 1
            
            # Check if this is a business concept
            is_business_concept = self._is_business_concept(prefix, local_name)
            if is_business_concept:
                business_facts_found += 1
            
            # Create fact name
            fact_name = f"{prefix}:{local_name}"
            
            # Extract fact data
            fact_data = {
                'value': element.text,
                'context_ref': element.get('contextRef'),
                'unit_ref': element.get('unitRef'),
                'decimals': element.get('decimals'),
                'precision': element.get('precision'),
                'prefix': prefix,
                'local_name': local_name,
                'namespace_uri': namespace_uri,
                'attributes': dict(element.attrib),
                'is_business_concept': is_business_concept
            }
            
            # Handle duplicate facts (multiple instances)
            if fact_name in facts:
                # Convert to list if not already
                if not isinstance(facts[fact_name], list):
                    facts[fact_name] = [facts[fact_name]]
                facts[fact_name].append(fact_data)
            else:
                facts[fact_name] = fact_data
        
        # Enhanced debugging for fact parsing
        logger.info(f"📊 Fact parsing completed: {elements_processed} elements processed, {facts_found} potential facts, {len(facts)} facts extracted")
        logger.info(f"🏢 Business concepts found: {business_facts_found}, Structural elements skipped: {structural_elements_skipped}")
        
        if len(facts) == 0 and elements_processed > 0:
            logger.warning(f"⚠️ No facts extracted despite processing {elements_processed} elements - possible namespace or parsing issues")
        
        return facts
    
    def _is_business_concept(self, prefix: str, local_name: str) -> bool:
        """Enhanced business concept detection for better pipeline connectivity"""
        # Enhanced business concept patterns for better detection
        business_prefixes = ['eba_met', 'eba_dim', 'find', 'finrep', 'corep', 'met', 'dim', 'xbrl', 'gb']
        business_patterns = ['md', 'mi', 'c_', 'r_', 'dp_', 'qcef', 'qaof', 'qfaf', 'lcr', 'nsfr']
        
        # Always consider non-xbrl namespace concepts as business concepts
        prefix_lower = prefix.lower()
        
        # Enhanced prefix checking
        if any(bp in prefix_lower for bp in business_prefixes):
            logger.debug(f"✅ Business concept by prefix: {prefix}:{local_name}")
            return True
        
        # Enhanced local name pattern checking
        local_lower = local_name.lower()
        if any(pattern in local_lower for pattern in business_patterns):
            logger.debug(f"✅ Business concept by pattern: {prefix}:{local_name}")
            return True
        
        # Enhanced concept patterns - more inclusive for FINREP files
        if len(local_name) > 2:
            # Check for typical EBA/FINREP patterns
            if (local_name[:2].isalpha() and any(c.isdigit() for c in local_name)) or \
               (local_name.startswith(('m', 'c', 'r', 'q')) and len(local_name) > 3) or \
               ('_' in local_name and len(local_name) > 4):
                logger.debug(f"✅ Business concept by structure: {prefix}:{local_name}")
                return True
        
        # Consider anything with non-XBRL namespace as potentially business
        if prefix_lower not in ['xbrl', 'xml', 'xsi', 'link', 'xlink']:
            logger.debug(f"✅ Business concept by non-structural namespace: {prefix}:{local_name}")
            return True
        
        logger.debug(f"❌ Non-business concept: {prefix}:{local_name}")
        return False
    
    def _parse_contexts(self, root: ET.Element, namespaces: Dict[str, str]) -> Dict[str, Any]:
        """Parse context definitions"""
        
        contexts = {}
        
        # Look for context elements
        for element in root:
            if self._is_xbrl_element(element, 'context'):
                context_id = element.get('id')
                if not context_id:
                    continue
                
                context_data = {
                    'id': context_id,
                    'entity': None,
                    'period': None,
                    'scenario': None,
                    'dimensions': {}
                }
                
                # Parse context components
                for child in element:
                    if self._is_xbrl_element(child, 'entity'):
                        context_data['entity'] = self._parse_entity(child)
                    elif self._is_xbrl_element(child, 'period'):
                        context_data['period'] = self._parse_period(child)
                    elif self._is_xbrl_element(child, 'scenario'):
                        context_data['scenario'] = self._parse_scenario(child, namespaces)
                
                contexts[context_id] = context_data
        
        return contexts
    
    def _parse_units(self, root: ET.Element, namespaces: Dict[str, str]) -> Dict[str, Any]:
        """Parse unit definitions"""
        
        units = {}
        
        for element in root:
            if self._is_xbrl_element(element, 'unit'):
                unit_id = element.get('id')
                if not unit_id:
                    continue
                
                unit_data = {
                    'id': unit_id,
                    'measures': []
                }
                
                # Parse unit measures
                for child in element:
                    if self._is_xbrl_element(child, 'measure'):
                        measure = child.text
                        if measure:
                            unit_data['measures'].append(measure)
                    elif self._is_xbrl_element(child, 'divide'):
                        # Handle complex units (ratios)
                        unit_data['type'] = 'ratio'
                        unit_data['numerator'] = []
                        unit_data['denominator'] = []
                        
                        for div_child in child:
                            if self._is_xbrl_element(div_child, 'unitNumerator'):
                                for measure in div_child:
                                    if self._is_xbrl_element(measure, 'measure') and measure.text:
                                        unit_data['numerator'].append(measure.text)
                            elif self._is_xbrl_element(div_child, 'unitDenominator'):
                                for measure in div_child:
                                    if self._is_xbrl_element(measure, 'measure') and measure.text:
                                        unit_data['denominator'].append(measure.text)
                
                units[unit_id] = unit_data
        
        return units
    
    def _parse_entity(self, entity_element: ET.Element) -> Dict[str, Any]:
        """Parse entity information from context"""
        
        entity_data = {}
        
        for child in entity_element:
            if self._is_xbrl_element(child, 'identifier'):
                entity_data['identifier'] = {
                    'scheme': child.get('scheme'),
                    'value': child.text
                }
            elif self._is_xbrl_element(child, 'segment'):
                entity_data['segment'] = self._parse_segment_or_scenario(child)
        
        return entity_data
    
    def _parse_period(self, period_element: ET.Element) -> Dict[str, Any]:
        """Parse period information from context"""
        
        period_data = {}
        
        for child in period_element:
            if self._is_xbrl_element(child, 'instant'):
                period_data['type'] = 'instant'
                period_data['instant'] = child.text
            elif self._is_xbrl_element(child, 'startDate'):
                period_data['type'] = 'duration'
                period_data['start_date'] = child.text
            elif self._is_xbrl_element(child, 'endDate'):
                period_data['end_date'] = child.text
        
        return period_data
    
    def _parse_scenario(self, scenario_element: ET.Element, namespaces: Dict[str, str]) -> Dict[str, Any]:
        """Parse scenario with dimensional information"""
        return self._parse_segment_or_scenario(scenario_element, namespaces)
    
    def _parse_segment_or_scenario(self, element: ET.Element, namespaces: Dict[str, str] = None) -> Dict[str, Any]:
        """Parse segment or scenario element for dimensional data"""
        
        data = {'dimensions': {}}
        
        for child in element:
            if 'explicitMember' in child.tag:
                dimension = child.get('dimension')
                member_value = child.text
                
                if dimension and member_value:
                    # Try to resolve namespace prefixes
                    if namespaces and ':' in dimension:
                        prefix, local_dim = dimension.split(':', 1)
                        if prefix in namespaces:
                            dimension = f"{prefix}:{local_dim}"
                    
                    data['dimensions'][dimension] = {
                        'type': 'explicit',
                        'value': member_value
                    }
            
            elif 'typedMember' in child.tag:
                dimension = child.get('dimension')
                if dimension:
                    data['dimensions'][dimension] = {
                        'type': 'typed',
                        'value': child.text or 'N/A'
                    }
        
        return data
    
    def _enrich_facts_with_context(self, facts: Dict[str, Any], contexts: Dict[str, Any], 
                                 units: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich facts with full context and unit information"""
        
        enriched_facts = {}
        
        for fact_name, fact_data in facts.items():
            # Handle both single facts and fact lists
            if isinstance(fact_data, list):
                enriched_facts[fact_name] = [
                    self._enrich_single_fact(fd, contexts, units) for fd in fact_data
                ]
            else:
                enriched_facts[fact_name] = self._enrich_single_fact(fact_data, contexts, units)
        
        return enriched_facts
    
    def _enrich_single_fact(self, fact_data: Dict[str, Any], contexts: Dict[str, Any], 
                          units: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich a single fact with context and unit details"""
        
        enriched = fact_data.copy()
        
        # Add context details
        context_ref = fact_data.get('context_ref')
        if context_ref and context_ref in contexts:
            enriched['context_details'] = contexts[context_ref]
        
        # Add unit details
        unit_ref = fact_data.get('unit_ref')
        if unit_ref and unit_ref in units:
            enriched['unit_details'] = units[unit_ref]
        
        # Add derived information
        enriched['has_dimensions'] = bool(
            enriched.get('context_details', {}).get('scenario', {}).get('dimensions') or
            enriched.get('context_details', {}).get('entity', {}).get('segment', {}).get('dimensions')
        )
        
        return enriched
    
    def _generate_parsing_statistics(self, facts: Dict[str, Any], namespaces: Dict[str, str],
                                   contexts: Dict[str, Any], units: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive parsing statistics"""
        
        stats = {
            'total_facts': len(facts),
            'total_contexts': len(contexts),
            'total_units': len(units),
            'total_namespaces': len(namespaces),
            'facts_by_namespace': {},
            'dimensional_facts': 0,
            'numeric_facts': 0,
            'text_facts': 0,
            'eba_facts': 0
        }
        
        # Analyze facts
        for fact_name, fact_data in facts.items():
            # Handle fact lists
            fact_instances = fact_data if isinstance(fact_data, list) else [fact_data]
            
            for fact_instance in fact_instances:
                prefix = fact_instance.get('prefix', '')
                
                # Count by namespace
                stats['facts_by_namespace'][prefix] = stats['facts_by_namespace'].get(prefix, 0) + 1
                
                # Count dimensional facts
                if fact_instance.get('has_dimensions'):
                    stats['dimensional_facts'] += 1
                
                # Count fact types
                value = fact_instance.get('value', '')
                if value:
                    try:
                        float(value)
                        stats['numeric_facts'] += 1
                    except (ValueError, TypeError):
                        stats['text_facts'] += 1
                
                # Count EBA facts
                if any(pattern in prefix.lower() for pattern in self.eba_namespace_patterns):
                    stats['eba_facts'] += 1
        
        # Add namespace analysis
        eba_namespaces = {prefix: uri for prefix, uri in namespaces.items() 
                         if any(pattern in prefix.lower() for pattern in self.eba_namespace_patterns)}
        
        stats['eba_namespaces'] = len(eba_namespaces)
        stats['eba_namespace_list'] = list(eba_namespaces.keys())
        
        return stats
    
    # Helper methods
    
    def _parse_element_namespace(self, tag: str) -> Optional[Tuple[str, str]]:
        """Parse element tag to extract namespace URI and local name"""
        if not tag.startswith('{'):
            return None
        
        namespace_end = tag.find('}')
        if namespace_end == -1:
            return None
        
        namespace_uri = tag[1:namespace_end]
        local_name = tag[namespace_end + 1:]
        
        return namespace_uri, local_name
    
    def _find_namespace_prefix(self, namespace_uri: str, namespaces: Dict[str, str]) -> Optional[str]:
        """Find prefix for a namespace URI"""
        for prefix, uri in namespaces.items():
            if uri == namespace_uri:
                return prefix
        return None
    
    def _is_xbrl_element(self, element: ET.Element, local_name: str) -> bool:
        """Check if element is an XBRL element with specific local name"""
        return (element.tag.endswith(f'}}{local_name}') and 
                'xbrl.org' in element.tag)
    
    def get_fact_summary(self, facts: Dict[str, Any]) -> Dict[str, Any]:
        """Get a summary of parsed facts for debugging"""
        
        summary = {
            'total_facts': len(facts),
            'sample_facts': {},
            'namespaces_found': set(),
            'fact_types': {}
        }
        
        # Sample first few facts from each namespace
        namespace_samples = {}
        
        for fact_name, fact_data in list(facts.items())[:20]:  # Limit to first 20 for summary
            fact_instance = fact_data if not isinstance(fact_data, list) else fact_data[0]
            prefix = fact_instance.get('prefix', 'unknown')
            
            summary['namespaces_found'].add(prefix)
            
            if prefix not in namespace_samples:
                namespace_samples[prefix] = []
            
            if len(namespace_samples[prefix]) < 3:  # Max 3 samples per namespace
                namespace_samples[prefix].append({
                    'fact_name': fact_name,
                    'value': fact_instance.get('value', '')[:50],  # Truncate long values
                    'has_context': bool(fact_instance.get('context_ref')),
                    'has_unit': bool(fact_instance.get('unit_ref'))
                })
        
        summary['sample_facts'] = namespace_samples
        summary['namespaces_found'] = list(summary['namespaces_found'])
        
        return summary