
import os
import json
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)

# Arelle CLI path
ARELLE_PATH = r"C:\Users\berbe\Documents\AI\XBRL-validation\Arella\arella\Arelle\arelleCmdLine.exe"

# Load validation rules
def load_finrep_rules():
    try:
        with open("finrep_validation_rules.json", "r", encoding="utf-8") as f:
            return {entry["rule_id"]: entry for entry in json.load(f)}
    except Exception:
        return {}

# Load cell mapping
def load_cell_mapping():
    try:
        with open("xbrl_cell_mappings.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

FINREP_RULES = load_finrep_rules()
CELL_MAPPING = load_cell_mapping()
