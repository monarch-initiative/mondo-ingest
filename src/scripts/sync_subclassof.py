"""Create outputs for purpose of analyzing and syncing subClassOf relations.

Resources
- GitHub issue: https://github.com/monarch-initiative/mondo-ingest/issues/92
- GitHub PR: https://github.com/monarch-initiative/mondo-ingest/pull/363
- Google doc about cases https://docs.google.com/document/d/1H8fJKiKD-L1tfS-2LJu8t0_2YXJ1PQJ_7Zkoj7Vf7xA/edit#heading=h.9hixairfgxa1

todo's
 1. Simplify: Set[RELATIONSHIP] _source_edges vars: (sub, rdfs:subClassOf, pred) --> (sub, pred) . This whole pipeline
 is only about subclass rels, so including it is redundant.
 2. reports/sync-subClassOf.confirmed.tsv updates
  https://github.com/monarch-initiative/mondo-ingest/pull/363#discussion_r1398505479
  These changes would require this be implemented in Python rather than the current awk-based goal.
  i. Move these (PK) cols to front: subject_mondo_id, object_mondo_id, subject_source_id, object_source_id
  ii. Add: 'source' column
  iii. Sort: source, mondo_subject_id, mondo_object_id
  iv. File name: stem subClassOf -> subclass (to be consistent with the 'confirmed' and 'added' files).
 3. OO: combine intertwined variable types
   It would simplify the code if instead of several steps to convert edges to diff namespace / add metadata, I
 created a subclass of set(), and do those things automatically. This would effectively combine my _source_edges
 (Set[RELATIONSHIP]) and non-_source_edges (List[Dict]), e.g. in_both_direct_source_edges & in_both_direct into a single
 object.
    related to qc#1: was there a reason why _direct cases done using source IDs and _indirect Mondo IDs? I think maybe
 not. I could (a) standardize all to Mondo IDs, or (b) do the OO, then it'll always have both sets of IDs in objs.
 4. case 5: in_mondo_only -> in_direct_mondo_only. rename the param, output name, etc
 5. #remove-temp-defaults remove EX_DEFAULTS, CLI defaults, and run_defaults() when done with development
 6. mondo-ingest-db -> components?: More performant at query time. But would need to make more .db files. So actually
 might be overall less performant.
 7. qc#1: Depending on which is passed into _convert_edge_namespace(), Mondo IDs or source IDs, I'm concerned
 that perhaps because not all IDs are mapped, I'm wondering if my workflow of collecting sets ->
 _convert_edge_namespace() -> _edges_with_metadata_from_plain_edges() contains any errors, causing rels to be
 dropped in a bad way. This probably isn't the case, since if there are no mappings, we actually don't want rows
 with missing sub/obj mappings to appear in the output and are filtering such rows from the df later anyway, but
 I'm still concerned because I feel like I haven't fully thought/walked through this after refactors. - Joe
"""
import logging
import os
import pickle
import sys
from argparse import ArgumentParser
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from time import time
from typing import Dict, Iterable, List, Set, Tuple, Union

import pandas as pd
from oaklib import get_adapter
from oaklib.implementations import SqlImplementation
from oaklib.interfaces.basic_ontology_interface import RELATIONSHIP
from oaklib.interfaces.obograph_interface import GraphTraversalMethod
from oaklib.types import CURIE

HERE = Path(os.path.abspath(os.path.dirname(__file__)))
SRC_DIR = HERE.parent
PROJECT_ROOT = SRC_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))
from src.scripts.sync_subclassof_collate_direct_in_mondo_only import collate_direct_in_mondo_only
from src.scripts.sync_subclassof_config import EX_DEFAULTS, IN_MONDO_ONLY_FILE_STEM, METADATA_DIR, REPORTS_DIR, \
    ROBOT_SUBHEADER, TMP_DIR
from src.scripts.utils import CACHE_DIR, MONDO_PREFIX_MAP, PREFIX_MAP, get_owned_prefix_map


def _edges_with_metadata_from_plain_edges(edges: Set[RELATIONSHIP], ns_data_map: Dict[CURIE, Dict]) -> List[Dict]:
    """From simple (subject, predicate, object) edge tuples, create dictionaries with mondo mappings and labels

    Populates: subject_source_id, subject_mondo_id, subject_mondo_label, object_source_id, object_mondo_id,
    object_mondo_label

    :param edges: A set of edges where all the subject and object IDs are of the same namespace.
    :param ns_data_map: A map of IDs from one namespace to another. Consists of mondo_id, source_id, mondo_label
    todo: something feels messy or off about this, its usage and its construction."""
    if not edges or not ns_data_map:
        return []
    ns_prefix = list(ns_data_map.keys())[0].split(':')[0]
    ns = 'mondo' if ns_prefix == 'MONDO' else 'source'
    ns2 = 'source' if ns_prefix == 'MONDO' else 'mondo'
    edges2 = []
    for e in edges:
        d = {}
        terms = {'subject': e[0], 'object': e[2]}
        for position, _id in terms.items():
            d_i = {f'{position}_{ns}_id': _id, f'{position}_{ns2}_id': None, f'{position}_mondo_label': None}
            try:
                mapping: Dict = ns_data_map[_id]
                d_i[f'{position}_{ns2}_id'] = mapping[f'{ns2}_id']
                d_i[f'{position}_mondo_label'] = mapping['mondo_label']
            except KeyError:
                pass  # the term only exists in source and is not in Mondo yet, so has no Mondo ID/label
            d = d | d_i
        edges2.append(d)
    return edges2


# todo: Unused for current use cases. Remove or save for potential future use cases
def _get_mondo_data_map(
    ss_df_source_dicts: List[Dict], mondo_label_lookup: Dict[CURIE, str], mapped_mondo_ids: List[CURIE]
) -> Dict[CURIE, Dict]:
    """Get map of Mondo IDs to metadata"""
    # We only care about mapped cases
    ids = set(mapped_mondo_ids)
    label_lookup = {k: v for k, v in mondo_label_lookup.items() if k in ids}
    # Get data
    mondo_data_map_within_source: Dict[CURIE, Dict] = {d['mondo_id']: d for d in ss_df_source_dicts}
    mondo_ids_not_in_source = set(label_lookup.keys()).difference(set(mondo_data_map_within_source.keys()))
    mondo_data_map_not_in_source = {x: {
        'mondo_id': x,
        'mondo_label': label_lookup[x],
        'source_id': ''
    } for x in mondo_ids_not_in_source}
    mondo_data_map: Dict[CURIE, Dict] = mondo_data_map_within_source | mondo_data_map_not_in_source
    return mondo_data_map


def _get_direct_scr_rels(
    curies: List[CURIE], db: SqlImplementation, prefix_map: PREFIX_MAP = None, verbose=True
) -> Set[RELATIONSHIP]:
    t0 = datetime.now()
    ontology_name = list(prefix_map.keys())[0] if prefix_map else ''

    rels_raw: List[RELATIONSHIP] = [x for x in db.relationships(
        subjects=curies, predicates=['rdfs:subClassOf'])]
    # - filter out non-source parents
    rels = set([x for x in rels_raw if any([x[2].startswith(y) for y in prefix_map])]) \
        if prefix_map else set(rels_raw)

    t1 = datetime.now()
    if verbose:
        logging.info(f'  - from "{ontology_name}" in {(t1 - t0).seconds} seconds')
    return rels


def _ancestors(
    curies: Iterable[CURIE], db: SqlImplementation, prefix_map: PREFIX_MAP = None, use_cache=False, save_cache=True,
    verbose=True, mondo_24hr_cache=True
) -> Set[RELATIONSHIP]:
    """Get direct & indirect SCRs (SubClass Relationships), AKA ancestors.

    :param prefix_map: If present, filters out ancestors that don't have a matching prefix.
    :param use_cache: Requires prefix_map if you want to have multiple caches."""
    t0 = datetime.now()
    # Cache: read
    ontology_name = list(prefix_map.keys())[0] if prefix_map else ''
    cache_path = os.path.join(CACHE_DIR, f'ancestors_{ontology_name}.pickle')
    if os.path.exists(cache_path) and use_cache:
        ancestors = pickle.load(open(cache_path, 'rb'))
    else:
        # If Mondo, use cache if mondo_24hr_cache=True and cache is indeed <24hrs
        # - either getmtime() for modified or getctime() for created should be sufficient
        if (ontology_name.lower() == 'mondo' and mondo_24hr_cache and
            os.path.exists(cache_path) and ((time() - os.path.getmtime(cache_path)) / (60 * 60) < 24)):
            return pickle.load(open(cache_path, 'rb'))

        # Execute
        # - Gather relationships by term
        ancestor_map: Dict[CURIE, List[CURIE]] = {}
        for term in curies:
            ancestors_i: List[CURIE] = [x for x in db.ancestors(
                start_curies=[term], predicates=['rdfs:subClassOf'], method=GraphTraversalMethod.HOP, reflexive=False)]
            if prefix_map:
                ancestors_i = [x for x in ancestors_i if any([x.startswith(f'{y}:') for y in prefix_map])]
            ancestor_map[term] = ancestors_i
        # - Convert to set of relationship triples
        ancestors: Set[RELATIONSHIP] = set()
        for term, ancestors_i in ancestor_map.items():
            for ancestor in ancestors_i:
                ancestors.add((term, 'rdfs:subClassOf', ancestor))
        # Cache: write
        if save_cache:
            with open(cache_path, 'wb') as f:
                pickle.dump(ancestors, f, protocol=pickle.HIGHEST_PROTOCOL)
    if verbose:
        t1 = datetime.now()
        logging.info(f'  - from "{ontology_name}" in {(t1 - t0).seconds} seconds')
    return ancestors


def _convert_edge_namespace(
    rels: Iterable[RELATIONSHIP], ns_map: Dict[CURIE, Union[CURIE, List[CURIE]]], return_failed_lookups=True
) -> Tuple[Set[RELATIONSHIP], Set[RELATIONSHIP]]:
    """Convert edges of from 1 namespace to a mapped namespace.

    failed_lookups: Each entry in this set can be 1 of 2 cases: (a) the edge exists in one ontology, represented by the
    namespace of IDs in rels & the keys in ns_map, but it does not exist in the mapped otology, represented by the
    namespace of IDs in rels2 & the values in ns_map; it may simply be that there are some terms in the 1st ontology
    that do not exist in the 2nd ontology, or (b) the edges should be in both ontologies, but if the inputs
    to this pipeline are out of sync, the mapped terms did not appear in ns_map.
    """
    rels2: Set[RELATIONSHIP] = set()
    failed_lookups = set()
    for x in rels:
        try:
            # For Source -> Mondo, should only be 1 sub and 1 obj, subs and objs should be strings
            # For Mondo -> Source, subs and objs should be lists of 1+ items
            subs, pred, objs = ns_map[x[0]], x[1], ns_map[x[2]]
            subs: List[CURIE] = [subs] if isinstance(subs, str) else subs
            objs: List[CURIE] = [objs] if isinstance(objs, str) else objs
            for s in subs:
                for o in objs:
                    rels2.add((s, pred, o))
        except KeyError:
            failed_lookups.add(x)

    return rels2, failed_lookups if return_failed_lookups else rels2


def sync_subclassof(
    outpath_added: str = EX_DEFAULTS['outpath_added'], outpath_confirmed: str = EX_DEFAULTS['outpath_confirmed'],
    outpath_added_obsolete: str = EX_DEFAULTS['outpath_added_obsolete'],
    mondo_db_path: str = EX_DEFAULTS['mondo_db_path'], mondo_ingest_db_path: str = EX_DEFAULTS['mondo_ingest_db_path'],
    mondo_mappings_path: str = EX_DEFAULTS['mondo_mappings_path'],
    onto_config_path: str = EX_DEFAULTS['onto_config_path'],
    outpath_direct_in_mondo_only: str = EX_DEFAULTS['outpath_in_mondo_only'], use_cache=False, verbose=True
):
    """Run"""
    source_name = os.path.basename(outpath_added).split('.')[0]
    owned_prefix_map: PREFIX_MAP = get_owned_prefix_map(onto_config_path)
    mondo_db: SqlImplementation = get_adapter(mondo_db_path)
    ingest_db: SqlImplementation = get_adapter(mondo_ingest_db_path)
    ontology_name = list(owned_prefix_map.keys())[0]
    logging.info(f'Running: Synchronization pipeline - subClassOf - {ontology_name}')

    # Source terms and mappings ----------------------------------------------------------------------------------------
    # - ss_df: Dataframe for mondo.sssom.tsv
    # - mondo_source_map: Map of Mondo IDs to 1+ source IDs each
    # - source_mondo_map: Map of source IDs to 1 Mondo ID each
    # - mondo_label_lookup: For looking up Mondo labels
    # - source_data_map: keys=source ids, values(mondo_id (if any), source_id, mondo_label (if any))
    # - mondo_data_map: keys=mondo ids, values=(mondo_id, source_id (if any), mondo_label)
    # - mondo_ids: List of set of Mondo IDs from mondo.sssom.tsv
    # - source_ids: List of set of source IDs from mondo.sssom.tsv
    logging.info('- Collecting all source terms and mondo mappings')
    # - Mondo labels
    mondo_ids_all: List[CURIE] = [
        x for x in [y for y in mondo_db.entities(filter_obsoletes=False)] if x.startswith('MONDO')]
    mondo_label_lookup: Dict[CURIE, str] = {x[0]: x[1] for x in [y for y in mondo_db.labels(mondo_ids_all)]}
    # - Mappings
    ss_df = pd.read_csv(mondo_mappings_path, sep='\t', comment='#')
    #   - filter: Only exact matches
    ss_df = ss_df[ss_df['predicate_id'] == 'skos:exactMatch']
    #   - filter: Only in source
    ss_df['obj_prefix'] = ss_df['object_id'].apply(lambda _id: _id.split(':')[0])
    _col_renames = {'subject_id': 'mondo_id', 'subject_label': 'mondo_label', 'object_id': 'source_id'}
    ss_df_source_dicts: List[Dict] = ss_df[ss_df['obj_prefix'].isin(owned_prefix_map)][
        ['subject_id', 'subject_label', 'object_id']].rename(columns=_col_renames).to_dict(orient='records')
    # - Lookup dictionaries
    #   - mapping lookups
    mondo_source_map: Dict[CURIE, List[CURIE]] = {}
    for d in ss_df_source_dicts:
        mondo_source_map.setdefault(d['mondo_id'], []).append(d['source_id'])
    source_mondo_map: Dict[CURIE, CURIE] = {d['source_id']: d['mondo_id'] for d in ss_df_source_dicts}
    #   - metadata lookups & id lists
    mondo_ids = list(ss_df['subject_id'])
    # todo: mondo_data_map: Unused for current use cases. Remove or save for potential future use cases
    # mondo_data_map: Dict[CURIE, Dict] = _get_mondo_data_map(ss_df_source_dicts, mondo_label_lookup, mondo_ids)
    source_data_map: Dict[CURIE, Dict] = {d['source_id']: d for d in ss_df_source_dicts}
    source_ids: List[CURIE] = list(source_data_map.keys())

    # Get subclass edges: ancestors (direct + indirect)  ---------------------------------------------------------------
    # - ancestors_mondo_mondo: Ancestors (Mondo IDs) from Mondo (direct and indirect)
    # - ancestors_mondo_source: Ancestors (source IDs) from Mondo (direct and indirect)
    # - ancestors_mondo_mondo_and_1or2_ids_not_in_source: Edges from ancestors_mondo_mondo not in source (unused)
    # - ancestors_source_source: Ancestors (source IDs) from source (direct and indirect)
    # - ancestors_source_mondo: Ancestors (Mondo IDs) from source (direct and indirect)
    # - ancestors_source_mondo_and_1or2_ids_not_in_mondo: Edges from ancestors_source_mondo not in Mondo (unused)
    logging.info('- Collecting ancestors (direct + indirect)')
    ancestors_mondo_mondo: Set[RELATIONSHIP] = _ancestors(  # from Mondo
        mondo_ids, mondo_db, MONDO_PREFIX_MAP, use_cache, True, verbose)
    ancestors_mondo_source, ancestors_mondo_mondo_and_1or2_ids_not_in_source = _convert_edge_namespace(
        ancestors_mondo_mondo, mondo_source_map)
    ancestors_source_source: Set[RELATIONSHIP] = _ancestors(  # from source
        source_ids, ingest_db, owned_prefix_map, use_cache, True, verbose)
    ancestors_source_mondo, ancestors_source_mondo_and_1or2_ids_not_in_mondo = _convert_edge_namespace(
        ancestors_source_source, source_mondo_map)

    # Get subclass edges: direct ---------------------------------------------------------------------------------------
    # - rels_direct_source_source: Edges with source IDs; all direct SCRs in source
    # - rels_direct_mondo_mondo: Edges with Mondo IDs that appear in Mondo, derived from all source::Mondo mappings
    # - rels_direct_mondo_source: Edges from rels_direct_mondo_mondo that appear in the source
    # - rels_direct_mondo_mondo_and_1or2_ids_not_in_source: Edges from rels_direct_mondo_mondo not in source (unused)
    logging.info('- Collecting direct subclass relations')
    rels_direct_source_source: Set[RELATIONSHIP] = _get_direct_scr_rels(  # from source
        source_ids, ingest_db, owned_prefix_map)
    
    if not rels_direct_source_source or len(rels_direct_source_source) < 1:
        raise ValueError("Source has no relationships. Something went wrong")
    
    rels_direct_mondo_mondo: Set[RELATIONSHIP] = _get_direct_scr_rels(  # from Mondo
        mondo_ids, mondo_db, MONDO_PREFIX_MAP)
    rels_direct_mondo_source, rels_direct_mondo_mondo_and_1or2_ids_not_in_source = _convert_edge_namespace(
        rels_direct_mondo_mondo, mondo_source_map)

    # Get subclass edges: indirect -------------------------------------------------------------------------------------
    # - rels_indirect_mondo_mondo: Indirect relationships (Mondo IDs) from Mondo
    # - rels_indirect_source_source: Indirect relationships (source IDs) from source
    # - rels_indirect_source_mondo:  Relationships from rels_indirect_source_source that appear in Mondo
    # - rels_indirect_source_mondo_and_1or2_ids_not_in_mondo: from rels_indirect_source_source not in Mondo (unused)
    logging.info('- Collecting indirect subclass relations')
    rels_indirect_mondo_mondo = ancestors_mondo_mondo.difference(rels_direct_mondo_mondo)
    # todo: remove unused, commented out vars?
    # rels_indirect_mondo_source = ''  # not needed?
    # rels_indirect_source_source = ancestors_source_source.difference(rels_direct_source_source)
    # rels_indirect_source_mondo, rels_indirect_source_mondo_and_1or2_ids_not_in_mondo = _convert_edge_namespace(
    #     rels_indirect_source_source, source_mondo_map)
    # - assertions
    # todo: this exception should be in tests/ instead
    #  - I added this check again because even after I fixed it once by rerunning the cache, it popped up again shortly
    #  after. It could be that I invalidated the cache somehow without realizing it. Rerunning cache fixed it though.
    missing_ancestor_rels = rels_indirect_mondo_mondo.union(rels_direct_mondo_mondo).difference(ancestors_mondo_mondo)
    if missing_ancestor_rels:
        raise ValueError(
            'FATAL BUILD ERROR: Ancestors discrepancy\n'
            'Detected error in consistency of sets of terms gathered from Mondo.\n'
            f'\n 1. Mondo SCR ancestors: {len(ancestors_mondo_mondo)}'
            f'\n 2. Mondo direct SCR relationships: {len(rels_direct_mondo_mondo)}'
            f'\n 3. Mondo indirect SCR relationships: {len(rels_indirect_mondo_mondo)}'
            f'\n Intersection (Top 5): {[rel for rel in list(missing_ancestor_rels)[:5]]}'
            f'\n "1" should be same as "2" + "3", but instead it has n less rels: {len(missing_ancestor_rels)}'
            '\nSee also: https://github.com/monarch-initiative/mondo-ingest/issues/525'
            '\n\nExiting.')

    # Determine hierarchy diferences -----------------------------------------------------------------------------------
    # todo: remove unused, commented out vars? (they were created in anticipation of possible cases)
    logging.info('Calculating various differences in hierarchies between source and Mondo')
    # Find which edges appear in both Mondo and source, or only in one or the other
    # - direct <--> direct
    #   - Direct SCRs exist in both Mondo and source
    in_both_direct_source_edges: Set[RELATIONSHIP] = rels_direct_source_source.intersection(rels_direct_mondo_source)
    in_both_direct: List[Dict] = _edges_with_metadata_from_plain_edges(in_both_direct_source_edges, source_data_map)
    #   - Direct SCRs in Mondo which are not direct in source (could be indirect or non-existent)
    # in_mondo_only_direct_source_edges: Set[RELATIONSHIP] = (
    #     rels_direct_mondo_source.difference(rels_direct_source_source))
    # in_mondo_only_direct: List[Dict] = _edges_with_metadata_from_plain_edges(
    #     in_mondo_only_direct_source_edges, source_data_map)
    #   - Direct SCRs in source which are not direct in Mondo (could be indirect or non-existent)
    # in_source_only_direct_source_edges: Set[RELATIONSHIP] = (
    #     rels_direct_source_source.difference(rels_direct_mondo_source))
    # in_source_only_direct: List[Dict] = _edges_with_metadata_from_plain_edges(
    #     in_source_only_direct_source_edges, source_data_map)

    # - indirect <--> indirect
    #   - Indirect SCRs that exist in both Mondo and source
    # in_both_indirect_mondo_edges: Set[RELATIONSHIP] = (
    #     rels_indirect_source_mondo.intersection(rels_indirect_mondo_mondo))
    # in_both_indirect: List[Dict] = _edges_with_metadata_from_plain_edges(in_both_indirect_mondo_edges, mondo_data_map)
    #   - Indirect SCRs that exist in source but not in Mondo
    # in_source_only_indirect_mondo_edges: Set[RELATIONSHIP] = rels_indirect_source_mondo.difference(
    #     rels_indirect_mondo_mondo)
    # in_source_only_indirect: List[Dict] = _edges_with_metadata_from_plain_edges(
    #     in_source_only_indirect_mondo_edges, mondo_data_map)
    #   - Indirect SCRs that exist in Mondo but not in source
    # in_mondo_only_indirect_mondo_edges: Set[RELATIONSHIP] = rels_indirect_mondo_mondo.difference(
    #     rels_indirect_source_mondo)
    # in_mondo_only_indirect: List[Dict] = _edges_with_metadata_from_plain_edges(
    #     in_mondo_only_indirect_mondo_edges, mondo_data_map)

    # - direct <--> ancestor
    #   - Direct SCRs in source that don't exist at all in Mondo
    in_source_direct_not_in_mondo_source_edges = rels_direct_source_source.difference(ancestors_mondo_source)
    in_source_direct_not_in_mondo: List[Dict] = _edges_with_metadata_from_plain_edges(
        in_source_direct_not_in_mondo_source_edges, source_data_map)
    #   - Direct SCRs in Mondo that don't exist at all in source
    in_mondo_direct_not_in_source_mondo_edges: Set[RELATIONSHIP] = (
        rels_direct_mondo_mondo.difference(ancestors_source_mondo))
    # in_mondo_direct_not_in_source: List[Dict] = _edges_with_metadata_from_plain_edges(
    #     in_mondo_direct_not_in_source_mondo_edges, mondo_data_map)

    # Create outputs ---------------------------------------------------------------------------------------------------
    # Google doc about cases:
    # https://docs.google.com/document/d/1H8fJKiKD-L1tfS-2LJu8t0_2YXJ1PQJ_7Zkoj7Vf7xA/edit#heading=h.9hixairfgxa1
    logging.info('Creating outputs for synchronization cases')
    common_sort_cols = ['subject_mondo_id', 'object_mondo_id', 'subject_source_id', 'object_source_id']

    # Case 1: SCR direct in source and Mondo
    subheader = deepcopy(ROBOT_SUBHEADER)
    subheader[0]['object_mondo_id'] = 'SC %'
    df1 = pd.DataFrame(in_both_direct)
    if len(df1) == 0:
        df1 = pd.DataFrame(columns=list(subheader[0].keys()))
    df1 = df1.sort_values(common_sort_cols)
    df1 = pd.concat([pd.DataFrame(subheader), df1])
    df1.to_csv(outpath_confirmed, sep='\t', index=False)

    # Case 2: SCR is direct in source, but indirect Mondo
    pass  # no output for this case

    # Case 3: SCR is direct in the source, but not at all in Mondo
    subheader = deepcopy(ROBOT_SUBHEADER)
    subheader[0]['object_mondo_id'] = 'AI obo:mondo#excluded_subClassOf'
    df3 = pd.DataFrame(in_source_direct_not_in_mondo)
    if len(df3) == 0:
        df3 = pd.DataFrame(columns=list(subheader[0].keys()))
    # - warning cases
    #   is.na() checks: only object_mondo_id should ever be missing, but checking both to be safe
    unmigrated_terms = set(df3[df3['object_mondo_id'].isna()]['object_source_id']).union(
        set(df3[df3['subject_mondo_id'].isna()]['object_source_id']))
    if len(unmigrated_terms) >= 200:
        logging.warning(f'Warning: {len(unmigrated_terms)} unmigrated source terms found in "{ontology_name}"; '
                        f'higher number than expected.')
    # - format
    #   only object_mondo_id should ever be missing, but checking both to be safe
    df3 = df3[~df3['subject_mondo_id'].isna() & ~df3['object_mondo_id'].isna()].sort_values(common_sort_cols)
    # - obsolete cases
    obsoletes = (df3['subject_mondo_label'].str.startswith('obsolete') |
                 df3['object_mondo_label'].str.startswith('obsolete'))
    df3_obs = df3[obsoletes].sort_values(common_sort_cols)
    # - non-obsolete cases
    df3 = df3[~obsoletes].sort_values(common_sort_cols)
    # - save
    df3_obs = pd.concat([pd.DataFrame(subheader), df3_obs])
    df3_obs.to_csv(outpath_added_obsolete, sep='\t', index=False)
    df3 = pd.concat([pd.DataFrame(subheader), df3])
    df3.to_csv(outpath_added, sep='\t', index=False)

    # Case 5: SCR is direct in Mondo, and not in the source at all
    rels_mondo_raw_all: List[RELATIONSHIP] = [x for x in mondo_db.relationships(
        subjects=list(set(ss_df['subject_id'])), predicates=['rdfs:subClassOf'])]
    rels_mondo_mondo_all = set(  # filter non-source parents
        [x for x in rels_mondo_raw_all if any([x[2].startswith(y) for y in MONDO_PREFIX_MAP.keys()])])
    df5 = pd.DataFrame([{'subject_id': x[0], 'object_id': x[2]} for x in rels_mondo_mondo_all])
    for pos in ['subject', 'object']:
        df5[f'{pos}_label'] = df5[f'{pos}_id'].apply(lambda _id: mondo_label_lookup.get(_id, None))
    src_field = f'in_{source_name}'
    df5[src_field] = df5.apply(
        lambda row:
        # UNSUPPORTED-MISSING: either or both Mondo IDs not mapped to a source
        'UNSUPPORTED-MISSING' if any(x not in mondo_source_map for x in [row['subject_id'], row['object_id']])
        # Supported / Unsupported: Whether edge has a direct or indirect SCR in source
        else 'UNSUPPORTED-SUBCLASS'
        if (row['subject_id'], 'rdfs:subClassOf', row['object_id']) in in_mondo_direct_not_in_source_mondo_edges
        else 'SUPPORTED',
        axis=1)
    df5 = df5.sort_values([src_field, 'subject_id', 'object_id'])
    df5.to_csv(outpath_direct_in_mondo_only, sep='\t', index=False)

    # Close out
    logging.info(f'Completed - Synchronization pipeline: subClassOf - {ontology_name}')


def cli():  # todo: #remove-temp-defaults
    """Command line interface."""
    parser = ArgumentParser(
        prog='sync-subclassof',
        description='Create outputs for purpose of analyzing and syncing subClassOf relations.')
    # Normal command line arguments
    parser.add_argument(
        '-a', '--outpath-added', required=False, default=EX_DEFAULTS['outpath_added'],
        help='Path to output robot template containing new subclass relationships from given ontology '
             'to be imported into Mondo.')
    parser.add_argument(
        '-O', '--outpath-added-obsolete', required=False, default=EX_DEFAULTS['outpath_added_obsolete'],
        help='Creates robot template containing new subclass relationships from given ontology that would be imported '
             'into Mondo, except for that these terms are obsolete in Mondo.')
    parser.add_argument(
        '-c', '--outpath-confirmed', required=False, default=EX_DEFAULTS['outpath_confirmed'],
        help='Path to output robot template containing subclass relations for given ontology that exist in Mondo and '
             'are confirmed to also exist in the source.')
    parser.add_argument(
        '-M', '--outpath-direct-in-mondo-only', required=False,
        default=EX_DEFAULTS['outpath_in_mondo_only'],
        help='Path to create file for relations for given ontology where direct subclass relation exists only in Mondo'
             ' and not in the source.')
    parser.add_argument(
        '-o', '--onto-config-path', required=False, default=EX_DEFAULTS['onto_config_path'],
        help='Path to a config `.yml` for the ontology which contains a `base_prefix_map` which contains a '
             'list of prefixes owned by the ontology. Used to filter out terms.')
    parser.add_argument(
        '-d', '--mondo-ingest-db-path', required=False, default=EX_DEFAULTS['mondo_ingest_db_path'],
        help='Path to SemanticSQL sqlite  `mondo-ingest.db`.')
    parser.add_argument(
        '-D', '--mondo-db-path', required=False, default=EX_DEFAULTS['mondo_db_path'],
        help='Path to SemanticSQL sqlite `mondo.db`.')
    parser.add_argument(
        '-m', '--mondo-mappings-path', required=False, default=EX_DEFAULTS['mondo_mappings_path'],
        help='Path to file containing all known Mondo mappings, in SSSOM format.')
    parser.add_argument(
        '-u', '--use-cache', required=False, default=EX_DEFAULTS['use_cache'],
        help='Use cached outputs, if any present, for outputs from operations that fetch ancestors. Cache will always'
             ' be saved even if this flag is not present, but it will not be loaded from unless flag is present.')

    d: Dict = vars(parser.parse_args())
    sync_subclassof(**d)


def run_defaults(use_cache=True):  # todo: #remove-temp-defaults
    """Run with default settings"""
    ontologies = ['ordo', 'doid', 'icd10cm', 'icd10who', 'omim', 'ncit']
    for name in ontologies:
        sync_subclassof(**{
            'outpath_added': str(REPORTS_DIR / f'{name}.subclass.added.robot.tsv'),
            'outpath_confirmed': str(REPORTS_DIR / f'{name}.subclass.confirmed.robot.tsv'),
            'onto_config_path': str(METADATA_DIR / f'{name}.yml'),
            'mondo_db_path': str(TMP_DIR / 'mondo.db'),
            'mondo_ingest_db_path': str(TMP_DIR / 'mondo-ingest.db'),
            'mondo_mappings_path': str(TMP_DIR / 'mondo.sssom.tsv'),
            'outpath_direct_in_mondo_only': str(REPORTS_DIR / f'{name}{IN_MONDO_ONLY_FILE_STEM}'),
            'use_cache': use_cache
        })
    collate_direct_in_mondo_only()


if __name__ == '__main__':
    cli()
    #run_defaults()  # todo: #remove-temp-defaults
