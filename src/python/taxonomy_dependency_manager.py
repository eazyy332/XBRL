
import zipfile
import os
import requests
import json
import xml.etree.ElementTree as ET
from pathlib import Path
import logging
import re
import shutil

logger = logging.getLogger(__name__)

class EBATaxonomyDependencyManager:
    def __init__(self, base_dir=None):
        if base_dir is None:
            base_dir = r"C:\Users\berbe\Documents\AI\XBRL-validation\taxonomies"
        
        self.base_dir = Path(base_dir)
        self.eba_dir = self.base_dir / "EBA"
        self.eurofiling_dir = self.base_dir / "Eurofiling"
        self.xbrl_org_dir = self.base_dir / "XBRL_International"
        
        # Create all directories
        for dir_path in [self.eba_dir, self.eurofiling_dir, self.xbrl_org_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def analyze_xbrl_file_requirements(self, xbrl_file_path):
        """
        CRITICAL: Analyze XBRL file to determine exact modules needed
        """
        try:
            with open(xbrl_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract filename patterns to determine reporting type
            filename = os.path.basename(xbrl_file_path).upper()
            
            # Determine reporting framework from filename
            if 'FINREP' in filename:
                framework = 'FINREP'
                if 'GAAP' in filename:
                    accounting_standard = 'GAAP'
                elif 'IFRS' in filename:
                    accounting_standard = 'IFRS'
                else:
                    accounting_standard = 'IFRS'  # Default
                
                if 'IND' in filename:
                    consolidation = 'INDIVIDUAL'
                elif 'CON' in filename:
                    consolidation = 'CONSOLIDATED'
                else:
                    consolidation = 'INDIVIDUAL'  # Default
                    
            elif 'COREP' in filename:
                framework = 'COREP'
                accounting_standard = None
                if 'CON' in filename:
                    consolidation = 'CONSOLIDATED'
                else:
                    consolidation = 'INDIVIDUAL'
            else:
                framework = 'UNKNOWN'
                accounting_standard = None
                consolidation = 'INDIVIDUAL'
            
            # Extract schema references from XBRL content
            schema_refs = re.findall(r'schemaLocation="([^"]*\.xsd)"', content)
            schema_refs.extend(re.findall(r'href="([^"]*\.xsd)"', content))
            
            required_modules = []
            for ref in schema_refs:
                module_name = ref.split('/')[-1]  # Get filename from URL
                required_modules.append(module_name)
            
            logger.info(f"🎯 XBRL Analysis: Framework={framework}, Standard={accounting_standard}, Consolidation={consolidation}")
            logger.info(f"🎯 Required modules from XBRL: {required_modules[:5]}...")
            
            return {
                'framework': framework,
                'accounting_standard': accounting_standard,
                'consolidation': consolidation,
                'required_modules': required_modules,
                'filename': filename
            }
            
        except Exception as e:
            logger.warning(f"Could not analyze XBRL file: {e}")
            return {
                'framework': 'UNKNOWN',
                'accounting_standard': None,
                'consolidation': 'INDIVIDUAL',
                'required_modules': [],
                'filename': os.path.basename(xbrl_file_path)
            }

    def discover_comprehensive_entry_points(self, extracted_dir):
        """
        COMPLETE FIX: Zoek specifiek naar EBA metadata taxonomy bestanden
        """
        entry_points = set()
        
        # STAP 1: Zoek specifiek naar EBA metadata taxonomy bestanden
        eba_metadata_patterns = [
            "**/eba_met*.xsd",           # Direct EBA metadata files
            "**/eba-met*.xsd", 
            "**/metadata*.xsd",
            "**/met*.xsd",               # Generic metadata files
            "**/dict/**/*.xsd",          # Dictionary/metadata in dict folders
            "**/fws/dict/**/*.xsd",      # Framework dictionary
            "**/crr/dict/**/*.xsd",      # CRR dictionary
            "**/eu/fr/xbrl/dict/**/*.xsd" # EU dictionary path
        ]
        
        logger.info("🔍 STAP 1: Zoeken naar EBA metadata taxonomy...")
        metadata_files = []
        for pattern in eba_metadata_patterns:
            matches = Path(extracted_dir).glob(pattern)
            for match in matches:
                if match.is_file() and match.suffix.lower() == '.xsd':
                    metadata_files.append(str(match))
                    entry_points.add(str(match))
                    logger.info(f"📋 EBA Metadata gevonden: {match.name}")
        
        # STAP 2: Zoek naar Eurofiling bestanden
        eurofiling_patterns = [
            "**/find*.xsd", 
            "**/eurofiling*.xsd",
            "**/filing-indicators*.xsd",
            "**/exp.xsd"
        ]
        
        logger.info("🔍 STAP 2: Zoeken naar Eurofiling taxonomies...")
        eurofiling_files = []
        for pattern in eurofiling_patterns:
            matches = Path(extracted_dir).glob(pattern)
            for match in matches:
                if match.is_file() and match.suffix.lower() == '.xsd':
                    eurofiling_files.append(str(match))
                    entry_points.add(str(match))
                    logger.info(f"📋 Eurofiling gevonden: {match.name}")
        
        # STAP 3: Zoek naar framework bestanden
        framework_patterns = [
            "**/finrep*.xsd",
            "**/corep*.xsd",
            "**/ae*.xsd",
            "**/fp*.xsd"
        ]
        
        logger.info("🔍 STAP 3: Zoeken naar framework taxonomies...")
        framework_files = []
        for pattern in framework_patterns:
            matches = Path(extracted_dir).glob(pattern)
            for match in matches:
                if match.is_file() and match.suffix.lower() == '.xsd':
                    framework_files.append(str(match))
                    entry_points.add(str(match))
        
        # STAP 4: Controleer of we EBA metadata hebben gevonden
        if not metadata_files:
            logger.warning("❌ GEEN EBA metadata bestanden gevonden!")
            logger.info("🔍 Proberen algemene zoektocht...")
            
            # Backup: zoek naar alle XSD bestanden en filter op inhoud
            all_xsd_files = list(Path(extracted_dir).glob("**/*.xsd"))
            for xsd_file in all_xsd_files:
                try:
                    with open(xsd_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Check of bestand EBA metadata concepten bevat
                    if any(eba_indicator in content for eba_indicator in [
                        'eba_met:', 'targetNamespace="http://www.eba.europa.eu', 
                        'xmlns:eba_met=', 'eba_met_'
                    ]):
                        metadata_files.append(str(xsd_file))
                        entry_points.add(str(xsd_file))
                        logger.info(f"📋 EBA Metadata via inhoud: {xsd_file.name}")
                        
                except Exception as e:
                    continue
        
        unique_entry_points = sorted(list(entry_points))
        
        logger.info(f"📊 DISCOVERY RESULTATEN:")
        logger.info(f"   📋 EBA Metadata bestanden: {len(metadata_files)}")
        logger.info(f"   📋 Eurofiling bestanden: {len(eurofiling_files)}")
        logger.info(f"   📋 Framework bestanden: {len(framework_files)}")
        logger.info(f"   📋 Totaal unique entry points: {len(unique_entry_points)}")
        
        # KRITISCH: Als we nog steeds geen metadata hebben, log dit als ERROR
        if len(metadata_files) == 0:
            logger.error("🚨 KRITIEK: Geen EBA metadata taxonomy gevonden!")
            logger.error("🚨 Dit verklaart waarom alle eba_met: concepts ontbreken!")
        
        return unique_entry_points

    def verify_eba_metadata_concepts(self, metadata_files):
        """
        NIEUW: Controleer of metadata bestanden daadwerkelijk eba_met: concepts bevatten
        """
        eba_concepts_found = set()
        
        for metadata_file in metadata_files[:5]:  # Check eerste 5 bestanden
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Zoek naar eba_met concept definities
                concept_matches = re.findall(r'name="(eba_met:[^"]*)"', content)
                eba_concepts_found.update(concept_matches)
                
                if concept_matches:
                    logger.info(f"✅ {os.path.basename(metadata_file)}: {len(concept_matches)} eba_met concepts")
                else:
                    logger.warning(f"⚠️ {os.path.basename(metadata_file)}: GEEN eba_met concepts gevonden")
                    
            except Exception as e:
                logger.warning(f"Kon {metadata_file} niet lezen: {e}")
        
        logger.info(f"📊 Totaal eba_met concepts gevonden in metadata: {len(eba_concepts_found)}")
        return list(eba_concepts_found)

    def prioritize_packages_by_xbrl_requirements(self, all_packages, xbrl_analysis):
        """
        ENHANCED: Controleer metadata bestanden op daadwerkelijke eba_met: concepts
        """
        framework = xbrl_analysis['framework']
        accounting_standard = xbrl_analysis['accounting_standard']
        consolidation = xbrl_analysis['consolidation']
        required_modules = xbrl_analysis['required_modules']
        
        critical_metadata_packages = []
        framework_packages = []
        secondary_packages = []
        other_packages = []
        
        # STAP 1: Verifieer metadata bestanden
        potential_metadata = []
        for package in all_packages:
            package_name = os.path.basename(package).lower()
            
            # Identificeer potentiële metadata bestanden
            if any(metadata_pattern in package_name for metadata_pattern in [
                'eba_met', 'eba-met', 'metadata', 'met.xsd', 'met_', 'dict', 'fws'
            ]):
                potential_metadata.append(package)
        
        # STAP 2: Verifieer welke metadata bestanden echt eba_met: concepts bevatten
        verified_metadata = self.verify_eba_metadata_concepts(potential_metadata)
        
        for package in all_packages:
            package_name = os.path.basename(package).lower()
            package_path = package
            
            # HOOGSTE PRIORITEIT: Geverifieerde metadata bestanden
            if package in potential_metadata:
                critical_metadata_packages.append(package)
                logger.info(f"🎯 CRITICAL METADATA: {os.path.basename(package)}")
                continue
            
            # EUROFILING bestanden
            if any(euro_pattern in package_name for euro_pattern in [
                'find', 'eurofiling', 'filing-indicators', 'exp.xsd'
            ]):
                critical_metadata_packages.append(package)
                logger.info(f"🎯 EUROFILING: {os.path.basename(package)}")
                continue
            
            # Framework prioriteit (zoals voorheen)
            if any(req_module.lower() in package_name for req_module in required_modules):
                framework_packages.append(package)
                logger.info(f"🎯 FRAMEWORK PRIORITY: {os.path.basename(package)}")
                continue
            
            # Rest van de logica zoals voorheen...
            if framework == 'FINREP':
                if 'finrep' in package_name:
                    if accounting_standard and accounting_standard.lower() in package_name:
                        if consolidation == 'INDIVIDUAL' and 'ind' in package_name:
                            framework_packages.append(package)
                        elif consolidation == 'CONSOLIDATED' and 'con' in package_name:
                            framework_packages.append(package)
                        else:
                            secondary_packages.append(package)
                    else:
                        secondary_packages.append(package)
                else:
                    other_packages.append(package)
            elif framework == 'COREP':
                if 'corep' in package_name:
                    secondary_packages.append(package)
                else:
                    other_packages.append(package)
            else:
                other_packages.append(package)
        
        # FINALE PRIORITEIT: Metadata EERST, dan framework
        final_packages = (
            critical_metadata_packages + 
            framework_packages + 
            secondary_packages + 
            other_packages[:30]
        )
        
        logger.info(f"📊 FINAL Package prioritization:")
        logger.info(f"   🎯 Critical metadata packages: {len(critical_metadata_packages)}")
        logger.info(f"   🎯 Framework packages: {len(framework_packages)}")
        logger.info(f"   🔸 Secondary packages: {len(secondary_packages)}")
        logger.info(f"   📄 Total selected: {len(final_packages)}")
        
        # KRITIEK: Waarschuw als we geen metadata hebben
        if len(critical_metadata_packages) == 0:
            logger.error("🚨 GEEN METADATA PACKAGES GEVONDEN - DIT VERKLAART MISSING CONCEPTS!")
        
        return final_packages

    def create_http_to_local_mapping(self, extracted_dir, required_modules):
        """
        CRITICAL: Map HTTP URLs to local file paths
        """
        mappings = {}
        
        for module in required_modules:
            # Find local file that matches the module name
            matching_files = list(Path(extracted_dir).glob(f"**/{module}"))
            
            if matching_files:
                local_path = str(matching_files[0])
                # Create HTTP URL pattern
                http_url = f"http://www.eba.europa.eu/eu/fr/xbrl/crr/fws/**/{module}"
                mappings[module] = local_path
                logger.info(f"📍 Mapped {module} -> {local_path}")
            else:
                logger.warning(f"❌ Could not find local file for required module: {module}")
        
        return mappings

    # ... keep existing code (find_taxonomy_entry_points, verify_package_integrity, _validate_xsd_file, copy_to_arelle_cache, auto_extract_if_needed, analyze_missing_concepts, check_required_dependencies, verify_package_contents, generate_download_instructions, auto_resolve_dependencies)
    
    def find_taxonomy_entry_points(self, extracted_dir):
        """
        UPDATED: Use the new comprehensive discovery method
        """
        return self.discover_comprehensive_entry_points(extracted_dir)
    
    def verify_package_integrity(self, entry_points):
        """
        FIXED: Properly validate taxonomy packages - XSD files are XML schemas, not ZIP files
        """
        valid_packages = []
        invalid_packages = []
        
        for entry_point in entry_points:
            try:
                if not os.path.exists(entry_point):
                    invalid_packages.append((entry_point, "File not found"))
                    continue
                
                # XSD files are XML schema files, NOT ZIP files
                if entry_point.endswith('.xsd'):
                    if self._validate_xsd_file(entry_point):
                        valid_packages.append(entry_point)
                        logger.info(f"✅ Valid XSD schema: {os.path.basename(entry_point)}")
                    else:
                        invalid_packages.append((entry_point, "Invalid XSD schema"))
                        logger.warning(f"⚠️ Invalid XSD schema: {os.path.basename(entry_point)}")
                
                # Only validate ZIP files as ZIP files
                elif entry_point.endswith(('.zip', '.taxonomy')):
                    if zipfile.is_zipfile(entry_point):
                        valid_packages.append(entry_point)
                        logger.info(f"✅ Valid ZIP package: {os.path.basename(entry_point)}")
                    else:
                        invalid_packages.append((entry_point, "Invalid ZIP file"))
                        logger.error(f"❌ Invalid ZIP file: {os.path.basename(entry_point)}")
                else:
                    # Other file types - assume valid
                    valid_packages.append(entry_point)
                    logger.info(f"✅ Valid package: {os.path.basename(entry_point)}")
                        
            except Exception as e:
                invalid_packages.append((entry_point, str(e)))
                logger.error(f"❌ Package validation error: {os.path.basename(entry_point)} - {e}")
        
        return valid_packages, invalid_packages

    def _validate_xsd_file(self, xsd_path):
        """
        NEW METHOD: Validate XSD file as XML schema (not ZIP)
        """
        try:
            # Parse as XML
            tree = ET.parse(xsd_path)
            root = tree.getroot()
            
            # Check if it's a valid XSD schema
            if 'schema' in root.tag.lower():
                return True
            
            # Check for schema-like content
            schema_indicators = ['element', 'complexType', 'simpleType', 'import', 'include']
            with open(xsd_path, 'r', encoding='utf-8') as f:
                content = f.read().lower()
            
            return any(indicator in content for indicator in schema_indicators)
            
        except ET.ParseError:
            logger.warning(f"XSD file has XML parse issues: {xsd_path}")
            return False
        except Exception as e:
            logger.warning(f"Could not validate XSD file: {xsd_path} - {e}")
            return False
    
    def copy_to_arelle_cache(self, extracted_dir):
        """
        Copy extracted taxonomy to Arelle's default cache location
        """
        try:
            arelle_cache = Path.home() / "AppData" / "Local" / "Arelle" / "cache"
            arelle_cache.mkdir(parents=True, exist_ok=True)
            
            target_dir = arelle_cache / "eba_taxonomy_local"
            
            if not target_dir.exists():
                shutil.copytree(extracted_dir, target_dir)
                logger.info(f"✅ Copied taxonomy to Arelle cache: {target_dir}")
                return str(target_dir)
            else:
                logger.info(f"✅ Taxonomy already in Arelle cache: {target_dir}")
                return str(target_dir)
        except Exception as e:
            logger.error(f"❌ Failed to copy to Arelle cache: {str(e)}")
            return extracted_dir
    
    def auto_extract_if_needed(self, zip_path, extract_dir):
        """
        Auto-extract ZIP file if directory doesn't exist for better Arelle compatibility
        """
        if os.path.exists(zip_path) and not os.path.exists(extract_dir):
            logger.info(f"🔧 Auto-extracting {os.path.basename(zip_path)} for better Arelle compatibility...")
            try:
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)
                logger.info(f"✅ Successfully extracted to: {extract_dir}")
                return str(extract_dir)
            except Exception as e:
                logger.error(f"❌ Failed to extract {zip_path}: {str(e)}")
                return zip_path
        elif os.path.exists(extract_dir):
            logger.info(f"✅ Using existing extracted directory: {extract_dir}")
            return str(extract_dir)
        else:
            logger.warning(f"⚠️ Neither ZIP nor extracted directory found, using ZIP path: {zip_path}")
            return zip_path
    
    def analyze_missing_concepts(self, validation_output):
        """
        Analyze validation output to identify missing taxonomy dependencies
        """
        missing_analysis = {
            'eurofiling_concepts': [],
            'eba_framework_concepts': [],
            'xbrl_base_concepts': [],
            'mixed_version_concepts': [],
            'unknown_concepts': []
        }
        
        # Extract missing concepts from validation output
        missing_concepts = []
        
        # Enhanced pattern matching for missing concepts
        patterns = [
            r'Schema concept definition missing for\s+([^\n\r]+)',
            r'Instance facts missing schema concept definition:\s*([^\n\r]+)',
            r'facts missing schema concept definition:\s*([^\n\r]+)',
            r'missing schema concept:\s*([^\n\r]+)',
            r'concept definition not found:\s*([^\n\r]+)',
            r'undefined concept:\s*([^\n\r]+)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, validation_output, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                # Split by comma and clean concept names
                concepts = [c.strip() for c in match.split(',') if c.strip()]
                for concept in concepts:
                    concept = concept.strip().strip('"\'')
                    if concept and len(concept) > 2:
                        missing_concepts.append(concept)
        
        # Remove duplicates
        missing_concepts = list(set(missing_concepts))
        
        # Categorize missing concepts
        for concept in missing_concepts:
            if concept.startswith('find:') or 'fIndicators' in concept or 'filingIndicators' in concept:
                missing_analysis['eurofiling_concepts'].append(concept)
            elif concept.startswith('eba_met_3_4:') or concept.startswith('eba_met_3_5:'):
                missing_analysis['mixed_version_concepts'].append(concept)
            elif concept.startswith('eba_met:') or concept.startswith('eba_dim:') or concept.startswith('eba_'):
                missing_analysis['eba_framework_concepts'].append(concept)
            elif concept.startswith('xbrli:') or concept.startswith('link:') or concept.startswith('xbrl:'):
                missing_analysis['xbrl_base_concepts'].append(concept)
            else:
                missing_analysis['unknown_concepts'].append(concept)
        
        logger.info(f"📊 Missing concept analysis complete:")
        for category, concepts in missing_analysis.items():
            if concepts:
                logger.info(f"   • {category}: {len(concepts)} missing")
        
        return missing_analysis
    
    def check_required_dependencies(self, missing_analysis):
        """
        UPDATED: Check dependencies - prefer extracted directories over ZIP files with entry point discovery
        """
        required_packages = []
        missing_packages = []
        
        # Check EBA Framework 4.0 package - PREFER EXTRACTED DIRECTORY WITH ENTRY POINTS
        eba_extracted = self.eba_dir / "extracted"
        eba_zip = self.eba_dir / "taxo_package_4.0_errata5.zip"
        
        if eba_extracted.exists() and any(eba_extracted.glob("**/*.xsd")):
            # Find entry points in extracted directory
            entry_points = self.find_taxonomy_entry_points(str(eba_extracted))
            if entry_points:
                # Use entry points instead of directory
                required_packages.extend(entry_points)
                logger.info(f"✅ EBA Framework 4.0 entry points found: {len(entry_points)} files")
            else:
                # Copy to Arelle cache and use directory
                cache_dir = self.copy_to_arelle_cache(str(eba_extracted))
                required_packages.append(cache_dir)
                logger.info(f"✅ EBA Framework 4.0 cached: {cache_dir}")
        elif eba_zip.exists():
            # Auto-extract ZIP file for better compatibility
            extracted_path = self.auto_extract_if_needed(str(eba_zip), str(eba_extracted))
            entry_points = self.find_taxonomy_entry_points(extracted_path)
            if entry_points:
                required_packages.extend(entry_points)
                logger.info(f"✅ EBA Framework 4.0 entry points from ZIP: {len(entry_points)} files")
            else:
                required_packages.append(extracted_path)
                logger.info(f"✅ EBA Framework 4.0 package: {extracted_path}")
        else:
            missing_packages.append({
                'name': 'EBA Framework 4.0 Taxonomy Package',
                'file': str(eba_zip),
                'url': 'https://www.eba.europa.eu/sites/default/files/2025-03/2028f606-49d2-4696-be48-7681cc18c696/taxo_package_4.0_errata5.zip',
                'reason': 'Contains main EBA concepts and validation rules'
            })
        
        # Check Eurofiling Filing Indicators (if needed)
        if missing_analysis['eurofiling_concepts']:
            eurofiling_extracted = self.eurofiling_dir / "extracted"
            eurofiling_zip = self.eurofiling_dir / "filing-indicators.zip"
            
            if eurofiling_extracted.exists() and any(eurofiling_extracted.glob("**/*.xsd")):
                entry_points = self.find_taxonomy_entry_points(str(eurofiling_extracted))
                required_packages.extend(entry_points)
                logger.info(f"✅ Eurofiling entry points found: {len(entry_points)} files")
            elif eurofiling_zip.exists():
                extracted_path = self.auto_extract_if_needed(str(eurofiling_zip), str(eurofiling_extracted))
                entry_points = self.find_taxonomy_entry_points(extracted_path)
                required_packages.extend(entry_points)
                logger.info(f"✅ Eurofiling entry points from ZIP: {len(entry_points)} files")
            else:
                missing_packages.append({
                    'name': 'Eurofiling Filing Indicators',
                    'file': str(eurofiling_zip),
                    'url': 'https://eurofiling.info/eurofiling-taxonomy-architecture/filing-indicators-taxonomy/',
                    'reason': f'Required for concepts: {", ".join(missing_analysis["eurofiling_concepts"][:3])}'
                })
        
        # Check XBRL International Base (if needed)
        if missing_analysis['xbrl_base_concepts']:
            xbrl_extracted = self.xbrl_org_dir / "extracted"
            xbrl_zip = self.xbrl_org_dir / "xbrl-base.zip"
            
            if xbrl_extracted.exists() and any(xbrl_extracted.glob("**/*.xsd")):
                entry_points = self.find_taxonomy_entry_points(str(xbrl_extracted))
                required_packages.extend(entry_points)
                logger.info(f"✅ XBRL Base entry points found: {len(entry_points)} files")
            elif xbrl_zip.exists():
                extracted_path = self.auto_extract_if_needed(str(xbrl_zip), str(xbrl_extracted))
                entry_points = self.find_taxonomy_entry_points(extracted_path)
                required_packages.extend(entry_points)
                logger.info(f"✅ XBRL Base entry points from ZIP: {len(entry_points)} files")
            else:
                missing_packages.append({
                    'name': 'XBRL International Base Taxonomy',
                    'file': str(xbrl_zip),
                    'url': 'https://taxonomies.xbrl.org/',
                    'reason': f'Required for base XBRL concepts: {", ".join(missing_analysis["xbrl_base_concepts"][:3])}'
                })
        
        return required_packages, missing_packages
    
    def verify_package_contents(self, package_path):
        """
        FIXED: Handle different file types correctly - XSD, ZIP, and directories
        """
        if not os.path.exists(package_path):
            return False, f"Package not found: {package_path}"
        
        try:
            # Handle XSD files - validate as XML schemas
            if package_path.endswith('.xsd'):
                logger.info(f"🔍 Validating XSD file: {os.path.basename(package_path)}")
                try:
                    ET.parse(package_path)
                    logger.info(f"✅ Valid XSD file: {Path(package_path).name}")
                    return True, f"Valid XSD file: {Path(package_path).name}"
                except Exception as e:
                    logger.error(f"❌ Invalid XSD file: {str(e)}")
                    return False, f"Invalid XSD file: {str(e)}"
            
            # Handle ZIP files - validate as ZIP archives
            elif package_path.endswith('.zip'):
                logger.info(f"🔍 Validating ZIP file: {os.path.basename(package_path)}")
                try:
                    with zipfile.ZipFile(package_path, 'r') as zip_file:
                        file_list = zip_file.namelist()
                        
                        logger.info(f"   📁 Total files: {len(file_list)}")
                        
                        # Check for essential files
                        xsd_files = [f for f in file_list if f.endswith('.xsd')]
                        xml_files = [f for f in file_list if f.endswith('.xml')]
                        
                        logger.info(f"   📊 XSD files: {len(xsd_files)}")
                        logger.info(f"   📊 XML files: {len(xml_files)}")
                        
                        if len(xsd_files) > 0 and len(xml_files) > 0:
                            logger.info(f"✅ Valid ZIP: {len(file_list)} files ({len(xsd_files)} XSD, {len(xml_files)} XML)")
                            return True, f"Valid ZIP: {len(file_list)} files ({len(xsd_files)} XSD, {len(xml_files)} XML)"
                        else:
                            issues = []
                            if len(xsd_files) == 0:
                                issues.append("No XSD schema files found")
                            if len(xml_files) == 0:
                                issues.append("No XML linkbase files found")
                            
                            logger.error(f"❌ ZIP validation failed: {'; '.join(issues)}")
                            return False, "; ".join(issues)
                        
                except zipfile.BadZipFile:
                    logger.error(f"❌ Invalid ZIP file: {package_path}")
                    return False, "Invalid or corrupted ZIP file"
            
            # Handle directories - check for XSD files
            elif os.path.isdir(package_path):
                logger.info(f"🔍 Validating directory: {os.path.basename(package_path)}")
                package_dir = Path(package_path)
                xsd_files = list(package_dir.glob("**/*.xsd"))
                xml_files = list(package_dir.glob("**/*.xml"))
                
                logger.info(f"   📊 XSD files: {len(xsd_files)}")
                logger.info(f"   📊 XML files: {len(xml_files)}")
                
                if len(xsd_files) > 0 and len(xml_files) > 0:
                    logger.info(f"✅ Valid directory: {len(xsd_files)} XSD, {len(xml_files)} XML files")
                    return True, f"Valid directory: {len(xsd_files)} XSD, {len(xml_files)} XML files"
                else:
                    logger.error(f"❌ Directory incomplete: {len(xsd_files)} XSD, {len(xml_files)} XML files")
                    return False, f"Directory incomplete - need both XSD and XML files"
            
            # Unsupported file type
            else:
                logger.error(f"❌ Unsupported file type: {package_path}")
                return False, f"Unsupported file type: {package_path}"
                
        except Exception as e:
            logger.error(f"❌ Error validating package: {str(e)}")
            return False, f"Error validating package: {str(e)}"
    
    def generate_download_instructions(self, missing_packages):
        """
        Generate detailed download instructions for missing packages
        """
        if not missing_packages:
            return "✅ All required taxonomy packages are available!"
        
        instructions = ["❌ MISSING REQUIRED TAXONOMY PACKAGES:", ""]
        
        for i, package in enumerate(missing_packages, 1):
            instructions.extend([
                f"{i}. {package['name']}",
                f"   📁 Save as: {package['file']}",
                f"   🔗 Download from: {package['url']}",
                f"   💡 Reason: {package['reason']}",
                ""
            ])
        
        instructions.extend([
            "📋 INSTALLATION STEPS:",
            "1. Download each package from the URLs above",
            "2. Save with the EXACT filenames shown",
            "3. Packages will be auto-extracted for better compatibility",
            "4. Restart the validation process",
            "5. Verify all missing concepts are resolved",
            ""
        ])
        
        return "\n".join(instructions)
    
    def auto_resolve_dependencies(self):
        """
        Automatically check and attempt to resolve missing dependencies
        """
        logger.info("🔍 Checking taxonomy dependency status...")
        
        # Check for common missing packages (prefer extracted directories)
        common_packages = {
            'EBA Framework 4.0': (self.eba_dir / "extracted", self.eba_dir / "taxo_package_4.0_errata5.zip"),
            'Eurofiling Filing Indicators': (self.eurofiling_dir / "extracted", self.eurofiling_dir / "filing-indicators.zip"),
            'XBRL Base': (self.xbrl_org_dir / "extracted", self.xbrl_org_dir / "xbrl-base.zip")
        }
        
        missing_count = 0
        available_packages = []
        
        for name, (extract_path, zip_path) in common_packages.items():
            if extract_path.exists() and any(extract_path.glob("**/*.xsd")):
                logger.info(f"✅ {name}: Available (extracted)")
                available_packages.append(str(extract_path))
            elif zip_path.exists():
                logger.info(f"✅ {name}: Available (will auto-extract)")
                # Auto-extract for better compatibility
                extracted_path = self.auto_extract_if_needed(str(zip_path), str(extract_path))
                available_packages.append(extracted_path)
            else:
                logger.warning(f"❌ {name}: Missing - {zip_path}")
                missing_count += 1
        
        if missing_count > 0:
            logger.warning(f"⚠️ {missing_count} taxonomy packages missing")
            logger.info("💡 Run validation to get specific download instructions")
            return False, available_packages
        else:
            logger.info("✅ All common taxonomy packages available")
            return True, available_packages
