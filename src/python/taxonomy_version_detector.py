"""
Taxonomy Version Detector
========================
Analyzeert XBRL bestanden om de vereiste taxonomy versie te bepalen.
Helpt gebruikers om de juiste taxonomy ZIP te selecteren.
"""

import logging
import xml.etree.ElementTree as ET
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class TaxonomyVersionDetector:
    """
    Detecteert de vereiste taxonomy versie uit XBRL instance bestanden
    """
    
    def __init__(self):
        # Bekende EBA taxonomy versie patterns
        self.version_patterns = {
            # EBA DPM 4.0 (nieuwste)
            'eba_dmp_4.0': {
                'name': 'EBA DPM 4.0',
                'schema_urls': [
                    'www.eba.europa.eu/eu/fr/xbrl/crr/fws/finrep/its-005-2020',
                    'www.eba.europa.eu/eu/fr/xbrl/crr/fws/corep/its-003-2021',
                    'eba.europa.eu/reports/ixbrl/solvency'
                ],
                'namespaces': ['find', 'eba_met', 'eba_dim'],
                'date_range': ['2020-11-15', '2024-12-31'],
                'recommended_zip': 'EBA_CRD_IV_XBRL_2.10_Reporting_Frameworks_2.10.0.1.Errata.zip'
            },
            
            # EBA DPM 3.0 (oudere versie)
            'eba_dmp_3.0': {
                'name': 'EBA DPM 3.0 Phase 2',
                'schema_urls': [
                    'www.eba.europa.eu/eu/fr/xbrl/crr/fws/finrep/its-005-2019',
                    'www.eba.europa.eu/eu/fr/xbrl/crr/fws/corep/its-003-2020'
                ],
                'namespaces': ['finrep', 'corep', 'dpm'],
                'date_range': ['2019-01-01', '2020-11-14'],
                'recommended_zip': 'FullTaxonomy3.0.phase2.zip'
            },
            
            # EBA DPM 2.x (legacy)
            'eba_dmp_2.x': {
                'name': 'EBA DPM 2.x (Legacy)',
                'schema_urls': [
                    'www.eba.europa.eu/eu/fr/xbrl/crr/fws/finrep/its-2018',
                    'www.eba.europa.eu/eu/fr/xbrl/crr/fws/corep/its-2018'
                ],
                'namespaces': ['finrep', 'corep'],
                'date_range': ['2016-01-01', '2018-12-31'],
                'recommended_zip': 'EBA_Legacy_Taxonomy.zip'
            }
        }
    
    def analyze_xbrl_taxonomy_requirements(self, xbrl_path: str) -> Dict:
        """
        Analyzeert XBRL bestand en bepaalt welke taxonomy versie nodig is
        
        Returns:
            Dict met taxonomy informatie en aanbevelingen
        """
        try:
            logger.info(f"🔍 Analyzing taxonomy requirements for: {xbrl_path}")
            
            # Parse XBRL file
            tree = ET.parse(xbrl_path)
            root = tree.getroot()
            
            analysis_result = {
                'file_info': {
                    'filename': xbrl_path.split('/')[-1],
                    'analysis_timestamp': datetime.now().isoformat()
                },
                'detected_version': None,
                'confidence': 'low',
                'recommendations': [],
                'namespace_analysis': {},
                'schema_references': [],
                'reporting_period': None,
                'entity_info': {}
            }
            
            # 1. Extract namespaces
            namespaces = self._extract_namespaces(root)
            analysis_result['namespace_analysis'] = self._analyze_namespaces(namespaces)
            
            # 2. Find schema references
            schema_refs = self._extract_schema_references(root, namespaces)
            analysis_result['schema_references'] = schema_refs
            
            # 3. Extract reporting period
            reporting_period = self._extract_reporting_period(root, namespaces)
            analysis_result['reporting_period'] = reporting_period
            
            # 4. Extract entity information
            entity_info = self._extract_entity_info(root, namespaces)
            analysis_result['entity_info'] = entity_info
            
            # 5. Determine taxonomy version
            detected_version, confidence = self._determine_taxonomy_version(
                namespaces, schema_refs, reporting_period
            )
            
            analysis_result['detected_version'] = detected_version
            analysis_result['confidence'] = confidence
            
            # 6. Generate recommendations
            recommendations = self._generate_recommendations(detected_version, confidence)
            analysis_result['recommendations'] = recommendations
            
            logger.info(f"✅ Taxonomy analysis completed:")
            logger.info(f"   🎯 Detected version: {detected_version}")
            logger.info(f"   📊 Confidence: {confidence}")
            logger.info(f"   📝 Namespaces found: {len(namespaces)}")
            logger.info(f"   🔗 Schema references: {len(schema_refs)}")
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"❌ Taxonomy analysis failed: {e}")
            return {
                'error': str(e),
                'suggestions': [
                    'Controleer of het XBRL bestand geldig is',
                    'Zorg dat het bestand niet beschadigd is',
                    'Probeer een ander XBRL bestand'
                ]
            }
    
    def _extract_namespaces(self, root: ET.Element) -> Dict[str, str]:
        """Extract alle namespace declarations"""
        namespaces = {}
        
        # Root namespaces
        for key, value in root.attrib.items():
            if key.startswith('xmlns:'):
                prefix = key.replace('xmlns:', '')
                namespaces[prefix] = value
            elif key == 'xmlns':
                namespaces['default'] = value
        
        # Ook nested namespaces zoeken (eerste 50 elementen)
        for i, elem in enumerate(root.iter()):
            if i > 50:  # Limit voor performance
                break
            for key, value in elem.attrib.items():
                if key.startswith('xmlns:'):
                    prefix = key.replace('xmlns:', '')
                    if prefix not in namespaces:
                        namespaces[prefix] = value
        
        return namespaces
    
    def _analyze_namespaces(self, namespaces: Dict[str, str]) -> Dict:
        """Analyzeert namespaces voor taxonomy versie hints"""
        
        namespace_analysis = {
            'total_namespaces': len(namespaces),
            'eba_namespaces': {},
            'standard_namespaces': {},
            'version_indicators': []
        }
        
        # Categoriseer namespaces
        for prefix, uri in namespaces.items():
            if 'eba.europa.eu' in uri:
                namespace_analysis['eba_namespaces'][prefix] = uri
                
                # Extract version indicators from URI
                if '2020' in uri:
                    namespace_analysis['version_indicators'].append('DMP_4.0_2020')
                elif '2019' in uri:
                    namespace_analysis['version_indicators'].append('DMP_3.0_2019')
                elif '2018' in uri:
                    namespace_analysis['version_indicators'].append('DMP_2.x_2018')
                    
            elif any(std in uri for std in ['xbrl.org', 'w3.org']):
                namespace_analysis['standard_namespaces'][prefix] = uri
        
        return namespace_analysis
    
    def _extract_schema_references(self, root: ET.Element, namespaces: Dict[str, str]) -> List[str]:
        """Extract schemaLocation references"""
        schema_refs = []
        
        # Zoek schemaLocation attributen
        for elem in root.iter():
            schema_location = elem.get('schemaLocation')
            if schema_location:
                # Split op whitespace en pak URLs
                locations = schema_location.split()
                for i in range(1, len(locations), 2):  # Elke 2e entry is een URL
                    if locations[i].startswith('http'):
                        schema_refs.append(locations[i])
        
        return list(set(schema_refs))  # Remove duplicates
    
    def _extract_reporting_period(self, root: ET.Element, namespaces: Dict[str, str]) -> Optional[str]:
        """Extract reporting period from XBRL contexts"""
        try:
            # Zoek context elementen
            for elem in root.iter():
                if elem.tag.endswith('context'):
                    period_elem = elem.find('.//*[local-name()="instant"]') or elem.find('.//*[local-name()="period"]')
                    if period_elem is not None:
                        return period_elem.text
                        
            # Fallback: zoek in filename
            filename = root.base or ""
            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
            if date_match:
                return date_match.group(1)
                
        except Exception as e:
            logger.warning(f"Could not extract reporting period: {e}")
        
        return None
    
    def _extract_entity_info(self, root: ET.Element, namespaces: Dict[str, str]) -> Dict:
        """Extract entity information"""
        entity_info = {}
        
        try:
            # Zoek entity identifier
            for elem in root.iter():
                if elem.tag.endswith('identifier'):
                    entity_info['identifier'] = elem.text
                    entity_info['scheme'] = elem.get('scheme', '')
                    
        except Exception as e:
            logger.warning(f"Could not extract entity info: {e}")
        
        return entity_info
    
    def _determine_taxonomy_version(self, namespaces: Dict[str, str], 
                                  schema_refs: List[str], 
                                  reporting_period: Optional[str]) -> Tuple[str, str]:
        """Bepaal taxonomy versie op basis van gevonden informatie"""
        
        # Score elke versie
        version_scores = {}
        
        for version_key, version_info in self.version_patterns.items():
            score = 0
            
            # Check schema URL matches
            for schema_ref in schema_refs:
                for pattern in version_info['schema_urls']:
                    if pattern in schema_ref:
                        score += 10
            
            # Check namespace matches
            for namespace_prefix in namespaces.keys():
                if namespace_prefix in version_info['namespaces']:
                    score += 5
            
            # Check reporting period
            if reporting_period and version_info['date_range']:
                start_date, end_date = version_info['date_range']
                if start_date <= reporting_period <= end_date:
                    score += 3
            
            version_scores[version_key] = score
        
        # Bepaal beste match
        if not version_scores or max(version_scores.values()) == 0:
            return 'unknown', 'none'
        
        best_version = max(version_scores, key=version_scores.get)
        best_score = version_scores[best_version]
        
        # Bepaal confidence level
        if best_score >= 10:
            confidence = 'high'
        elif best_score >= 5:
            confidence = 'medium'
        else:
            confidence = 'low'
        
        return best_version, confidence
    
    def _generate_recommendations(self, detected_version: str, confidence: str) -> List[Dict]:
        """Genereer aanbevelingen voor taxonomy selectie"""
        recommendations = []
        
        if detected_version == 'unknown':
            recommendations.append({
                'type': 'warning',
                'title': 'Taxonomy versie niet herkend',
                'message': 'Kon geen bekende EBA taxonomy versie detecteren in het XBRL bestand.',
                'action': 'Probeer handmatig de juiste taxonomy te selecteren op basis van de rapportage datum.'
            })
            
            # Suggest default
            recommendations.append({
                'type': 'suggestion',
                'title': 'Standaard aanbeveling',
                'message': 'Voor moderne XBRL bestanden (2020+) gebruik EBA DMP 4.0',
                'taxonomy_file': 'EBA_CRD_IV_XBRL_2.10_Reporting_Frameworks_2.10.0.1.Errata.zip'
            })
            
        else:
            version_info = self.version_patterns[detected_version]
            
            recommendations.append({
                'type': 'success',
                'title': f'Aanbevolen taxonomy: {version_info["name"]}',
                'message': f'Detectie confidence: {confidence}',
                'taxonomy_file': version_info['recommended_zip'],
                'confidence': confidence
            })
            
            if confidence != 'high':
                recommendations.append({
                    'type': 'info',
                    'title': 'Verificatie aanbevolen',
                    'message': 'Controleer of de aanbevolen taxonomy overeenkomt met uw verwachting.',
                    'action': 'Vergelijk de gevonden namespaces en schema referenties.'
                })
        
        return recommendations

def get_taxonomy_recommendations(xbrl_path: str) -> Dict:
    """
    Convenience functie voor het krijgen van taxonomy aanbevelingen
    """
    detector = TaxonomyVersionDetector()
    return detector.analyze_xbrl_taxonomy_requirements(xbrl_path)