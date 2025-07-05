
import re
from typing import Dict, List, Optional, Any
import json

class XBRLErrorEnricher:
    """
    Enhanced XBRL validation error enrichment module.
    Adds contextual information, formula validation, and EBA-specific suggestions.
    """
    
    def __init__(self):
        # Enhanced sheet mapping for EBA FINREP patterns
        self.sheet_patterns = {
            r'F-01\.01': 'F-01.01 - Statement of Financial Position (Assets)',
            r'F-01\.02': 'F-01.02 - Statement of Financial Position (Liabilities)', 
            r'F-01\.03': 'F-01.03 - Statement of Financial Position (Equity)',
            r'F-02\.00': 'F-02.00 - Income Statement',
            r'F-03\.00': 'F-03.00 - Breakdown by residual maturity',
            r'F-04\.01': 'F-04.01 - Credit quality of performing exposures',
            r'F-04\.02': 'F-04.02 - Credit quality of non-performing exposures',
            r'F-18\.00': 'F-18.00 - Accounting classification of financial assets',
            r'F-32\.01': 'F-32.01 - Maturity breakdown',
            r'C\s*\d+\.\d+': 'Capital Requirements Regulation',
            r'CR\s*GB\s*\d+': 'Credit Risk - General',
            r'MKR\s*SA\s*\d+': 'Market Risk - Standardised Approach'
        }
        
        # Enhanced error patterns with EBA-specific rules
        self.error_suggestions = {
            r'formula.*validation.*failed': 'Controleer de wiskundige formule - de berekening klopt niet met de EBA regels',
            r'consistency.*check.*failed': 'Er is een inconsistentie tussen gerelateerde datapunten gedetecteerd',
            r'dimensional.*constraint.*violation': 'De dimensie combinatie is niet toegestaan volgens de EBA taxonomie',
            r'context.*not.*found': 'Controleer of de juiste contextRef is ingevuld voor deze periode en entiteit',
            r'unit.*not.*found': 'Controleer of de juiste unitRef is opgegeven (meestal EUR voor monetaire bedragen)',
            r'duplicate.*context': 'Er zijn meerdere contexten met dezelfde identifier. Zorg voor unieke context IDs',
            r'missing.*dimension': 'Controleer of alle vereiste dimensies zijn opgegeven voor deze regel',
            r'invalid.*date': 'Controleer of de datum in het juiste formaat staat (YYYY-MM-DD)',
            r'decimal.*precision': 'Controleer of het aantal decimalen correct is opgegeven',
            r'required.*element.*missing': 'Dit verplichte element ontbreekt. Voeg het toe aan uw XBRL bestand',
            r'inconsistent.*total': 'De som van onderliggende elementen komt niet overeen met het totaal',
            r'negative.*value.*not.*allowed': 'Negatieve waarden zijn niet toegestaan voor dit element',
            r'calculation.*inconsistency': 'Er is een rekenfout gedetecteerd. Controleer de formule en invoerwaarden',
            r'enumeration.*constraint': 'De waarde voldoet niet aan de toegestane lijst van waarden',
            r'datatype.*violation': 'Het datatype komt niet overeen met wat verwacht wordt',
            r'period.*mismatch': 'De periode komt niet overeen met de verwachte rapportageperiode'
        }
        
        # Rule type classification
        self.rule_types = {
            r'formula|calculation': 'formula',
            r'consistency|cross.*reference': 'consistency', 
            r'completeness|required|mandatory': 'completeness',
            r'dimension|member|domain': 'dimensional'
        }
        
        # Severity mapping
        self.severity_mapping = {
            'error': 'error',
            'warning': 'warning', 
            'info': 'info',
            'fatal': 'error'
        }

    def classify_rule_type(self, message: str, rule_code: str) -> str:
        """Classify the type of validation rule based on message content."""
        combined_text = f"{message} {rule_code}".lower()
        
        for pattern, rule_type in self.rule_types.items():
            if re.search(pattern, combined_text):
                return rule_type
        
        return 'consistency'  # default

    def extract_formula_info(self, message: str) -> Dict[str, Any]:
        """Extract formula-related information from error messages."""
        formula_info = {}
        
        # Look for expected vs actual values
        expected_match = re.search(r'expected[:\s]+([0-9,.-]+)', message, re.IGNORECASE)
        if expected_match:
            formula_info['expectedValue'] = expected_match.group(1)
            
        actual_match = re.search(r'actual[:\s]+([0-9,.-]+)', message, re.IGNORECASE)
        if actual_match:
            formula_info['actualValue'] = actual_match.group(1)
            
        # Look for formula expressions
        formula_match = re.search(r'formula[:\s]+(.+?)(?:\.|$)', message, re.IGNORECASE)
        if formula_match:
            formula_info['formula'] = formula_match.group(1).strip()
            
        return formula_info

    def extract_sheet_from_xpath(self, xpath_or_message: str) -> Optional[str]:
        """Extract sheet information from XPath or error message."""
        if not xpath_or_message:
            return None
            
        # Try to match known sheet patterns
        for pattern, sheet_name in self.sheet_patterns.items():
            if re.search(pattern, xpath_or_message, re.IGNORECASE):
                return sheet_name
                
        # Try to extract from concept names
        concept_match = re.search(r'([A-Z]+_\d+_\d+)', xpath_or_message)
        if concept_match:
            return f"Sheet {concept_match.group(1)}"
            
        return None

    def generate_suggestion(self, error_message: str, rule_type: str = 'consistency') -> str:
        """Generate enhanced suggestions based on error message and rule type."""
        if not error_message:
            return "Controleer de XBRL structuur en inhoud volgens EBA specificaties"
            
        error_lower = error_message.lower()
        
        # Try to match enhanced error patterns
        for pattern, suggestion in self.error_suggestions.items():
            if re.search(pattern, error_lower):
                return suggestion
        
        # Rule type specific suggestions
        if rule_type == 'formula':
            return "Controleer de mathematische berekening - alle waardes moeten kloppen met de EBA formules"
        elif rule_type == 'dimensional':
            return "Controleer de dimensie combinaties volgens de EBA hypercube definities"
        elif rule_type == 'completeness':
            return "Dit verplichte veld moet worden ingevuld volgens EBA regelgeving"
        
        # Default suggestions based on keywords
        if 'context' in error_lower:
            return "Controleer de context definitie en referenties"
        elif 'unit' in error_lower:
            return "Controleer of de juiste eenheid (unit) is opgegeven"
        elif 'dimension' in error_lower:
            return "Controleer de dimensie instellingen voor dit element"
        elif 'period' in error_lower:
            return "Controleer of de rapportageperiode correct is ingesteld"
        elif 'calculate' in error_lower or 'sum' in error_lower:
            return "Controleer de rekenregels en totalen"
        elif 'required' in error_lower or 'mandatory' in error_lower:
            return "Dit veld is verplicht en moet worden ingevuld"
        else:
            return "Controleer de XBRL structuur volgens de EBA taxonomie vereisten"

    def enrich_error(self, error_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich a single error with enhanced context and suggestions."""
        enriched = error_data.copy()
        
        # Extract original fields
        message = error_data.get('message', '')
        xpath = error_data.get('xpath', '')
        line = error_data.get('line')
        column = error_data.get('column')
        severity = error_data.get('severity', 'error')
        rule_code = error_data.get('rule', error_data.get('code', ''))
        
        # Classify rule type
        rule_type = self.classify_rule_type(message, rule_code)
        enriched['ruleType'] = rule_type
        
        # Extract formula information if applicable
        if rule_type == 'formula':
            formula_info = self.extract_formula_info(message)
            enriched.update(formula_info)
        
        # Add sheet information
        sheet = self.extract_sheet_from_xpath(xpath or message)
        if sheet:
            enriched['sheet'] = sheet
            
        # Add enhanced suggestion
        suggestion = self.generate_suggestion(message, rule_type)
        enriched['suggestion'] = suggestion
        
        # Normalize severity
        enriched['severity'] = self.severity_mapping.get(severity.lower(), 'error')
        
        # Add concept information if available
        concept_match = re.search(r'([a-zA-Z_]+:[a-zA-Z_0-9]+)', message)
        if concept_match:
            enriched['concept'] = concept_match.group(1)
            
        # Ensure line and column are present (even if None)
        enriched['line'] = line
        enriched['column'] = column
        
        return enriched

    # ... keep existing code (enrich_errors, create_validation_result, and other methods)
