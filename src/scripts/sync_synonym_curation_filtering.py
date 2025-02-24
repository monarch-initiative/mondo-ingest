"""Filter out cases where curation is needed"""
import os
import sys
from argparse import ArgumentParser
from pathlib import Path
from typing import Union, List

import pandas as pd
from oaklib import get_adapter
from oaklib.types import CURIE, URI


HERE = Path(os.path.abspath(os.path.dirname(__file__)))
SRC_DIR = HERE.parent
PROJECT_ROOT = SRC_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))
from src.scripts.sync_synonym import _common_operations, _read_sparql_output_tsv
from src.scripts.utils import remove_angle_brackets


def _read_synonym_file(path: Union[Path, str], case: str) -> pd.DataFrame:
    """Does special operations for reading in a synonym sync robot.tsv in this context"""
    df = pd.read_csv(path, sep='\t').rename(columns={'synonym_scope_source': 'synonym_scope'}).drop(0).fillna('')
    df['synonym_type'] = df['synonym_type'].apply(
        lambda x: x.replace('http://purl.obolibrary.org/obo/mondo#ABBREVIATION', 'MONDO:ABBREVIATION'))
    df['case'] = case
    return df


def sync_synonyms_curation_filtering(
    added_inpath: Union[Path, str], confirmed_inpath: Union[Path, str], updated_inpath: Union[Path, str],
    added_outpath: Union[Path, str], confirmed_outpath: Union[Path, str], updated_outpath: Union[Path, str],
    mondo_synonyms_inpath: Union[Path, str], mondo_db_inpath: Union[Path, str], review_outpath: Union[Path, str],
    filter_updated=False
):
    """Filter out cases where curation is needed"""
    # Read -added & -updated
    df_add: pd.DataFrame = _read_synonym_file(added_inpath, 'added')
    df_upd: pd.DataFrame = _read_synonym_file(updated_inpath, 'updated')

    # Read -confirmed & ascertain unconfirmed
    df_conf = pd.read_csv(confirmed_inpath, sep='\t')
    df_conf2 = df_conf.copy().drop(0).fillna('')
    df_conf2['case'] = 'confirmed'
    df_conf2['synonym_scope'] = df_conf2['synonym_scope_source']
    df_mondo_syns = _read_sparql_output_tsv(mondo_synonyms_inpath).fillna('').rename(columns={
        'cls_id': 'mondo_id', 'cls_label': 'mondo_label', 'synonym_type': 'synonym_type_mondo', 'dbXref': 'source_id'})
    df_mondo_syns = df_mondo_syns[~df_mondo_syns['mondo_label'].str.startswith('obsolete ')]
    merge_columns = ['synonym', 'synonym_scope', 'mondo_id']
    df_mondo_conf = df_mondo_syns.merge(
        df_conf2[merge_columns + ['case']], on=merge_columns, how='left', suffixes=('', '_conf'))
    df_mondo_syns['case'] = df_mondo_conf['case'].fillna('unconfirmed')

    # Group all sources of synonyms & labels cases together
    df_all = pd.concat([df_add, df_upd, df_mondo_syns], ignore_index=True).fillna('')
    df_all['synonym_type'] = df_all.apply(
        lambda row: row['synonym_type'] if row['synonym_type'] else row['synonym_type_mondo'], axis=1)

    # Discover review cases: exactSynonym appears in multiple terms
    # - find all duplicative cases where scope+synonym has >1 instance
    df_all_dupes = df_all[df_all.groupby(['synonym', 'synonym_scope']).transform('size') > 1]\
        .sort_values(['synonym', 'synonym_scope', 'mondo_id', 'source_id'])
    df_review_syns = pd.DataFrame()
    if len(df_all_dupes) > 0:
        # - find all cases where, among these multiple synonym+scope instances, there is >1 associated mondo_id
        df_review_syns = df_all_dupes[
            df_all_dupes.groupby(['synonym', 'synonym_scope'])['mondo_id'].transform('nunique') > 1]
        df_review_syns = df_review_syns.sort_values(['synonym', 'synonym_scope', 'mondo_id'])
        # - leave only exactMatch cases
        df_review_syns = df_review_syns[df_review_syns['synonym_scope'] == 'oio:hasExactSynonym']
        # - before filtering abbreviations: handle edge cases of missing synonym_type for 1 of the duplicates
        df_review_syns['synonym_type'] = df_review_syns.groupby(
            'synonym')['synonym_type'].transform(lambda x: '|'.join(filter(None, x)))
        # - remove abbreviations; we aren't bothered by duplicates of this type
        df_review_syns = df_review_syns[~df_review_syns['synonym_type'].str.contains('MONDO:ABBREVIATION')]

    # Discover review cases: exactSynonym appears as label in another term
    # - get mondo labels
    # todo: this (reading Mondo & only filtering by its terms (nad possibly labels)) should be a utility func somewhere
    oi = get_adapter(mondo_db_inpath)
    ids_all: List[Union[CURIE, URI]] = [x for x in oi.entities(filter_obsoletes=False)]
    ids_all = remove_angle_brackets(ids_all)
    id_labels_all: List[tuple] = [x for x in oi.labels(ids_all)]
    df_mondo_labs = pd.DataFrame(id_labels_all, columns=['mondo_id', 'mondo_label']).fillna('')
    df_mondo_labs['prefix'] = df_mondo_labs['mondo_id'].str.split(':', expand=True)[0]
    df_mondo_labs = df_mondo_labs[df_mondo_labs['prefix'] == 'MONDO']
    del df_mondo_labs['prefix']
    # - get relevant synonym sync cases to filter
    df_sync = pd.concat([df_add, df_upd], ignore_index=True)
    df_sync = df_sync[df_sync['synonym_scope'] == 'oio:hasExactSynonym']
    # - filter to keep only rows where mondo_ids are different
    df_review_labs = df_sync.merge(df_mondo_labs, left_on=['synonym'], right_on=['mondo_label'], how='inner')
    df_review_labs = df_review_labs[df_review_labs['mondo_id_x'] != df_review_labs['mondo_id_y']].rename(columns={
        'mondo_id_x': 'mondo_id', 'mondo_id_y': 'filtered_because_this_mondo_id_already_has_this_synonym_as_its_label'})
    if len(df_review_labs) > 0:
        # - remove abbreviations; we aren't bothered by duplicates of this type
        df_review_labs = df_review_labs.drop('synonym_type_mondo', axis=1)\
            .merge(df_mondo_syns[['mondo_id', 'synonym', 'synonym_scope', 'synonym_type_mondo']],
            on=['mondo_id', 'synonym', 'synonym_scope'], how='left').fillna('')
        df_review_labs['synonym_type'] = df_review_labs.apply(
            lambda row: row['synonym_type'] if row['synonym_type'] else row['synonym_type_mondo'], axis=1)
        df_review_labs['synonym_type'] = df_review_labs.groupby(
            'synonym')['synonym_type'].transform(lambda x: '|'.join(set(filter(None, x))))
        df_review_labs = df_review_labs[~df_review_labs['synonym_type'].str.contains('MONDO:ABBREVIATION')]

    # Generate outputs & save
    # - review file
    df_review = pd.concat([df_review_syns, df_review_labs], ignore_index=True)
    if len(df_review) > 0:
        df_review = df_review[['synonym', 'mondo_id', 'source_id', 'case', 'synonym_type',
            'filtered_because_this_mondo_id_already_has_this_synonym_as_its_label']]\
        .sort_values(['synonym', 'mondo_id'])
    df_review.to_csv(review_outpath, sep='\t', index=False)
    # - unfiltered outputs
    df_upd.to_csv(updated_outpath, sep='\t', index=False)
    df_conf.to_csv(confirmed_outpath, sep='\t', index=False)
    # - filtered outputs
    df_filtered = df_all[~df_all.index.isin(df_review.index)]
    if filter_updated:
        _common_operations(df_filtered[df_filtered['case'] == 'updated'], updated_outpath, dont_make_scope_cols=True)
    _common_operations(df_filtered[df_filtered['case'] == 'added'], added_outpath, dont_make_scope_cols=True)


def cli():
    """Command line interface."""
    parser = ArgumentParser(
        prog='sync-synonyms-curation-filtering',
        description='Filter out cases where curation is needed')
    parser.add_argument(
        '-a', '--added-inpath', required=True,
        help='Path to input ROBOT template TSV containing synonyms that aren\'t yet integrated into Mondo.')
    parser.add_argument(
        '-c', '--confirmed-inpath', required=True,
        help='Path to input ROBOT template TSV containing synonym confirmations.')
    parser.add_argument(
        '-u', '--updated-inpath', required=True,
        help='Path to input ROBOT template TSV containing updates to synonym scope.')
    parser.add_argument(
        '-A', '--added-outpath', required=True,
        help='Path to filtered ROBOT template TSV containing synonyms that aren\'t yet integrated into Mondo.')
    parser.add_argument(
        '-C', '--confirmed-outpath', required=True,
        help='Path to filtered ROBOT template TSV containing synonym confirmations.')
    parser.add_argument(
        '-U', '--updated-outpath', required=True,
        help='Path to filtered ROBOT template TSV containing updates to synonym scope.')
    parser.add_argument(
        '-m', '--mondo-synonyms-inpath', required=True,
        help='Path to a TSV containing information about Mondo synonyms. Columns: ?mondo_id, ?dbXref, ?synonym_scope, '
             '?synonym, synonym_type.')
    parser.add_argument(
        '-M', '--mondo-db-inpath', required=True, help='Path to Mondo SemanticSQL DB.')
    parser.add_argument(
        '-o', '--review-outpath', required=True,
        help='Path to curation file for review.')
    sync_synonyms_curation_filtering(**vars(parser.parse_args()))


if __name__ == '__main__':
    cli()
