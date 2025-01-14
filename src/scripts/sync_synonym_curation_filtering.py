"""Filter out cases where curation is needed"""
import os
import shutil
import sys
from argparse import ArgumentParser
from datetime import datetime
from pathlib import Path
from typing import Union

import pandas as pd

HERE = Path(os.path.abspath(os.path.dirname(__file__)))
SRC_DIR = HERE.parent
PROJECT_ROOT = SRC_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))
from src.scripts.sync_synonym import _common_operations


def sync_synonyms_curation_filtering(
    added_path: Union[Path, str], confirmed_path: Union[Path, str], updated_path: Union[Path, str],
    outpath: Union[Path, str]
):
    """Filter out cases where curation is needed"""
    # todo temp: backup temporarily for development; remove when done
    tmp_dir = SRC_DIR / 'ontology' / 'tmp'
    t0 = str(datetime.now())
    for file in [added_path, confirmed_path, updated_path]:
        shutil.copy(file, tmp_dir / f"{Path(file).name.replace('.robot.tsv', '')}_{t0}.robot.tsv")

    add_df = pd.read_csv(added_path, sep='\t').drop(0)
    add_df['case'] = 'added'
    conf_df = pd.read_csv(confirmed_path, sep='\t').drop(0)
    conf_df['case'] = 'confirmed'
    upd_df = pd.read_csv(updated_path, sep='\t').drop(0)
    upd_df['case'] = 'updated'
    df = pd.concat([add_df, conf_df, upd_df], ignore_index=True).fillna("")

    # Find all cases where scope+synonym is repeated
    dupes_mask = df.groupby(['synonym', 'synonym_scope_source']).transform('size') > 1
    df_all_dupes = df[dupes_mask].sort_values(['synonym', 'synonym_scope_source', 'mondo_id', 'source_id'])

    # First group by synonym and synonym_scope_source and count unique mondo_ids
    multiple_mondo_mask = df_all_dupes.groupby(['synonym', 'synonym_scope_source'])['mondo_id'].transform('nunique') > 1
    df_review = df_all_dupes[multiple_mondo_mask]
    df_review = df_review.sort_values(['synonym', 'synonym_scope_source', 'mondo_id'])
    # - Remove abbreviations; we aren't bothered by duplicates of this type
    non_abbrev_mask = ~df_review['synonym_type'].str.contains("http://purl.obolibrary.org/obo/mondo#ABBREVIATION")
    df_review = df_review[non_abbrev_mask][['synonym', 'synonym_scope_source', 'mondo_id', 'source_id', 'case']]

    # Save
    df_review.to_csv(outpath, sep='\t', index=False)
    df_filtered = df[~df.index.isin(df_review.index)]
    _common_operations(df_filtered[df_filtered['case'] == 'added'], added_path, dont_make_scope_cols=True)
    _common_operations(df_filtered[df_filtered['case'] == 'confirmed'], confirmed_path, dont_make_scope_cols=True)
    _common_operations(df_filtered[df_filtered['case'] == 'updated'], updated_path, dont_make_scope_cols=True)


def cli():
    """Command line interface."""
    parser = ArgumentParser(
        prog='sync-synonyms-curation-filtering',
        description='Filter out cases where curation is needed')
    parser.add_argument(
        '-a', '--added-path', required=True,
        help='Path to ROBOT template TSV containing synonyms that aren\'t yet integrated into Mondo.')
    parser.add_argument(
        '-c', '--confirmed-path', required=True,
        help='Path to ROBOT template TSV containing synonym confirmations.')
    parser.add_argument(
        '-u', '--updated-path', required=True,
        help='Path to ROBOT template TSV containing updates to synonym scope.')
    parser.add_argument(
        '-o', '--outpath', required=True,
        help='Path to curation file for review.')
    sync_synonyms_curation_filtering(**vars(parser.parse_args()))


if __name__ == '__main__':
    cli()
