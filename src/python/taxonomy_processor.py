import os
import zipfile
import logging
import shutil
from pathlib import Path
from taxonomy_dependency_manager import EBATaxonomyDependencyManager

logger = logging.getLogger(__name__)

class TaxonomyProcessor:
    def __init__(self, architecture_version=None):
        self.dependency_manager = EBATaxonomyDependencyManager()
        self.architecture_version = architecture_version
    
    def process_taxonomy_file(self, taxonomy_path, architecture_version=None):
        """
        Architecture-aware taxonomy processing
        Returns: (extracted_schemas, all_packages, extraction_dir)
        """
        # Use architecture from parameter or instance
        arch_version = architecture_version or self.architecture_version
        
        logger.info(f"🔧 Processing taxonomy file: {taxonomy_path} (Architecture: {arch_version})")
        
        try:
            extraction_dir = None
            extracted_schemas = []
            
            if taxonomy_path.endswith('.zip'):
                # Extract ZIP file with architecture-specific handling
                extraction_dir = self._extract_taxonomy_zip(taxonomy_path, arch_version)
                extracted_schemas = self._discover_schemas_in_directory(extraction_dir, arch_version)
            elif os.path.isdir(taxonomy_path):
                # Use directory directly
                extraction_dir = taxonomy_path
                extracted_schemas = self._discover_schemas_in_directory(extraction_dir, arch_version)
            else:
                logger.warning(f"⚠️ Unsupported taxonomy file format: {taxonomy_path}")
            
            # Architecture-specific package discovery
            all_packages = []
            if extraction_dir:
                all_packages = self._discover_packages_by_architecture(extraction_dir, arch_version)
                valid_packages, invalid_packages = self.dependency_manager.verify_package_integrity(all_packages)
                logger.info(f"📦 Found {len(valid_packages)} valid packages, {len(invalid_packages)} invalid for {arch_version}")
                all_packages = valid_packages
            
            logger.info(f"✅ Taxonomy processing complete:")
            logger.info(f"   📁 Extraction dir: {extraction_dir}")
            logger.info(f"   📄 Extracted schemas: {len(extracted_schemas)}")
            logger.info(f"   📦 Available packages: {len(all_packages)}")
            logger.info(f"   🏗️ Architecture: {arch_version}")
            
            return extracted_schemas, all_packages, extraction_dir
            
        except Exception as e:
            logger.error(f"❌ Taxonomy processing failed: {str(e)}")
            return [], [], None
    
    def _extract_taxonomy_zip(self, zip_path, architecture_version=None):
        """Architecture-aware taxonomy ZIP extraction with SHORT paths for Windows compatibility"""
        try:
            # FIXED: Use SHORT paths to avoid Windows 260 character limit
            arch_suffix = "a1" if architecture_version == "arch_1_0" else "a2"
            extraction_dir = os.path.join("uploads", f"tax_{arch_suffix}")

            # Validate and prepare extraction directory
            if os.path.exists(extraction_dir):
                if not os.path.isdir(extraction_dir) or not os.access(extraction_dir, os.W_OK | os.R_OK):
                    backup_path = f"{extraction_dir}_old"
                    try:
                        os.rename(extraction_dir, backup_path)
                        logger.warning(f"📝 Moved existing path {extraction_dir} to {backup_path}")
                    except Exception:
                        logger.warning(f"⚠️ Could not rename {extraction_dir}, attempting removal")
                        try:
                            if os.path.isdir(extraction_dir):
                                shutil.rmtree(extraction_dir)
                            else:
                                os.remove(extraction_dir)
                        except Exception as cleanup_error:
                            logger.error(f"❌ Unable to prepare extraction dir {extraction_dir}: {str(cleanup_error)}")
                            return None

            os.makedirs(extraction_dir, exist_ok=True)
            if not os.access(extraction_dir, os.W_OK):
                logger.error(f"❌ Extraction directory not writable: {extraction_dir}")
                return None
            logger.info(f"📁 Created SHORT extraction directory: {extraction_dir}")
            
            logger.info(f"📦 Extracting taxonomy ZIP: {zip_path} for {architecture_version}")
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # FIXED: Extract with path length checking to avoid Windows issues
                for member in zip_ref.infolist():
                    # Check path length before extraction
                    full_path = os.path.join(extraction_dir, member.filename)
                    if len(full_path) > 250:  # Safe margin below 260 limit
                        # Skip files with too-long paths and log
                        logger.warning(f"⚠️ Skipping file with long path: {member.filename[:50]}...")
                        continue
                    
                    try:
                        zip_ref.extract(member, extraction_dir)
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to extract {member.filename}: {str(e)[:100]}")
                        continue
                
                # Verify extraction
                extracted_files = os.listdir(extraction_dir)
                logger.info(f"📂 Extracted {len(extracted_files)} items to {extraction_dir}")
                if extracted_files:
                    logger.info(f"📄 Sample files: {extracted_files[:5]}")
            
            logger.info(f"✅ Taxonomy extracted successfully to: {extraction_dir}")
            return extraction_dir
            
        except zipfile.BadZipFile as e:
            logger.error(f"❌ Invalid ZIP file: {str(e)}")
            return None
        except PermissionError as e:
            logger.error(f"❌ Permission denied accessing {extraction_dir}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"❌ Failed to extract taxonomy ZIP: {str(e)}")
            return None
    
    def _discover_schemas_in_directory(self, directory, architecture_version=None):
        """Architecture-aware schema discovery"""
        schemas = []
        
        try:
            # Architecture-specific search patterns
            if architecture_version == "arch_1_0":
                # DPM 3.0 patterns - focus on FINREP/COREP schemas
                patterns = ["**/*.xsd", "**/finrep/**/*.xsd", "**/corep/**/*.xsd", "**/dict/**/*.xsd"]
                priority_keywords = ['finrep', 'corep', 'dpm_3', 'phase2', 'dict']
            else:
                # DPM 4.0 patterns - focus on EBA metadata schemas  
                patterns = ["**/*.xsd", "**/dict/**/*.xsd", "**/mod/**/*.xsd", "**/eba_met/**/*.xsd"]
                priority_keywords = ['eba_met', 'metadata', 'dict', 'find', 'dpm_4']
            
            for pattern in patterns:
                matches = list(Path(directory).glob(pattern))
                schemas.extend([str(m) for m in matches])
            
            # Remove duplicates
            unique_schemas = list(set(schemas))
            
            # Architecture-specific prioritization
            prioritized_schemas = []
            regular_schemas = []
            
            for schema in unique_schemas:
                schema_name = os.path.basename(schema).lower()
                schema_path = schema.lower()
                
                # Check if this schema is priority for current architecture
                is_priority = any(keyword in schema_name or keyword in schema_path 
                                for keyword in priority_keywords)
                
                if is_priority:
                    prioritized_schemas.append(schema)
                else:
                    regular_schemas.append(schema)
            
            final_schemas = prioritized_schemas + regular_schemas
            
            logger.info(f"📄 Discovered {len(final_schemas)} schema files for {architecture_version}:")
            logger.info(f"   🎯 Priority schemas: {len(prioritized_schemas)}")
            logger.info(f"   📝 Regular schemas: {len(regular_schemas)}")
            
            # Log sample priority schemas
            for schema in prioritized_schemas[:5]:
                logger.info(f"   ✅ Priority: {os.path.basename(schema)}")
            
            return final_schemas
            
        except Exception as e:
            logger.error(f"❌ Schema discovery failed: {str(e)}")
            return []
    
    def _discover_packages_by_architecture(self, extraction_dir, architecture_version):
        """Architecture-specific package discovery"""
        try:
            if architecture_version == "arch_1_0":
                # DPM 3.0 - look for FINREP/COREP packages
                logger.info("🔍 Searching for DPM 3.0 packages (FINREP/COREP)")
                packages = self.dependency_manager.discover_comprehensive_entry_points(extraction_dir)
                # Filter for relevant packages
                arch_packages = [p for p in packages if any(term in str(p).lower() 
                               for term in ['finrep', 'corep', 'phase2', 'dpm_3'])]
                if not arch_packages:
                    arch_packages = packages[:10]  # Fallback to first 10
            else:
                # DPM 4.0 - look for EBA packages  
                logger.info("🔍 Searching for DPM 4.0 packages (EBA)")
                packages = self.dependency_manager.discover_comprehensive_entry_points(extraction_dir)
                # Filter for relevant packages
                arch_packages = [p for p in packages if any(term in str(p).lower() 
                               for term in ['eba_met', 'find', 'dpm_4', 'errata'])]
                if not arch_packages:
                    arch_packages = packages[:10]  # Fallback to first 10
            
            logger.info(f"📦 Found {len(arch_packages)} architecture-specific packages")
            return arch_packages
            
        except Exception as e:
            logger.error(f"❌ Architecture-specific package discovery failed: {str(e)}")
            return self.dependency_manager.discover_comprehensive_entry_points(extraction_dir)
    
    def verify_taxonomy_concepts(self, extracted_schemas, test_concepts=None, architecture_version=None):
        """Architecture-aware concept verification"""
        arch_version = architecture_version or self.architecture_version
        
        if test_concepts is None:
            if arch_version == "arch_1_0":
                # DPM 3.0 test concepts
                test_concepts = ['finrep:md123', 'corep:cr_1_1', 'dpm:dimension']
            else:
                # DPM 4.0 test concepts
                test_concepts = ['eba_met:qCEF', 'eba_met:qAOF', 'eba_met:qFAF', 'find:LCR_1_1']
        
        found_concepts = {}
        
        try:
            logger.info(f"🔍 Verifying taxonomy contains {len(test_concepts)} test concepts for {arch_version}")
            
            for schema_path in extracted_schemas[:20]:  # Check first 20 schemas
                try:
                    with open(schema_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    schema_name = os.path.basename(schema_path)
                    
                    for concept in test_concepts:
                        if concept in content or concept.split(':')[1] in content:
                            if concept not in found_concepts:
                                found_concepts[concept] = []
                            found_concepts[concept].append(schema_name)
                            
                except Exception as e:
                    logger.warning(f"⚠️ Could not read schema {schema_path}: {str(e)}")
                    continue
            
            logger.info(f"🎯 Concept verification results for {arch_version}:")
            for concept in test_concepts:
                if concept in found_concepts:
                    logger.info(f"   ✅ {concept}: Found in {len(found_concepts[concept])} schemas")
                else:
                    logger.warning(f"   ❌ {concept}: NOT FOUND in taxonomy")
            
            return found_concepts
            
        except Exception as e:
            logger.error(f"❌ Concept verification failed: {str(e)}")
            return {}