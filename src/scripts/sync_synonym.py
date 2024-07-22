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


# todo: when dirty_df no longer necessary, remove 'case' from these
HEADERS_TO_ROBOT_SUBHEADERS = {
    'mondo_id': 'ID',
    'mondo_label': '',
    'synonym_scope': 'AI',  # todo next impt: pred  - 'A' correct? AI?
    'synonym': '',  # todo: obj of 'scope' ow?
    'source_id': '>A oboInOwl:source',  # todo axiom  # todo question: This is how we annotate source CURIEs. but isn't a CURIE similar to an IRI, so why isn't it 'AI' insead of just 'A'?
    'source_label': '',
    'synonym_type': '',
    'mondo_evidence': '',
    'case': '',
    'synonym_scope_mondo': '',
}
SORT_COLS = ['case', 'mondo_id', 'source_id', 'synonym_scope', 'synonym_type', 'synonym']


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


def _format_and_save(
    df: pd.DataFrame, outpath: Union[Path, str], order_cols: List[str] = list(HEADERS_TO_ROBOT_SUBHEADERS.keys()),
        sort_cols: List[str] = SORT_COLS,
    save=True
) -> pd.DataFrame:
    """Format column order and sorting, drop any superfluous columns, and optionally save to file."""
    order_cols = [x for x in order_cols if x in df.columns]
    sort_cols = [x for x in sort_cols if x in df.columns]
    df = df[order_cols].sort_values(by=sort_cols)
    if save:
        df.to_csv(outpath, sep='\t', index=False)
    return df


def _filter_a_by_not_in_b(
        df_a: pd.DataFrame, df_b: pd.DataFrame, join_on: List[str]
) -> pd.DataFrame:
    """Filter out all rows not in common, given a `join_on`.

    Example use case: -added
    - df_a: Dataframe of synonym data from a source
    - df_b: Dataframe of synonym data from a source
    - join_on: ['mondo_id', 'synonym'] - we want to find ones that are in source but not in Mondo

    Alternative implementation yielding exact same results:
        merge_df = base_df.merge(to_intersect_df, on=join_on, how='left', indicator=True)
        filtered_df = merge_df[merge_df['_merge'] == 'left_only'].drop(columns=['_merge'])
        return filtered_df.rename(
            columns=lambda x: x[:-2] if x.endswith('_x') else x)[list(base_df.columns)]
    """
    return df_a[~df_a[join_on].apply(tuple, axis=1).isin(
        df_b[join_on].apply(tuple, axis=1)
    )]


def sync_synonyms(
    ontology_db_path: Union[Path, str], mondo_synonyms_path: Union[Path, str], mondo_mappings_path: Union[Path, str],
    onto_config_path: Union[Path, str], outpath_added: Union[Path, str], outpath_confirmed: Union[Path, str],
    outpath_deleted: Union[Path, str], outpath_updated: Union[Path, str], deactivate_deleted=True,
    combined_outpath_template_str = 'tmp/synonym_sync_combined_cases_{}.tsv'
):
    """Create outputs for syncing synonyms between Mondo and its sources.

    :param deactivate_deleted: If True, will not create the '-deleted' template.

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
    mappings_df = mappings_df[['mondo_id', 'mondo_label', 'source_id']]  # source_label added later from source

    # - filter by source
    # todo: filtering by prefixes / source
    # Todo: i. keep or remove?
    #   the role of source_id in -confirmed and -updated is different than what I originally thought. Do I still need to
    #   filter here? I think so. Originally our pseudocode was an iterator over only these matches, I thought
    # todo: ii. if keep: refactor
    #  check this pattern used elsewhere; I think it has. and abstract into func for these 3 lines; 'filter prefixes'
    #  - OR use this?: get_all_owned_terms()
    #    - it seems long and messy compared to these 3 lines, but is more comprehensive. I could make
    #      get_all_owned_terms() a simple 3 line func and then make a separate func for all edge cases?
    #  - note I may have list(owned_prefix_map.keys())[0] instead of list(owned_prefix_map)[0] ins ome places
    mappings_df['source_prefix'] = mappings_df['source_id'].apply(lambda x: x.split(':')[0])
    mappings_df = mappings_df[mappings_df['source_prefix'].isin(owned_prefix_map.keys())]
    del mappings_df['source_prefix']

    # - filter obsoletes (from mappings_df --> source_df & mondo_df)
    #  - filter obsoleted in Mondo
    mappings_df = mappings_df[~mappings_df['mondo_label'].str.startswith('obsolete')]
    # Todo: obsoletes/deleted filtering correct?
    #  I feel like this way might be wrong. this is probably too early / not the correct place to be filtering
    #  - filter obsoleted in source
    source_obsoletes: Set[CURIE] = set([x for x in source_db.obsoletes()])
    mappings_df = mappings_df[~mappings_df['source_id'].isin(source_obsoletes)]
    # - labels / label lookups
    # todo: I'd like to move these labels somewhere different for better flow, but requires refactor
    source_labels: List[Tuple[CURIE, str]] = [x for x in source_db.labels(mappings_df['source_id'].tolist())]
    source_labels: Dict[CURIE, str] = {curie: label for curie, label in source_labels}
    mappings_df['source_label'] = mappings_df['source_id'].map(source_labels)
    mondo_labels: Dict[CURIE, str] = mappings_df.set_index('mondo_id')['mondo_label'].to_dict()
    # - filter mapped but deleted IDs
    #   If there is no label, we take that as a proxy / sign that it has been deleted. Alternative ways: entities(),
    #   all_entity_curies(), node() (empty props), node_exists() (no: falsely says 'True', prolly cuz bad xrefs exist)
    source_deleted_ids: Set[CURIE] = set([k for k, v in source_labels.items() if not v])
    mappings_df = mappings_df[~mappings_df['source_id'].isin(source_deleted_ids)]
    if len(mappings_df) == 0:
        logging.warning(f'Synonym Sync: No mappings found for source {source_name}. Exiting.')
        return

    # Query synonyms: source
    source_df: pd.DataFrame = _query_synonyms(mappings_df['source_id'].tolist(), source_db)\
        .rename(columns={'curie': 'source_id'})
    source_df['synonym_lower'] = source_df['synonym'].str.lower()
    source_df['source_label'] = source_df['source_id'].map(source_labels)

    # Query synonyms: Mondo
    mondo_df = pd.read_csv(mondo_synonyms_path, sep='\t').rename(columns={'?dbXref': 'source_id'}).fillna('')
    mondo_df['source_id'] = mondo_df['source_id'].apply(lambda x: x.replace('https://orcid.org/', 'ORCID:'))
    mondo_df['synonym_lower'] = mondo_df['synonym'].str.lower()
    # - URI -> CURIEs
    # todo: utilize curies package; handle more cases
    mondo_df['source_id'] = mondo_df['source_id'].apply(lambda x: x.split('/')[-1] if x else '')
    # - add evidence column
    mondo_evidence_lookup: Dict[Tuple, List[str]] = mondo_df.groupby(
        ['mondo_id', 'synonym_scope', 'synonym'])['source_id'].agg(list).to_dict()
    mondo_evidence_lookup: Dict[Tuple, str] = {k: ', '.join(v) for k, v in mondo_evidence_lookup.items()}
    mondo_evidence_rows: List[List[str]] = []
    for k, v in mondo_evidence_lookup.items():
        mondo_evidence_rows.append(list(k) + [v])
    mondo_evidence_df = pd.DataFrame(
        mondo_evidence_rows, columns=['mondo_id', 'synonym_scope', 'synonym', 'mondo_evidence'])
    mondo_df = mondo_df.merge(mondo_evidence_df, on=['mondo_id', 'synonym_scope', 'synonym'], how='left')
    # - only need 1 row per unique combo of ['mondo_id', 'synonym_scope', 'synonym']
    del mondo_df['source_id']
    mondo_df.drop_duplicates(inplace=True)
    # - filter terms not in mondo.sssom.tsv
    #   - also effectively filters by source previously filtered mappings_df (obsoletes & deletions)
    mondo_df = mondo_df[mondo_df['mondo_id'].isin(set(mappings_df['mondo_id']))]
    # - add labels
    mondo_df['mondo_label'] = mondo_df['mondo_id'].map(mondo_labels)

    # Determine synchronization cases
    # -confirmed
    #  Cases where scope + synonym string are the same
    confirmed_df = mondo_df.merge(source_df, on=['synonym_scope', 'synonym_lower'], how='inner').rename(columns={
        'synonym_x': 'synonym', 'synonym_y': 'synonym_source'})  # keep Mondo casing if different
    del confirmed_df['mondo_evidence']
    confirmed_df = _format_and_save(confirmed_df, outpath_confirmed)
    confirmed_df['case'] = 'confirmed'

    # -updated
    #  Cases where scope has is different in source
    updated_df = mondo_df.merge(source_df, on=['synonym_lower'], how='inner').rename(columns={
        'synonym_scope_x': 'synonym_scope_mondo', 'synonym_scope_y': 'synonym_scope',
        'synonym_x': 'synonym', 'synonym_y': 'synonym_source'})  # keep Mondo casing if different
    updated_df = updated_df[updated_df['synonym_scope_mondo'] != updated_df['synonym_scope']]
    updated_df = _format_and_save(updated_df, outpath_updated)
    updated_df['case'] = 'updated'

    # -added
    #  Cases where synonym exists in source term but not in mapped Mondo term
    # - add mapped mondo IDs
    source_df_with_mondo_ids = source_df.merge(mappings_df[['source_id', 'mondo_id', 'mondo_label']], on=['source_id'], how='inner')
    # - leave only synonyms that don't exist on given Mondo IDs
    added_df = _filter_a_by_not_in_b(source_df_with_mondo_ids, mondo_df, ['mondo_id', 'synonym_lower'])
    added_df = _format_and_save(added_df, outpath_added)
    added_df['case'] = 'added'

    # -deleted
    #  Cases where synonym exists in Mondo term, but not in mapped source term
    deleted_df = pd.DataFrame()
    # todo: reactivate when ready.
    #  - depends on more than just 1 source not having synonym. it must (i) exist on no mapped source terms, and (ii) have
    #  no other qualifying evidence (I think just: ORCID & MONDO;notVerified),
    #  - considerations: what role source_id plays in this logic. this may be outdated
    #  - ensure has labels
    # todo: do 100% of mondo and source terms in here have labels? I think they should.
    if not deactivate_deleted:
        # todo: i think this implementation is outdated post source_id refactor
        deleted_df = mondo_df.merge(
            source_df, on=['synonym_scope', 'synonym_lower'], how='left', indicator=True)
        deleted_df = deleted_df[deleted_df['_merge'] == 'left_only'].drop('_merge', axis=1)  # also can do via mondo_id=nan
        deleted_df = _filter_a_by_not_in_b(deleted_df, updated_df, ['mondo_id', 'source_id', 'synonym_lower'])
        deleted_df = _format_and_save(deleted_df, outpath_deleted)
        deleted_df['case'] = 'deleted'

    # Write outputs
    # todo: temp: dirty_df: combine all cases for analysis during development
    if combined_outpath_template_str:
        dirty_df = pd.concat([confirmed_df, added_df, updated_df, deleted_df], ignore_index=True)
        dirty_outpath = str(combined_outpath_template_str).format(source_name)
        dirty_df = _format_and_save(dirty_df, dirty_outpath)
        dirty_df['source_ontology'] = source_name
        dirty_df.to_csv(dirty_outpath, sep='\t', index=False)


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
        help='Path to ROBOT template TSV to create which will contain synonyms that aren\'t yet integrated into Mondo '
             ' for all mapped source terms.')
    parser.add_argument(
        '-c', '--outpath-confirmed', required=True,
        help='Path to ROBOT template TSV to create which will contain synonym confirmations; combination of synonym '
             'scope predicate and synonym string exists in both source and Mondo for a given mapping.')
    parser.add_argument(
        '-d', '--outpath-deleted', required=True,
        help='Path to ROBOT template TSV to create which will contain synonym deletions; exists in Mondo but not '
             'in source(s) for a given mapping.')
    parser.add_argument(
        '-u', '--outpath-updated', required=True,
        help='Path to ROBOT template TSV to create which will contain updates to synonym scope predicate; cases where '
             'the synonym exists in Mondo and on the mapped source term, but the scope predicate is different.')
    sync_synonyms(**vars(parser.parse_args()))


if __name__ == '__main__':
    cli()
