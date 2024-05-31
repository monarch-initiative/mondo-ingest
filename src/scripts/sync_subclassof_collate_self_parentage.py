"""Sync SubClass: Report for Mondo classes having themselves as parents in the "added" template (legal proxy merges)."""
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
from src.scripts.sync_subclassof_config import COLLATE_SELF_PARENTAGE_DEFAULT_PATH, EX_DEFAULTS, \
    SELF_PARENTAGE_DEFAULT_FILE_STEM, TMP_DIR
DESC = 'Generating report for Mondo classes having themselves as parents in the "added" template (legal proxy merges).'


def aggregate_inputs() -> pd.DataFrame:
    """Aggregate all input files for each source
    todo: this code is very similar to what's in the other collation script, so I'd like to abstract if possible at
     some point. Some differences that the other script has, which could be dealt w/ via parameterization:
      - deletes 2 columns in each loopp
      - merged field names differ
    """
    df = pd.DataFrame()
    files: List[str] = glob(str(TMP_DIR / f'*{SELF_PARENTAGE_DEFAULT_FILE_STEM}'))
    if not files:
        return df

    for file in files:
        df_i = pd.read_csv(file, sep='\t')
        # Set initial dataframe for which subsequent ones will be joined
        if len(df) == 0:
            df = df_i
            continue
        # Concatenate data
        df = pd.concat([df, df_i])
    return df


def collate_self_parentage(
    mondo_mappings_path: str = EX_DEFAULTS['mondo_mappings_path'], outpath: str = COLLATE_SELF_PARENTAGE_DEFAULT_PATH
):
    """'Report for Mondo classes having themselves as parents in the "added" template (legal proxy merges)."""
    logging.info(DESC)
    df: pd.DataFrame = aggregate_inputs()
    if len(df) == 0:
        logging.warning(
            'collate_self_parentage():'
            'No inputs detected for collation of "self-parentage" source cases. This is probably the result of '
            'running this step out of order. This should come at the end of the synchronization (subclass) pipeline, '
            'after outputs have been generated for each class.')
        return
    df.to_csv(outpath, sep='\t', index=False)


def cli():
    """Command line interface."""
    parser = ArgumentParser(
        prog='sync-subclassof: Collate self-parentage cases',
        description='For: ' + DESC)
    parser.add_argument(
        '-m', '--mondo-mappings-path', required=False, default=EX_DEFAULTS['mondo_mappings_path'],
        help='Path to file containing all known Mondo mappings, in SSSOM format.')
    parser.add_argument(
        '-o', '--outpath', required=False,
        default=TMP_DIR / 'sync-subClassOf.added.self-parentage.tsv', help='Path to save output.')
    d: Dict = vars(parser.parse_args())
    collate_self_parentage(**d)


if __name__ == '__main__':
    cli()
