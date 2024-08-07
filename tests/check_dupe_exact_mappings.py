"""Report duplicate exact mappings in mondo.sssom.tsv"""
import logging
import os
import sys
from argparse import ArgumentParser
from pathlib import Path
from typing import Set

import pandas as pd
from oaklib.types import CURIE

HERE = Path(os.path.abspath(os.path.dirname(__file__)))
PROJECT_ROOT = HERE.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tests.config import TMP_DIR

DEFAULTS = {
    'mondo_mappings_path': str(TMP_DIR / 'mondo.sssom.tsv'),
}


def _report_duplicate_exact_mappings_by_direction(df: pd.DataFrame, by=['mondo', 'source'][0]):
    """Report duplciate exact mappings in mondo.sssom.tsv, based on 1 mondo ID to 2+ source terms, or vice versa"""
    if by not in ['mondo', 'source']:
        raise ValueError("'by' must be either of 'mondo' or 'source'.")
    field = 'subject_id' if by == 'mondo' else 'object_id'
    i = 1
    dups = []
    for prefix, df_i in df.groupby('obj_prefix'):
        j = 1
        # Collect all mappings by ID
        row_map_by_mondo_id = {}
        for _index, row in df_i.iterrows():
            row = dict(row)
            if row[field] not in row_map_by_mondo_id:
                row_map_by_mondo_id[row[field]] = []
            row_map_by_mondo_id[row[field]].append(row)
        # Filter and name duplicates
        for mappings in row_map_by_mondo_id.values():
            if len(mappings) > 1:
                dups.extend([d | {'dupe_id': i, 'source_dupe_id': f'{prefix}_{j}'} for d in mappings])
                i += 1
                j += 1
    out_df = pd.DataFrame(dups).rename(columns={'obj_prefix': 'source'})[[
        'dupe_id', 'source', 'source_dupe_id', 'subject_id', 'object_id', 'predicate_id', 'subject_label']].sort_values(
        ['dupe_id', 'source', 'source_dupe_id', 'object_id'])
    return out_df


def check_dupe_exact_mappings(
    mondo_mappings_path: str = DEFAULTS['mondo_mappings_path'],
):
    """Run"""
    ss_df = pd.read_csv(mondo_mappings_path, sep='\t', comment='#')
    ss_df = ss_df[ss_df['predicate_id'] == 'skos:exactMatch']
    ss_df['obj_prefix'] = ss_df['object_id'].apply(lambda _id: _id.split(':')[0])
    # df_mondo: Is no problem. Mappings from multiple source IDs to same Mondo ID is fine.
    # df_mondo = _report_duplicate_exact_mappings_by_direction(ss_df, 'mondo')
    df = _report_duplicate_exact_mappings_by_direction(ss_df, 'source')
    df = df[['object_id', 'subject_id', 'predicate_id', 'subject_label']]
    dups: Set[CURIE] = set(df['object_id'])
    if len(df) > 0:
        logging.error(f'Found {len(df)} duplicate exact mapping records in mondo.sssom.tsv for the following IDs:\n'
                      f'{", ".join(dups)}')


def cli():
    """Command line interface."""
    parser = ArgumentParser(
        prog='check-dupe-exact-mappings',
        description='Report duplciate exact mappings in mondo.sssom.tsv')
    parser.add_argument(
        '-m', '--mondo-mappings-path', required=False, default=DEFAULTS['mondo_mappings_path'],
        help='Path to file containing all known Mondo mappings, in SSSOM format.')
    d = vars(parser.parse_args())
    check_dupe_exact_mappings(**d)


if __name__ == '__main__':
    cli()
