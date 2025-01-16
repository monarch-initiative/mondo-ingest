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
from src.scripts.sync_synonym import _common_operations, _read_sparql_output_tsv


def sync_synonyms_curation_filtering(
    added_path: Union[Path, str], confirmed_path: Union[Path, str], updated_path: Union[Path, str],
    mondo_synonyms_path: Union[Path, str], outpath: Union[Path, str]
):
    """Filter out cases where curation is needed"""
    # todo temp: backup temporarily for development; remove when done
    tmp_dir = SRC_DIR / 'ontology' / 'tmp'
    t0 = str(datetime.now())
    for file in [added_path, confirmed_path, updated_path]:
        shutil.copy(file, tmp_dir / f"{Path(file).name.replace('.robot.tsv', '')}_{t0}.robot.tsv")

    # Read -added & -updated
    add_df = pd.read_csv(added_path, sep='\t').drop(0)
    add_df['case'] = 'added'
    add_df['synonym_scope'] = add_df['synonym_scope_source']
    upd_df = pd.read_csv(updated_path, sep='\t').drop(0)
    upd_df['case'] = 'updated'
    upd_df['synonym_scope'] = upd_df['synonym_scope_source']

    # Read -confirmed & ascertain unconfirmed
    conf_df = pd.read_csv(confirmed_path, sep='\t').drop(0)  # Not de-duped. Used for informational purposes.
    conf_df['case'] = 'confirmed'
    conf_df['synonym_scope'] = conf_df['synonym_scope_source']
    mondo_df = _read_sparql_output_tsv(mondo_synonyms_path)\
        .rename(columns={'cls_id': 'mondo_id', 'synonym_type': 'synonym_type_mondo', 'dbXref': 'source_id'})
    merge_columns = ['synonym', 'synonym_scope', 'mondo_id']
    merged_df = mondo_df.merge(conf_df[merge_columns + ['case']], on=merge_columns, how='left', suffixes=('', '_conf'))
    mondo_df['case'] = merged_df['case'].fillna('unconfirmed')

    # Generate review cases
    df = pd.concat([add_df, upd_df, mondo_df], ignore_index=True).fillna("")
    # - Find all duplicative cases where scope+synonym has >1 instance
    dupes_mask = df.groupby(['synonym', 'synonym_scope']).transform('size') > 1
    df_all_dupes = df[dupes_mask].sort_values(['synonym', 'synonym_scope', 'mondo_id', 'source_id'])
    # - Find all cases where, among these multiple synonym+scope instances, there is >1 associated mondo_id
    multiple_mondo_mask = df_all_dupes.groupby(['synonym', 'synonym_scope'])['mondo_id'].transform('nunique') > 1
    df_review = df_all_dupes[multiple_mondo_mask]
    df_review = df_review.sort_values(['synonym', 'synonym_scope', 'mondo_id'])
    # - Leave only exactMatch cases
    df_review = df_review[df_review['synonym_scope'] == 'oio:hasExactSynonym']
    # - Remove abbreviations; we aren't bothered by duplicates of this type
    non_abbrev_mask = ~df_review['synonym_type'].str.contains("http://purl.obolibrary.org/obo/mondo#ABBREVIATION")
    df_review = df_review[non_abbrev_mask][['synonym', 'synonym_scope', 'mondo_id', 'source_id', 'case']]
    df_review.to_csv(outpath, sep='\t', index=False)

    # Filter cases from -added & -updated
    df_filtered = df[~df.index.isin(df_review.index)]

    # todo temp - analysis, if needed
    ar1 = df_review[df_review['case'] == 'unconfirmed']
    # examine
    f_df = pd.read_csv('~/Desktop/failures.csv').rename(columns={'value': 'synonym'})
    il = f_df.merge(df_filtered, on=['synonym'], how='left')  # 1329  todo: why some not have 'case'? makes sense if they are not from syn sync and pre-existed in Mondo but that does not appear to be case because 0 fails b4
    ii = f_df.merge(df_filtered, on=['synonym'], how='inner')  # 358
    # for 1 class i looked at, it's in review and not in the sync
    ar = df_review = df_review[df_review['synonym'] == 'Zlotogora-Ogur syndrome']
    af = df_review = df_filtered[df_filtered['synonym'] == 'Zlotogora-Ogur syndrome']

    # todo temp: don't run these lines until i'm done w/ code and ready to push again
    _common_operations(df_filtered[df_filtered['case'] == 'added'], added_path, dont_make_scope_cols=True)
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
        '-m', '--mondo-synonyms-path', required=True,
        help='Path to a TSV containing information about Mondo synonyms. Columns: ?mondo_id, ?dbXref, ?synonym_scope, '
             '?synonym, synonym_type.')
    parser.add_argument(
        '-o', '--outpath', required=True,
        help='Path to curation file for review.')
    sync_synonyms_curation_filtering(**vars(parser.parse_args()))


if __name__ == '__main__':
    cli()
