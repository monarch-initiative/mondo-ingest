"""Filter out cases where curation is needed"""
import os
import shutil
import sys
from argparse import ArgumentParser
from datetime import datetime
from pathlib import Path
from typing import Union, List

import pandas as pd
from oaklib import get_adapter
from oaklib.types import CURIE, URI

from src.scripts.utils import remove_angle_brackets

HERE = Path(os.path.abspath(os.path.dirname(__file__)))
SRC_DIR = HERE.parent
PROJECT_ROOT = SRC_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))
from src.scripts.sync_synonym import _common_operations, _read_sparql_output_tsv


def _read_synonym_file(path: Union[Path, str], case: str) -> pd.DataFrame:
    """Does special operations for reading in a synonym sync robot.tsv in this context"""
    df = pd.read_csv(path, sep='\t').rename(columns={'synonym_scope_source': 'synonym_scope'}) \
        .drop(0)[['synonym', 'synonym_scope', 'mondo_id', 'source_id', 'synonym_type']].fillna('')
    df['synonym_type'] = df['synonym_type'].apply(
        lambda x: x.replace('http://purl.obolibrary.org/obo/mondo#ABBREVIATION', 'MONDO:ABBREVIATION'))
    df['case'] = case
    return df


def sync_synonyms_curation_filtering(
    added_path: Union[Path, str], confirmed_path: Union[Path, str], updated_path: Union[Path, str],
    mondo_synonyms_path: Union[Path, str], mondo_db_path: Union[Path, str], outpath: Union[Path, str]
):
    """Filter out cases where curation is needed"""
    # todo temp: backup temporarily for development; remove when done
    tmp_dir = SRC_DIR / 'ontology' / 'tmp'
    t0 = str(datetime.now())
    for file in [added_path, confirmed_path, updated_path]:
        shutil.copy(file, tmp_dir / f"{Path(file).name.replace('.robot.tsv', '')}_{t0}.robot.tsv")

    # Read -added & -updated
    df_add: pd.DataFrame = _read_synonym_file(added_path, 'added')
    df_upd: pd.DataFrame = _read_synonym_file(updated_path, 'updated')

    # Read -confirmed & ascertain unconfirmed
    df_conf = pd.read_csv(confirmed_path, sep='\t').drop(0).fillna('')  # Not de-duped. Used for informational purposes.
    df_conf['case'] = 'confirmed'
    df_conf['synonym_scope'] = df_conf['synonym_scope_source']
    df_mondo_syns = _read_sparql_output_tsv(mondo_synonyms_path).fillna('').rename(columns={
        'cls_id': 'mondo_id', 'cls_label': 'mondo_label', 'synonym_type': 'synonym_type_mondo', 'dbXref': 'source_id'})
    df_mondo_syns = df_mondo_syns[~df_mondo_syns['mondo_label'].str.startswith('obsolete ')]
    merge_columns = ['synonym', 'synonym_scope', 'mondo_id']
    df_mondo_conf = df_mondo_syns.merge(
        df_conf[merge_columns + ['case']], on=merge_columns, how='left', suffixes=('', '_conf'))
    df_mondo_syns['case'] = df_mondo_conf['case'].fillna('unconfirmed')

    # Group all sources of synonyms & labels cases together
    df_all = pd.concat([df_add, df_upd, df_mondo_syns], ignore_index=True).fillna('')
    df_all['synonym_type'] = df_all.apply(
        lambda row: row['synonym_type'] if row['synonym_type'] else row['synonym_type_mondo'], axis=1)

    # Discover review cases: exactSynonym appears in multiple terms
    # - find all duplicative cases where scope+synonym has >1 instance
    df_all_dupes = df_all[df_all.groupby(['synonym', 'synonym_scope']).transform('size') > 1]\
        .sort_values(['synonym', 'synonym_scope', 'mondo_id', 'source_id'])
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
    oi = get_adapter(mondo_db_path)
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
    del df_review_labs['mondo_label']  # this is left over from the merge; not useful information
    # - remove abbreviations; we aren't bothered by duplicates of this type
    df_review_labs = df_review_labs.merge(df_mondo_syns[['mondo_id', 'synonym', 'synonym_scope', 'synonym_type_mondo']],
        on=['mondo_id', 'synonym', 'synonym_scope'], how='left').fillna('')
    df_review_labs['synonym_type'] = df_review_labs.apply(
        lambda row: row['synonym_type'] if row['synonym_type'] else row['synonym_type_mondo'], axis=1)
    del df_review_labs['synonym_type_mondo']
    df_review_labs['synonym_type'] = df_review_labs.groupby(
        'synonym')['synonym_type'].transform(lambda x: '|'.join(filter(None, x)))
    df_review_labs = df_review_labs[~df_review_labs['synonym_type'].str.contains('MONDO:ABBREVIATION')]

    # Generate outputs & save
    df_review = pd.concat([df_review_syns, df_review_labs], ignore_index=True)[['synonym', 'mondo_id', 'source_id',
        'case', 'synonym_type', 'filtered_because_this_mondo_id_already_has_this_synonym_as_its_label']]\
        .sort_values(['synonym', 'mondo_id'])
    df_review.to_csv(outpath, sep='\t', index=False)

    df_filtered = df_all[~df_all.index.isin(df_review.index)]
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
        '-M', '--mondo-db-path', required=True, help='Path to Mondo SemanticSQL DB.')
    parser.add_argument(
        '-o', '--outpath', required=True,
        help='Path to curation file for review.')
    sync_synonyms_curation_filtering(**vars(parser.parse_args()))


if __name__ == '__main__':
    cli()
