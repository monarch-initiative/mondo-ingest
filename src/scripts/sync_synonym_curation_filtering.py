"""Filter out cases where curation is needed"""
import os
import shutil
import sys
from argparse import ArgumentParser
from datetime import datetime
from pathlib import Path
from typing import Union, List, Dict

import pandas as pd
from oaklib import get_implementation_from_shorthand
from oaklib.types import CURIE, URI

from src.scripts.utils import remove_angle_brackets

HERE = Path(os.path.abspath(os.path.dirname(__file__)))
SRC_DIR = HERE.parent
PROJECT_ROOT = SRC_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))
from src.scripts.sync_synonym import _common_operations, _read_sparql_output_tsv


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
    df_add = pd.read_csv(added_path, sep='\t').rename(columns={'synonym_scope_source': 'synonym_scope'})\
        .drop(0)[['synonym', 'synonym_scope', 'mondo_id', 'source_id', 'synonym_type']]
    df_add['case'] = 'added'
    df_upd = pd.read_csv(updated_path, sep='\t').rename(columns={'synonym_scope_source': 'synonym_scope'})\
        .drop(0)[['synonym', 'synonym_scope', 'mondo_id', 'source_id', 'synonym_type']]
    df_upd['case'] = 'updated'

    # Read -confirmed & ascertain unconfirmed
    df_conf = pd.read_csv(confirmed_path, sep='\t').drop(0)  # Not de-duped. Used for informational purposes.
    df_conf['case'] = 'confirmed'
    df_conf['synonym_scope'] = df_conf['synonym_scope_source']
    df_mondo_syns = _read_sparql_output_tsv(mondo_synonyms_path).rename(columns={
        'cls_id': 'mondo_id', 'cls_label': 'mondo_label', 'synonym_type': 'synonym_type_mondo', 'dbXref': 'source_id'})
    merge_columns = ['synonym', 'synonym_scope', 'mondo_id']
    df_mondo_conf = df_mondo_syns.merge(
        df_conf[merge_columns + ['case']], on=merge_columns, how='left', suffixes=('', '_conf'))
    df_mondo_syns['case'] = df_mondo_conf['case'].fillna('unconfirmed')

    # Group all sources of synonyms & labels cases together
    df_all = pd.concat([df_add, df_upd, df_mondo_syns], ignore_index=True).fillna("")

    # Discover review cases: Duplciate synonyms
    # - Find all duplicative cases where scope+synonym has >1 instance
    dupes_mask = df_all.groupby(['synonym', 'synonym_scope']).transform('size') > 1
    df_all_dupes = df_all[dupes_mask].sort_values(['synonym', 'synonym_scope', 'mondo_id', 'source_id'])
    # - Find all cases where, among these multiple synonym+scope instances, there is >1 associated mondo_id
    multiple_mondo_mask = df_all_dupes.groupby(['synonym', 'synonym_scope'])['mondo_id'].transform('nunique') > 1
    df_review_syns = df_all_dupes[multiple_mondo_mask]
    df_review_syns = df_review_syns.sort_values(['synonym', 'synonym_scope', 'mondo_id'])
    # - Leave only exactMatch cases
    df_review_syns = df_review_syns[df_review_syns['synonym_scope'] == 'oio:hasExactSynonym']
    # - Remove abbreviations; we aren't bothered by duplicates of this type
    non_abbrev_mask = ~df_review_syns['synonym_type'].str.contains("http://purl.obolibrary.org/obo/mondo#ABBREVIATION")
    df_review_syns = df_review_syns[non_abbrev_mask]


    # Discover review cases: Duplciate synonyms
    # - Get mondo labels
    # todo: this should be a utility func somewhere
    oi = get_implementation_from_shorthand(mondo_db_path)
    ids_all: List[Union[CURIE, URI]] = [x for x in oi.entities(filter_obsoletes=False)]
    ids_all = remove_angle_brackets(ids_all)
    id_labels_all: List[tuple] = [x for x in oi.labels(ids_all)]
    df_mondo_labs = pd.DataFrame(id_labels_all, columns=['mondo_id', 'mondo_label'])
    df_mondo_labs['prefix'] = df_mondo_labs['mondo_id'].str.split(':', expand=True)[0]
    df_mondo_labs = df_mondo_labs[df_mondo_labs['prefix'] == 'MONDO']
    del df_mondo_labs['prefix']
    # - Get relevant synonym sync cases to filter
    df_sync = pd.concat([df_add, df_upd], ignore_index=True)
    df_sync = df_sync[df_sync['synonym_scope'] == 'oio:hasExactSynonym']
    # - filter to keep only rows where mondo_ids are different
    df_review_labs = df_sync.merge(df_mondo_labs, left_on=['synonym'], right_on=['mondo_label'], how='inner')
    df_review_labs = df_review_labs[df_review_labs['mondo_id_x'] != df_review_labs['mondo_id_y']].rename(columns={'mondo_id_x': 'mondo_id', 'mondo_id_y': 'filtered_because_this_mondo_id_already_has_this_synonym_as_its_label'})
    del df_review_labs['mondo_label']

    # Generate outputs & save
    df_review = pd.concat([df_review_syns, df_review_labs], ignore_index=True)[['synonym', 'mondo_id', 'source_id', 'case']]
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
