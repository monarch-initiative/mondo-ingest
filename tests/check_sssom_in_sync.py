"""Checks that SSSOM is in sync with Mondo by ensuring that all SSSOM doesn't have any novel IDs."""
import logging
import os
import sys
from argparse import ArgumentParser
from pathlib import Path
from typing import Dict, List, Set, Union

import pandas as pd
from oaklib import get_adapter
from oaklib.implementations import SqlImplementation
from oaklib.types import CURIE, URI


HERE = Path(os.path.abspath(os.path.dirname(__file__)))
PROJECT_ROOT = HERE.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tests.config import TMP_DIR

DEFAULTS = {
    'mondo_db_path': str(TMP_DIR / 'mondo.db'),
    'mondo_mappings_path': str(TMP_DIR / 'mondo.sssom.tsv'),
}


def check_sssom_in_sync(
    mondo_db_path: str = DEFAULTS['mondo_db_path'], mondo_mappings_path: str = DEFAULTS['mondo_mappings_path'],
    filter_obsoletes=True
):
    """Run"""
    # Read Mondo
    mondo_db: SqlImplementation = get_adapter(mondo_db_path)

    # Read SSSOM
    ss_df = pd.read_csv(mondo_mappings_path, sep='\t', comment='#')
    # - filter: Only exact matches
    ss_df = ss_df[ss_df['predicate_id'] == 'skos:exactMatch']
    # todo: ordo fix: temp until fixed: https://github.com/monarch-initiative/mondo-ingest/issues/369
    ss_df['object_id'] = ss_df['object_id'].apply(lambda _id: _id.replace('orphanet.ordo', 'Orphanet'))

    # Gather IDs
    all_ids_db: List[Union[URI, CURIE]] = [x for x in mondo_db.entities(filter_obsoletes=filter_obsoletes)]
    mondo_ids_db: Set[CURIE] = set([x for x in all_ids_db if x.startswith('MONDO:')])
    if filter_obsoletes:
        ss_df = ss_df[~ss_df['subject_label'].str.startswith('obsolete')]
    mondo_ids_sssom: Set[CURIE] = set(ss_df['subject_id'])

    # Set differences
    in_db_only = mondo_ids_db.difference(mondo_ids_sssom)
    in_sssom_only = mondo_ids_sssom.difference(mondo_ids_db)
    all_problematic_ids = in_db_only.union(in_sssom_only)

    # Labels
    labels_lookup_db: Dict[CURIE, str] = {y[0]: y[1] for y in [x for x in mondo_db.labels(mondo_ids_db)]}
    labels_lookup_sssom: Dict[CURIE, str] = ss_df.set_index('subject_id')['subject_label'].to_dict()
    labels_lookup = labels_lookup_db | labels_lookup_sssom  # any labels in former replaced by latter; should be same

    # Create dataframe & save
    df = pd.DataFrame({
        'subject_id': list(all_problematic_ids),
        'subject_label': [labels_lookup[x] for x in all_problematic_ids],
    })
    df['in_ontology_only'] = df['subject_id'].apply(lambda x: x in in_db_only)
    df['in_sssom_only'] = df['subject_id'].apply(lambda x: x in in_sssom_only)
    df = df.sort_values(['in_ontology_only', 'subject_id'])

    # QC check
    in_sssom_not_in_mondo: Set[CURIE] = set(df[df['in_sssom_only'] == True]['subject_id'])
    if in_sssom_not_in_mondo:
        logging.error('The following IDs are in SSSOM but not in Mondo: %s', in_sssom_not_in_mondo)


def cli():
    """Command line interface."""
    parser = ArgumentParser(
        prog='check-sssom-in-sync',
        description='Checks that SSSOM is in sync with Mondo by ensuring that all SSSOM doesn\'t have any novel IDs.')
    parser.add_argument(
        '-D', '--mondo-db-path', required=False, default=DEFAULTS['mondo_db_path'],
        help='Path to SemanticSQL sqlite `mondo.db`.')
    parser.add_argument(
        '-m', '--mondo-mappings-path', required=False, default=DEFAULTS['mondo_mappings_path'],
        help='Path to file containing all known Mondo mappings, in SSSOM format.')
    d = vars(parser.parse_args())
    check_sssom_in_sync(**d)


if __name__ == '__main__':
    cli()
