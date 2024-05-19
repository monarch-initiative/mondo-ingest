"""Sync SubClass: Combine all --outpath-direct-in-mondo-only outputs for all sources."""
import logging
import os
import sys
from argparse import ArgumentParser
from glob import glob
from pathlib import Path
from typing import Dict, List

import pandas as pd

HERE = Path(os.path.abspath(os.path.dirname(__file__)))
SRC_DIR = HERE.parent
PROJECT_ROOT = SRC_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))
from src.scripts.sync_subclassof_config import IN_MONDO_ONLY_FILE_STEM, REPORTS_DIR


def collate_direct_in_mondo_only(outpath=REPORTS_DIR / 'sync-subClassOf.direct-in-mondo-only.tsv'):
    """Combine all --outpath-direct-in-mondo-only outputs for all sources.

    For all subclass relationships in Mondo, shows which sources do not have it and whether no source has it.

    Side effects: Deletes SOURCE.subclass.direct-in-mondo-only.tsv's from which the combination is made."""
    logging.info('Generating report of which subclass axioms are included in which ontologies.')
    files: List[str] = glob(str(REPORTS_DIR / f'*{IN_MONDO_ONLY_FILE_STEM}'))
    if not files:
        logging.warning(
            'collate_direct_in_mondo_only():'
            'No inputs detected for collation of "direct-in-mondo-only" source cases. This is probably the result of '
            'running this step out of order. This should come at the end of the synchronization (subclass) pipeline, '
            'after outputs have been generated for each class.')
        return

    df = pd.DataFrame()
    for file in files:
        df_i = pd.read_csv(file, sep='\t')
        # Set initial dataframe for which subsequent ones will be joined
        if len(df) == 0:
            df = df_i
            continue
        del df_i['subject_label']
        del df_i['object_label']
        # Join data
        df = pd.merge(df, df_i, on=['subject_id', 'object_id'])

    # Find: which relationships are in no source?
    source_cols = [x for x in df.columns if x.startswith('in_')]
    def _aggregate(row: pd.Series, cols=source_cols):
        """Determine status of edge as it pertains to all sources"""
        return 'SUPPORTED' in set([row[x] for x in cols])
    df['in_any_source'] = df.apply(_aggregate, axis=1)

    # Format & save
    # todo: for some reason the sorting is off; It goes FALSE-MISSING -> True -> False
    df = df[['subject_id', 'object_id', 'in_any_source', 'subject_label', 'object_label'] + source_cols].sort_values(
        ['in_any_source', 'subject_id', 'object_id'], ascending=[False, True, True])
    df.to_csv(outpath, sep='\t', index=False)
    # Delete inputs no longer needed
    for file in files:
        os.remove(file)


def cli():
    """Command line interface."""
    parser = ArgumentParser(
        prog='sync-subclassof: Collate direct rels in Mondo only',
        description='Combine all --outpath-direct-in-mondo-only outputs for all sources at given path, using those as '
                    'inputs, and then deletes them after. This flag should only be used by itself.')
    parser.add_argument(
        '-o', '--outpath', required=False,
        default=REPORTS_DIR / 'sync-subClassOf.direct-in-mondo-only.tsv', help='Path to save output.')
    d: Dict = vars(parser.parse_args())
    collate_direct_in_mondo_only(**d)


if __name__ == '__main__':
    cli()
