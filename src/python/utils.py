
import os
import xml.etree.ElementTree as ET
import zipfile
import logging

logger = logging.getLogger(__name__)

def extract_annotations(taxonomy_zip_path):
    """Extract annotations from taxonomy zip file"""
    annotations = {}
    try:
        with zipfile.ZipFile(taxonomy_zip_path, 'r') as zip_ref:
            zip_ref.extractall("temp_taxonomy")

        for root_dir, _, files in os.walk("temp_taxonomy"):
            for file in files:
                if file.endswith(".xml"):
                    file_path = os.path.join(root_dir, file)
                    try:
                        tree = ET.parse(file_path)
                        root = tree.getroot()
                        for elem in root.iter():
                            if "label" in elem.tag.lower() and elem.text:
                                annotations[elem.text.strip()] = elem.attrib.get("id", "")
                    except Exception:
                        continue
    except Exception:
        pass

    return annotations

def create_uploads_directory():
    """Create uploads directory if it doesn't exist"""
    os.makedirs("uploads", exist_ok=True)

def save_uploaded_files(instance_file, taxonomy_file):
    """Save uploaded files and return their paths"""
    create_uploads_directory()
    
    instance_path = os.path.join("uploads", instance_file.filename)
    taxonomy_path = os.path.join("uploads", taxonomy_file.filename)
    
    instance_file.save(instance_path)
    taxonomy_file.save(taxonomy_path)
    
    return instance_path, taxonomy_path
