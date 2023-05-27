"""Test migration pipeline"""
import os
import sys
import unittest
from pathlib import Path
from typing import List

import pandas as pd
from oaklib.types import CURIE

TEST_DIR = Path(os.path.abspath(os.path.dirname(__file__)))
PROJECT_ROOT = TEST_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))
from src.scripts.migrate import slurp

TEST_INPUT_DIR = TEST_DIR / 'input' / 'test_migrate'
TEST_OUTPUT_DIR = TEST_DIR / 'output' / 'test_migrate'
ONTOLOGY_DIR = PROJECT_ROOT / 'src' / 'ontology'
USE_CACHE = False

class TestMigrate(unittest.TestCase):
    """Test migration pipeline"""

    df: pd.DataFrame
    migratable: List[CURIE]
    mapping_status: pd.DataFrame

    @classmethod
    def setUpClass(cls):
        """Always runs first"""
        outpath = str(TEST_OUTPUT_DIR / 'ordo.tsv')
        mapping_status_path = str(TEST_INPUT_DIR / 'ordo_mapping_status_custom.tsv')
        os.makedirs(TEST_OUTPUT_DIR, exist_ok=True)
        slurp(
            ontology_path=str(ONTOLOGY_DIR / 'components' / 'ordo.owl'),
            mondo_terms_path=str(ONTOLOGY_DIR / 'reports' / 'mirror_signature-mondo.tsv'),
            onto_config_path=str(ONTOLOGY_DIR / 'metadata' / 'ordo.yml'),
            mondo_mappings_path=str(TEST_INPUT_DIR / 'mondo.sssom.tsv'),
            mapping_status_path=mapping_status_path,
            slurp_dir_path=str(TEST_OUTPUT_DIR),
            outpath=outpath,
            min_id=850000,
            max_id=999999,
            use_cache=USE_CACHE)
        cls.df = pd.read_csv(outpath, sep='\t')
        cls.migratable = cls.df['xref'].to_list()[1:]
        cls.mapping_status_df = pd.read_csv(mapping_status_path, sep='\t')

    def test_parents_field(self):
        """Test parents field to make sure these are Mondo IDs and not native ontology IDs."""
        example_parents_str: str = self.df['parents'][1]
        parents: List[CURIE] = example_parents_str.split('|')
        self.assertTrue(all([x.startswith('MONDO') for x in parents]))

    def test_all_expected_in_output(self):
        """Tests against known passing cases in input file. All of these terms meet all conditions for inclusion in the
        the output file, e.g. they're not mapped, excluded, or obsolete, and they either have no parents, or all of
        their parents are either mapped, excluded, or obsolete."""
        expected: List[CURIE] = \
            self.mapping_status_df[self.mapping_status_df['expected_in_output'] == True]['subject_id'].to_list()
        self.assertTrue(all([x in self.migratable for x in expected]))

    def test_all_unexpected_not_in_output(self):
        """Tests against known failing cases in input file. None of these terms meet all conditions for inclusion in the
        the output file, e.g. they're either mapped, excluded, or obsolete, or not all of their parents are mapped,
        excluded, or obsolete."""
        unexpected: List[CURIE] = \
            self.mapping_status_df[self.mapping_status_df['expected_in_output'] == False]['subject_id'].to_list()
        self.assertTrue(all([x not in self.migratable for x in unexpected]))

    def test_deprecated_excluded_mapped_not_in_output(self):
        """Tests subset cases of test_all_unexpected_not_in_output(), specifically one case of each where a term is
        either mapped, excluded, or obsolete/deprecated."""
        for field in ['is_mapped', 'is_excluded', 'is_deprecated']:
            df = self.mapping_status_df[self.mapping_status_df[field] == True]
            unexpected: CURIE = df['subject_id'].to_list()[0]
            self.assertNotIn(unexpected, self.migratable)

    def test_no_parents_in_output(self):
        """Tests subset case of test_all_expected_in_output(), specifically a case where the term is not mapped,
        excluded, or obsolete, and also that it has no parents."""
        has_no_parents = 'Orphanet:C001'  # As of 2023/05/28
        self.assertIn(has_no_parents, self.migratable)


if __name__ == '__main__':
    unittest.main()
