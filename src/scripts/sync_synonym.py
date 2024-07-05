"""Create outputs for syncing synonyms between Mondo and its sources."""
import logging
import os
import sys
from argparse import ArgumentParser
from pathlib import Path
from typing import Union, List, Tuple, Set, Dict

import pandas as pd
from oaklib import get_adapter
from oaklib.implementations import SqlImplementation
from oaklib.types import CURIE, PRED_CURIE

HERE = Path(os.path.abspath(os.path.dirname(__file__)))
SRC_DIR = HERE.parent
PROJECT_ROOT = SRC_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))
from src.scripts.utils import PREFIX_MAP, get_owned_prefix_map


NON_SOURCE_ID_SOURCE_SPECIFIC_SYNONYM_XREFS = ['OMIM:genemap2']  # current as of 2027/07/15


def _query_synonyms(ids: List[CURIE], db: SqlImplementation) -> pd.DataFrame:
    """Get synonym triples from sqlite DB"""
    tups: Set[Tuple[CURIE, PRED_CURIE, str]] = set()
    for _id in ids:
        for pred, alias in sorted(db.alias_relationships(_id)):
            # - filter all but synonyms: prior in pipeline have already converted other props such as 'label' to syns
            # todo: is this the best filter? is there more that can appear that should be filtered out? Should instead
            #  not filter by things we want out, but by the list of synonym preds we want in?
            if pred == 'rdfs:label':
                continue
            tups.add((_id, pred, alias))
    df = pd.DataFrame(tups, columns=['curie', 'synonym_scope', 'synonym'])
    return df


def _filter_non_intersecting_rows(
        base_df: pd.DataFrame, intersecting_df: pd.DataFrame, join_on: List[str]
) -> pd.DataFrame:
    """Filter out all rows are not in common, given a `join_on`."""
    merge_df = base_df.merge(intersecting_df, on=join_on, how='left', indicator=True)
    filtered_df = merge_df[merge_df['_merge'] == 'left_only'].drop(columns=['_merge'])
    filtered_df = filtered_df.rename(
        columns=lambda x: x[:-2] if x.endswith('_x') else x)[list(base_df.columns)]
    return filtered_df


def sync_synonyms(
    ontology_db_path: Union[Path, str], mondo_synonyms_path: Union[Path, str], mondo_mappings_path: Union[Path, str],
    onto_config_path: Union[Path, str], outpath_added: Union[Path, str], outpath_confirmed: Union[Path, str],
    outpath_deleted: Union[Path, str], outpath_updated: Union[Path, str]
):
    """Create outputs for syncing synonyms between Mondo and its sources.

    todo: possible refactor: labels: Maybe could be done more cleanly and consistently. At first, wanted to add to both
     source_df and mondo_df, but this caused _x and _y cols during joins, or I would have to join on those cols as well.
     So I arbitrarily chose mondo_df. This is fine in all cases but -added, where they're added in a custom way.
    """
    # Get basic info for source
    owned_prefix_map: PREFIX_MAP = get_owned_prefix_map(onto_config_path)
    source_name: str = list(owned_prefix_map)[0]
    source_db: SqlImplementation = get_adapter(ontology_db_path)

    # Filtered mapping set: determine set of mondo/source ID pairs to sync
    mappings_df = pd.read_csv(mondo_mappings_path, sep='\t', comment='#')
    # - filter exact matches
    mappings_df = mappings_df[mappings_df['predicate_id'] == 'skos:exactMatch']
    # - rename cols
    mappings_df = mappings_df.rename(columns={'subject_id': 'mondo_id', 'subject_label': 'mondo_label',
          'object_id': 'source_id', 'object_label': 'source_label'})
    # - remove unneeded cols
    mappings_df = mappings_df[['mondo_id', 'mondo_label', 'source_id', 'source_label']]
    # todo: refactor filtering by prefixes
    #  check this pattern used elsewhere; I think it has. and abstract into func for these 3 lines; 'filter prefixes'
    #  - OR use this?: get_all_owned_terms()
    #    - it seems long and messy compared to these 3 lines, but is more comprehensive. I could make
    #      get_all_owned_terms() a simple 3 line func and then make a separate func for all edge cases?
    #  - note I may have list(owned_prefix_map.keys())[0] instead of list(owned_prefix_map)[0] ins ome places
    # - filter by source
    mappings_df['source_prefix'] = mappings_df['source_id'].apply(lambda x: x.split(':')[0])
    mappings_df = mappings_df[mappings_df['source_prefix'].isin(owned_prefix_map.keys())]
    del mappings_df['source_prefix']
    # - filter obsoletes (from mappings_df --> source_df & mondo_df)
    #  - filter obsoleted in Mondo
    mappings_df = mappings_df[~mappings_df['mondo_label'].str.startswith('obsolete')]
    #  - filter obsoleted in source
    source_obsoletes: Set[CURIE] = set([x for x in source_db.obsoletes()])
    mappings_df = mappings_df[~mappings_df['source_id'].isin(source_obsoletes)]
    # - filter mapped but deleted IDs
    #   If there is no label, we take that as a proxy / sign that it has been deleted. Alternative ways: entities(),
    #   all_entity_curies(), node() (empty props), node_exists() (no: falsely says 'True', prolly cuz bad xrefs exist)
    source_labels: List[Tuple[CURIE, str]] = [x for x in source_db.labels(mappings_df['source_id'].tolist())]
    source_deleted_ids: Set[CURIE] = set([x[0] for x in source_labels if not x[1]])
    mappings_df = mappings_df[~mappings_df['source_id'].isin(source_deleted_ids)]
    if len(mappings_df) == 0:
        logging.warning(f'Synonym Sync: No mappings found for source {source_name}. Exiting.')
        return
    # - update source labels (sometimes Mondo & source have discrepancy)
    source_labels: Dict[CURIE, str] = {curie: label for curie, label in source_labels}
    mappings_df['source_label'] = mappings_df['source_id'].map(source_labels)

    # Query synonyms: source
    source_df: pd.DataFrame = _query_synonyms(mappings_df['source_id'].tolist(), source_db)
    # - add mapped mondo ids
    source_mondo_lookup = mappings_df.set_index('source_id')['mondo_id'].to_dict()
    source_df['mondo_id'] = source_df['curie'].map(source_mondo_lookup)
    source_df = source_df.rename(columns={'curie': 'source_id'})[['mondo_id', 'source_id', 'synonym_scope', 'synonym']]

    # Query synonyms: Mondo
    mondo_df = pd.read_csv(mondo_synonyms_path, sep='\t').rename(columns={'?dbXref': 'source_id'})
    mondo_df = mondo_df.rename(columns=lambda x: x.lstrip('?'))
    # - filter by source
    mondo_df['source_prefix'] = mondo_df['source_id'].apply(lambda x: x.split(':')[0])
    mondo_df = mondo_df[mondo_df['source_prefix'].isin(owned_prefix_map.keys())]
    del mondo_df['source_prefix']
    # - filter by source previously filtered mappings_df (obsoletes & deletions)
    mondo_df = mondo_df[mondo_df['mondo_id'].isin(set(mappings_df['mondo_id']))]  # alternative: JOIN-based solution
    # - filter out rows which don't appear in mondo.sssom.tsv for whatever reason
    mondo_df = mondo_df.merge(mappings_df[['mondo_id', 'source_id']], on=['mondo_id', 'source_id'], how='inner')
    # - filter out any non-source-ID, source-specific synonym xrefs
    #   Not future-proof, as this list has to be maintained, but as of 2024/07/15 there is only one entry, so there is
    #   not high risk of this being a problem. Alternative: Come up w/ regex for valid codes for all sources. Will
    #   mostly be numbers, but can include . and -. Not sure if can include alpha chars.
    mondo_df = mondo_df[~mondo_df['source_id'].isin(NON_SOURCE_ID_SOURCE_SPECIFIC_SYNONYM_XREFS)]
    # - add labels
    mondo_df = mondo_df.merge(mappings_df, on=['mondo_id', 'source_id'], how='left')

    # Determine synchronization cases    # -confirmed
    confirmed_df = mondo_df.merge(source_df, on=['mondo_id', 'source_id', 'synonym_scope', 'synonym'], how='inner')
    confirmed_df['case'] = 'confirmed'

    # -updated
    updated_df = mondo_df.merge(source_df, on=['mondo_id',  'source_id', 'synonym',], how='inner').rename(
        columns={'synonym_scope_x': 'synonym_scope_mondo', 'synonym_scope_y': 'synonym_scope'})
    updated_df = updated_df[updated_df['synonym_scope_mondo'] != updated_df['synonym_scope']]
    updated_df = updated_df[[
        'mondo_id', 'mondo_label', 'source_id', 'source_label', 'synonym_scope_mondo', 'synonym_scope', 'synonym',
        'synonym_type']]
    updated_df['case'] = 'updated'

    # -added
    added_df = source_df.merge(
        mondo_df, on=['mondo_id', 'source_id', 'synonym_scope', 'synonym'], how='left', indicator=True)
    added_df = added_df[added_df['_merge'] == 'left_only'].drop(columns=['_merge', 'mondo_label', 'source_label'])
    # - add labels
    for ont in ['mondo', 'source']:
        added_df = added_df.merge(
            mappings_df[[f'{ont}_id', f'{ont}_label']].drop_duplicates(), on=f'{ont}_id', how='left')
    added_df = _filter_non_intersecting_rows(added_df, updated_df, ['mondo_id', 'source_id', 'synonym'])
    del added_df['synonym_type']
    added_df['case'] = 'added'

    # -deleted
    deleted_df = mondo_df.merge(
        source_df, on=['mondo_id', 'source_id', 'synonym_scope', 'synonym'], how='left', indicator=True)
    deleted_df = deleted_df[deleted_df['_merge'] == 'left_only'].drop('_merge', axis=1)  # also can do via mondo_id=nan
    deleted_df = _filter_non_intersecting_rows(deleted_df, updated_df, ['mondo_id', 'source_id', 'synonym'])
    deleted_df['case'] = 'deleted'

    # Write outputs
    # todo: temp: dirty_df: combine all cases for analysis during development
    dirty_df = pd.concat([confirmed_df, added_df, updated_df, deleted_df], ignore_index=True)[[
        'mondo_id', 'mondo_label', 'source_id', 'source_label', 'synonym_scope', 'synonym', 'synonym_type', 'case',
        'synonym_scope_mondo']]\
        .sort_values(by=['case', 'mondo_id', 'source_id', 'synonym_scope', 'synonym_type', 'synonym'])
    dirty_df['source_ontology'] = source_name
    dirty_df = dirty_df.rename(columns={'synonym_scope_mondo': 'synonym_scope_mondo__for_-updated_case'})
    dirty_df.to_csv(f'tmp/synonym_sync_combined_cases_{source_name}.tsv', sep='\t', index=False)


def cli():
    """Command line interface."""
    parser = ArgumentParser(
        prog='sync-synonyms',
        description='Create outputs for syncing synonyms between Mondo and its sources.')
    parser.add_argument(
        '-o', '--ontology-db-path', required=False,
        help='Path to SemanticSQL sqlite `.db` file for the given source ontology.')
    parser.add_argument(
        '-m', '--mondo-synonyms-path', required=False,
        help='Path to a TSV with the columns: ?mondo_id, ?dbXref, ?synonym_scope, ?synonym, synonym_type.')
    parser.add_argument(
        '-s', '--mondo-mappings-path', required=True,
        help='Path to file containing all known Mondo mappings, in SSSOM format.')
    parser.add_argument(
        '-C', '--onto-config-path', required=True,
        help='Path to a config `.yml` for the ontology which contains a `base_prefix_map` which contains a '
             'list of prefixes owned by the ontology. Used to filter out terms.')
    parser.add_argument(
        '-a', '--outpath-added', required=True,
        help='Path to robot template TSV to create which will contain synonyms that aren\'t yet integrated into Mondo '
             'for given ontoogy.')
    parser.add_argument(
        '-c', '--outpath-confirmed', required=True,
        help='Path to robot template TSV to create which will contain synonym confirmations.')
    parser.add_argument(
        '-d', '--outpath-deleted', required=True,
        help='Path to robot template TSV to create which will contain synonym deletions.')
    parser.add_argument(
        '-u', '--outpath-updated', required=True,
        help='Path to robot template TSV to create which will contain synonym metadata changes.')
    sync_synonyms(**vars(parser.parse_args()))


if __name__ == '__main__':
    cli()
