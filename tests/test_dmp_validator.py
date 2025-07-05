import os
import sys
import unittest
import types

# Ensure src/python is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'python'))

# Provide a dummy pyodbc module if it's not installed
if 'pyodbc' not in sys.modules:
    sys.modules['pyodbc'] = types.ModuleType('pyodbc')

from dmp_validator import DMPValidator

class DMPValidatorListFactsTest(unittest.TestCase):
    def test_validate_repeated_facts(self):
        validator = DMPValidator()

        facts = {
            'met:factA': [
                {'value': '100', 'context': 'c1', 'unit': 'EUR'},
                {'value': '200', 'context': 'c2', 'unit': 'EUR'},
            ],
            'met:factB': {'value': '1', 'context': 'c3', 'unit': 'EUR'},
        }

        concept_resolutions = {
            'timestamp': '2024-01-01',
            'resolution_details': [
                {
                    'fact_name': 'met:factA',
                    'concept_code': 'FA',
                    'concept_type': 'Monetary',
                    'source_table': 't1',
                    'resolved': True,
                },
                {
                    'fact_name': 'met:factB',
                    'concept_code': 'FB',
                    'concept_type': 'Monetary',
                    'source_table': 't1',
                    'resolved': True,
                },
            ],
        }

        result = validator.validate_facts(facts, concept_resolutions)

        self.assertEqual(result['total_facts'], 3)
        self.assertEqual(len(result['fact_validations']), 3)
        summary = result['validation_summary']
        total_count = (
            summary['valid_facts']
            + summary['invalid_facts']
            + summary['warning_facts']
            + summary['unresolved_facts']
        )
        self.assertEqual(total_count, 3)

if __name__ == '__main__':
    unittest.main()
