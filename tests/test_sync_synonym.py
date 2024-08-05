"""Synonym synchronization tests.

Todo: legal proxy merges: tests to ensure they show up correctly
  - e.g. if Mondo:123 has exactMatch OMIM:123 and OMIM:456, appears correctly.
  - could also test against illegal proxy merges, but might not be the best place here (e.g. OMIM:123 should not be
  exact to Mondo:123 and Mondo:456).
Todo: obsoleted: test cases: (i) obsolete Mondo term, (ii) obsolete source term
Todo: 'deleted terms': test cases - There were some cases in OMIM where Mondo has a mapping to a term and it appears in
 mondo.sssom.tsv, but term doesn't exist in source.

todo: super class: to use w/ subclass sync: similar setup, e.g. updated, confirmed, added, deleted
todo: refactor to declare expected cases as static files?
  - i.e. as opposed to declaring them here as List[Dict] w/ code comments, I could commit '-expected' files and have
  comments (e.g. which case the row represents) in a column.
todo: refactor 'case' enumeration commenting to account for 3rd dimension (unmapped)
  As of 2024/07/30, We have 2 dimensions: (1) casing (same vs not), (2) source attribution (exists vs doesn't exist).
  This ends up yielding 2x2 = 4 cases.
  Haven't fully thought through, but 1 of the following is correct:
  a. Should assume all cases are mapped. Unmapped cases are a separate test; shouldn't appear in any template.
  b. By adding (3) mapping (mapped vs not), this should actually create 2x2x2=8 cases.
  It's really excessive to test for all of these cases, but it would be good to at least be consistent with how we are
  labeling / commenting about these cases.
  I think we need to make sure that, like 'a', each of these unmapped cases doesn't appear in any template, the correct
  place to put tests is 'b': each case -added, -confirmed, -updated, -deleted, because there are 2 kinds of unmapped:
  (i) where there exists no information in Mondo, (ii) where Mondo has everything it needs in mondo.owl to be 1 of these
  bonafide 4 cases, but for whatever reason (obsoletion, term deletion, etc), no there's no row in mondo.sssom.tsv.
"""
import os
import subprocess
import sys
import unittest
from pathlib import Path
from typing import Dict, Union, Tuple, List

import pandas as pd

# noinspection DuplicatedCode
TEST_DIR = Path(os.path.abspath(os.path.dirname(__file__)))
PROJECT_ROOT = TEST_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))
from src.scripts.sync_synonym import sync_synonyms

ONTO_DIR = PROJECT_ROOT / 'src' / 'ontology'
META_DIR = ONTO_DIR / 'metadata'
IN_DIR = TEST_DIR / 'input' / 'sync_synonym'
OUT_DIR = TEST_DIR / 'output'
INPUT_MONDO_DB = IN_DIR / 'test_mondo.db'  # create via: sh run.sh make ../../tests/input/sync_synonym/test_mondo.db
INPUT_SOURCE_DB = IN_DIR / 'test_omim.db'  # create via: sh run.sh make ../../tests/input/sync_synonym/test_omim.db
INPUT_MONDO_SYNONYMS = IN_DIR / 'mondo-synonyms-scope-type-xref.tsv'  # create via: sh run.sh make ../../tests/input/sync_synonym/mondo-synonyms-scope-type-xref.tsv
INPUT_EXCLUDED_SYNONYMS = IN_DIR / 'mondo-excluded-synonyms.tsv'
INPUT_MAPPINGS = IN_DIR / 'test_mondo.sssom.tsv'
INPUT_SOURCE_METADATA = META_DIR / 'omim.yml'
OUTPUT_ADDED = OUT_DIR / 'omim.synonyms.added.robot.tsv'
OUTPUT_CONFIRMED = OUT_DIR / 'omim.synonyms.confirmed.robot.tsv'
OUTPUT_DELETED = OUT_DIR / 'omim.synonyms.deleted.robot.tsv'
OUTPUT_UPDATED = OUT_DIR / 'omim.synonyms.updated.robot.tsv'

class TestSyncSynonyms(unittest.TestCase):
    """Synonym synchronization tests."""

    @classmethod
    def setUpClass(cls):
        """Set up"""
        # todo: #1 run pipeline / prereqs - dependent on fixing _run_make_goal()
        # if not os.path.exists(INPUT_SOURCE_DB):
        #     cls._run_make_goal('../../tests/input/sync_synonym/omim.db')
        # if not os.path.exists(INPUT_MONDO_DB):
        #     cls._run_make_goal('../../tests/input/sync_synonym/mondo.db')
        # if not os.path.exists(INPUT_MONDO_SYNONYMS):
        #     cls._run_make_goal('../../tests/input/sync_synonym/mondo-synonyms-scope-type-xref.tsv')
        sync_synonyms(
            ontology_db_path=INPUT_SOURCE_DB,
            mondo_synonyms_path=INPUT_MONDO_SYNONYMS,
            excluded_synonyms_path=INPUT_EXCLUDED_SYNONYMS,
            mondo_mappings_path=INPUT_MAPPINGS,
            onto_config_path=INPUT_SOURCE_METADATA,
            outpath_added=OUTPUT_ADDED,
            outpath_confirmed=OUTPUT_CONFIRMED,
            outpath_deleted=OUTPUT_DELETED,
            outpath_updated=OUTPUT_UPDATED,
            combined_outpath_template_str=None
        )
        cls.df_lookup: Dict[str, pd.DataFrame] = {
            'added': cls._read_df(OUTPUT_ADDED),
            'confirmed': cls._read_df(OUTPUT_CONFIRMED),
            'deleted': cls._read_df(OUTPUT_DELETED),
            'updated': cls._read_df(OUTPUT_UPDATED),
        }

    # todo: #1 eventually fix this. It's not working. I'm getting back:
    #  stdout: "Running obolibrary/odkfull:latest with '-Xmx20G' as options for ROBOT and other Java-based pipeline steps.
    #  stderr: 'the input device is not a TTY
    @staticmethod
    def _run_make_goal(make_goal: str, raise_errs=True) -> Tuple[str, str]:
        """Run a subprocess command."""
        command_str = 'sh run.sh make ' + make_goal
        result = subprocess.run(command_str.split(), capture_output=True, text=True, cwd=str(ONTO_DIR))
        stderr, stdout = result.stderr, result.stdout
        if stderr and 'error' in stderr.lower() and raise_errs:
            raise RuntimeError(f'Error in subprocess command: {command_str}\n\n{stderr}')
        return stderr, stdout

    @staticmethod
    def _read_df(path: Union[str, Path]) -> pd.DataFrame:
        return pd.read_csv(path, sep='\t') if os.path.exists(path) else pd.DataFrame()

    @staticmethod
    def _filter_df_via_equals_conditions(df: pd.DataFrame, *conditions: Tuple[str, str]) -> pd.DataFrame:
        """Filters a dataframe given arbitrary number of equals conditions.

        :param *conditions: Any number of 'col' + 'val' tuples. E.g. passing ('my_col', 'my_val') will create a filter
        condition of df['my_col'] == 'my_val'.
        """
        if len(df) == 0:
            return df  # no output exists for given template for given example
        combined_condition = pd.Series(True, index=df.index)
        for column, value in conditions:
            combined_condition &= (df[column] == value)
        return df[combined_condition]

    def _assert_only_in_correct_template(self, case: Dict[str, str], template: str = None):
        """For a given example case, check that it is in the correct output template and not in others.

        :param template: The alias / common name of the ROBOT template where the case is expected to be found. If None,
         checks to make sure the case is in no template.
        :param case: Dictionary keys are columns to look up in the template dataframe, and the dictionary values are
         the expected values to be found when accessing the row in the dataframe.
        """
        # Check case in correct template
        if template:
            correct_df: pd.DataFrame = self.df_lookup[template]
            correct_df = self._filter_df_via_equals_conditions(correct_df, *case.items())
            self.assertEqual(1, len(correct_df))
        # Check case not in other templates
        for template_i, df_i in self.df_lookup.items():
            # Filter column 'mondo_id' from 'added' case. It will never be in that template.
            case_i: Dict[str, str] = case if template != 'added' else {k: v for k, v in case.items() if k != 'mondo_id'}
            if template_i != template:
                df_i = self._filter_df_via_equals_conditions(df_i, *case_i.items())
                self.assertEqual(0, len(df_i), f'Case found in incorrect template "{template_i}"' + str(case))

    def _assert_in_no_template(self, case: Dict[str, str]):
        """Assert that the case, which may exist in mondo.owl and omim.owl but for which no mapping exists in
        mondo.sssom.tsv, doesn't appear in any template."""
        self._assert_only_in_correct_template(case, '')

    def _common_case_assertions(self, cases: List[Dict[str, str]], template: str):
        """Run common assertions for each individual ROBOT template case"""
        for case in cases:
            self._assert_only_in_correct_template(case, template)
        results: pd.DataFrame = self.df_lookup[template]
        # -1 accounts for the ROBOT subheader
        self.assertEqual(len(cases), len(results) - 1, f'Got a different number of rows in template: {template}.')

    def test_deleted(self):
        """Check that case is marked deleted: Scope + synonym exists in Mondo w/, but it's not in the source ."""
        # todo: account for mapped, account for xref, acount for casing
        pass

    def test_added(self):
        """Check that case is marked added: When scope + synonym doesn't exist in Mondo."""
        cases: List[Dict[str, str]] = [
            # Case 1: Synonym doesn't exist at all on mapped Mondo term
            {
                'mondo_id': 'MONDO:8000008',
                'synonym_scope': 'oio:hasExactSynonym',
                'synonym': 'MARTS1',
                'source_id': 'OMIM:212720',
            },
            # Case 2: Synonym doesn't exist on mapped Mondo term, but it is the label
            {
                'mondo_id': 'MONDO:8000008',
                'synonym_scope': 'oio:hasExactSynonym',
                'synonym': 'martsolf syndrome 1',
                'source_id': 'OMIM:212720',
            },
        ]
        self._common_case_assertions(cases, 'added')
        # Case 3: Unmapped: Synonym doesn't exist at all in Mondo, but source term isn't mapped to any Mondo term
        self._assert_in_no_template({
            'mondo_id': 'MONDO:999999',
            'synonym_scope': 'oio:hasExactSynonym',
            'synonym': 'Unmapped: Synonym doesn\'t exist at all in Mondo, but source term isn\'t mapped to any Mondo term',
            'source_id': 'OMIM:999999',
        })

    def test_updated(self):
        """Check that case is marked updated: Synonym string is the same, but scope is different

        Case 1: Same casing
        1.1: Source xref exists
        No example or test yet.

        1.2: Source xref doesn't exist
        mondo-edit.obo
            id: MONDO:8000008
            synonym: "MARTSOLF syndrome" BROAD [OMIM:212720]
        omim.owl:
            <owl:Class rdf:about="https://omim.org/entry/212720">
                <oboInOwl:hasExactSynonym>martsolf syndrome

        Case 2: Different casing
        Tests exist, but no examples here.

        Case 3: Mapped vs unmapped
        todo?: No examples or tests yet.
        """
        cases: List[Dict[str, str]] = [
            # Case 1: Same casing: Synonym exists in Mondo, but has different scope (same casing)
            # 1.1. Source attribution exists
            # todo?
            # 1.2. Source attribution doesn't exist
            {
                'mondo_id': 'MONDO:8000008',
                'synonym_scope': 'oio:hasExactSynonym',
                'synonym': 'Fake synonym',
                'source_id': 'OMIM:212720',
            },
            # Case 2: Synonym exists in Mondo w/ different scope and different casing (e.g. lowercase vs UPPERCASE vs
            #   Sentence case)
            # - 2.1. Source attribution exists
            {
                'mondo_id': 'MONDO:8000008',
                'synonym_scope': 'oio:hasExactSynonym',
                'synonym': 'MARTSOLF syndrome',  # casing is 'martsolf syndrome' in OMIM
                'source_id': 'OMIM:212720',
            },
            # - 2.1. Source attribution doesn't exist
            {
                'mondo_id': 'MONDO:8000008',
                'synonym_scope': 'oio:hasExactSynonym',
                'synonym': 'Martsolf syndrome',  # casing is 'martsolf syndrome' in OMIM
                'source_id': 'OMIM:212720',
            },
        ]
        self._common_case_assertions(cases, 'updated')

    def test_confirmed(self):
        """Check that case is marked confirmed: When scope + synonym string are same.

        Case 1: Same casing
        The difference between the two case types, as in the examples below:
         - Case 1.1: [OMIM:212720]
         - Case 1.2: []

        1.1: has source xref
        mondo-edit.obo
            id: MONDO:8000008
            synonym: "cataract-intellectual disability-hypogonadism" EXACT [OMIM:212720]
        omim.owl:
            <owl:Class rdf:about="https://omim.org/entry/212720">
                <oboInOwl:hasExactSynonym>cataract-mental retardation-hypogonadism

        1.2: missing a source xref
        mondo-edit.obo
            id: MONDO:8000008
            synonym: "cataract-intellectual disability-hypogonadism" RELATED []
        omim.owl:
            <owl:Class rdf:about="https://omim.org/entry/212720">
                <oboInOwl:hasRelatedSynonym>cataract-intellectual disability-hypogonadism

        Case 2: Different casing
        See tests below for example cases.

        Case 3: Mapped vs unmapped
        See tests below for example cases.
        """
        cases: List[Dict[str, str]] = [
            # Case 1: Same casing
            # 1.1. Has source xref
            {
                'mondo_id': 'MONDO:8000008',
                'synonym_scope': 'oio:hasExactSynonym',
                'synonym': 'cataract-mental retardation-hypogonadism',
                'source_id': 'OMIM:212720',
            },
            # 1.2. Has no source xref
            {
                'mondo_id': 'MONDO:8000008',
                'synonym_scope': 'oio:hasRelatedSynonym',
                'synonym': 'cataract-intellectual disability-hypogonadism',
                'source_id': 'OMIM:212720',
            },
            # Case 2: Different casing
            # 2.1. Has source xref
            {
                'mondo_id': 'MONDO:8000008',
                'synonym_scope': 'oio:hasExactSynonym',
                'synonym': 'fake confirmed: lower in Mondo, upper in source',
                'source_id': 'OMIM:212720',
            },
            # 2.2. Has no source xref
            {
                'mondo_id': 'MONDO:8000008',
                'synonym_scope': 'oio:hasExactSynonym',
                'synonym': 'fake confirmed: lower in Mondo, upper in source - no xref',
                'source_id': 'OMIM:212720',
            },
        ]
        self._common_case_assertions(cases, 'confirmed')
        # Case 3: Unmapped: Synonym doesn't exist at all in Mondo, but source term isn't mapped to any Mondo term
        self._assert_in_no_template({
            'mondo_id': 'MONDO:999999',
            'synonym_scope': 'oio:hasExactSynonym',
            'synonym': 'Unmapped: Synonym exists in 1 source and 1 Mondo term, but no mapping',
            'source_id': 'OMIM:999999',
        })
