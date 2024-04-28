"""Sync SubClass: Update report for Mondo classes having themselves as parents in the 'added' template."""
import logging
import os
import sys
from argparse import ArgumentParser
from pathlib import Path
from typing import Dict

import pandas as pd

HERE = Path(os.path.abspath(os.path.dirname(__file__)))
SRC_DIR = HERE.parent
PROJECT_ROOT = SRC_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))
from src.scripts.sync_subclassof_config import OUTPATH_SELF_PARENTAGE, EX_DEFAULTS


def collate_self_parentage(
        mondo_mappings_path: str = EX_DEFAULTS['mondo_mappings_path'], in_outpath: str = OUTPATH_SELF_PARENTAGE
):
    """Update report for Mondo classes having themselves as parents in the 'added' template."""
    logging.info('Updateing report for Mondo classes having themselves as parents in the "added" template.')

    sssom_df = pd.read_csv(mondo_mappings_path, sep='\t', comment='#')
    id_label_map: Dict[str, str] = dict(zip(sssom_df['object_id'], sssom_df['object_label']))

    df = pd.read_csv(in_outpath, sep='\t').rename(columns={
        'subject_mondo_id': 'mondo_id', 'subject_mondo_label': 'mondo_label'})
    df['subject_source_label'] = df['subject_source_id'].map(id_label_map)
    df['object_source_label'] = df['object_source_id'].map(id_label_map)
    df = df[['mondo_id', 'mondo_label', 'subject_source_id', 'subject_source_label', 'object_source_id', 'object_source_label']]

    df.to_csv(in_outpath, sep='\t', index=False)


def cli():
    """Command line interface."""
    parser = ArgumentParser(
        prog='sync-subclassof: Collate self-parentage issues',
        description='Update report for Mondo classes having themselves as parents in the "added" template.')

    parser.add_argument(
        '-m', '--mondo-mappings-path', required=False, default=EX_DEFAULTS['mondo_mappings_path'],
        help='Path to file containing all known Mondo mappings, in SSSOM format.')
    parser.add_argument(
        '-o', '--in-outpath', required=False, default=OUTPATH_SELF_PARENTAGE,
        help='The file containing all of the cases. It will be read as input and updated / saved again.')
    d: Dict = vars(parser.parse_args())
    collate_self_parentage(**d)


if __name__ == '__main__':
    cli()
