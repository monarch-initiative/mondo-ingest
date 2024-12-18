"""Create outputs for syncing synonyms between Mondo and its sources."""
import logging
import os
import re
import sys
from argparse import ArgumentParser
from pathlib import Path
from typing import Union, List, Tuple, Set, Dict, Any

import curies
import pandas as pd
import yaml
from oaklib import get_adapter
from oaklib.implementations import SqlImplementation
from oaklib.types import CURIE, PRED_CURIE, URI

HERE = Path(os.path.abspath(os.path.dirname(__file__)))
SRC_DIR = HERE.parent
PROJECT_ROOT = SRC_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))
from src.scripts.utils import PREFIX_MAP, get_owned_prefix_map


HEADERS_TO_ROBOT_SUBHEADERS = {
    'mondo_id': 'ID',
    'mondo_label': '',
    'synonym_scope_source': '',
    'synonym_scope_mondo': '',
    'synonym': '',
    'synonym_case_diff_mondo': '',
    'synonym_case_diff_source': '',
    'source_id': '',
    'source_label': '',
    'synonym_type': '',
    'synonym_type_mondo': '',
    'mondo_evidence': '',
    'case': '',
    'exact_synonym': 'A oboInOwl:hasExactSynonym',
    'exact_source_id': '>A oboInOwl:hasDbXref',
    'exact_synonym_type': '>AI oboInOwl:hasSynonymType SPLIT=|',
    'broad_synonym': 'A oboInOwl:hasBroadSynonym',
    'broad_source_id': '>A oboInOwl:hasDbXref',
    'broad_synonym_type': '>AI oboInOwl:hasSynonymType SPLIT=|',
    'narrow_synonym': 'A oboInOwl:hasNarrowSynonym',
    'narrow_source_id': '>A oboInOwl:hasDbXref',
    'narrow_synonym_type': '>AI oboInOwl:hasSynonymType SPLIT=|',
    'related_synonym': 'A oboInOwl:hasRelatedSynonym',
    'related_source_id': '>A oboInOwl:hasDbXref',
    'related_synonym_type': '>AI oboInOwl:hasSynonymType SPLIT=|',
}
SORT_COLS = ['case', 'mondo_id', 'source_id', 'synonym_scope_source', 'synonym_type', 'synonym_type_mondo', 'synonym']
MONDO_ABBREV_URI = 'http://purl.obolibrary.org/obo/mondo#ABBREVIATION'


def _query_synonyms(ids: List[CURIE], db: SqlImplementation) -> pd.DataFrame:
    """Get synonym triples from sqlite DB

    # todo: this could be refactored to SPARQL instead, though we are considering refactoring all SPARQL to OAK.
    """
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


def _add_synonym_type_inferences(row: pd.Series, exclusions: Set[str]) -> str:
    """Append additional synonym_type(s) based on logical rules."""
    syn: str = row['synonym']
    syn_type_str: str = row['synonym_type']
    types: Set[URI] = set(syn_type_str.split('|') if syn_type_str else [])

    # Acronym: uppercase, no numbers, no whitespace, <10 chars
    if syn not in exclusions and syn.isupper() and not any(char.isspace() for char in syn) and len(syn) < 10:
        types.add(MONDO_ABBREV_URI)

    return '|'.join(types)


def _add_syn_variation_cols(df: pd.DataFrame) -> pd.DataFrame:
    """Set 'synonym' col, and add cols showing capitalization differences in between Mondo and source."""
    df['synonym'] = df['synonym_case_mondo']
    df['synonym_case_diff_mondo'] = df.apply(lambda row:
        row['synonym_case_mondo'] if row['synonym_case_mondo'] != row['synonym_case_source'] else '', axis=1)
    df['synonym_case_diff_source'] = df.apply(lambda row:
        row['synonym_case_source'] if row['synonym_case_source'] != row['synonym_case_mondo'] else '', axis=1)
    return df


def _curies_to_uris_from_delim_str(uris_or_curies_str: str, delim='|') -> str:
    """From a delimited string of IRIs of which some may be CURIEs, standardize anticipated cases to URIs.

    todo: Ideally prefix map flexible enough to handle Mondo & source(s). But currently all from source are anticipated
     to be URIs already, so this is a low priority.
    """
    if not uris_or_curies_str:
        return uris_or_curies_str
    epm = [{
        "prefix": "MONDO",
        "prefix_synonyms": ["mondo"],
        "uri_prefix": "http://purl.obolibrary.org/obo/mondo#",
    }]
    conv = curies.Converter.from_extended_prefix_map(epm)
    uris_or_curies: List[str] = uris_or_curies_str.split(delim)
    uris: List[URI] = [conv.expand(x, passthrough=True) for x in uris_or_curies]
    return '|'.join(uris)


def _common_operations(
    df: pd.DataFrame, outpath: Union[Path, str], order_cols: List[str] = list(HEADERS_TO_ROBOT_SUBHEADERS.keys()),
    sort_cols: List[str] = SORT_COLS, mondo_exclusions_df=pd.DataFrame(), save=True, df_is_combined=False
) -> pd.DataFrame:
    """Merges synonym types, filters exclusions, does some formatting, and optionally saves.

    Formatting: Add columns, format column order and sorting, drop any superfluous columns.

    :param: df_is_combined: At the end, we combine all cases into a single file. But for this combined case, we want to
     skip certain operations.

    todo: consider refactor: things that might be able to be done after building mondo_df and source_df but before cases
     1. pretty sure: merging of synonym_type & synonym_type_mondo
     2. maybe: filtering exclusions
    """
    # Filter exclusions
    if len(mondo_exclusions_df) > 0:
        df = _filter_a_by_not_in_b(df, mondo_exclusions_df, ['mondo_id', 'synonym_scope', 'synonym_lower'])

    # Format
    if not df_is_combined:
        # - Acronyms: Use source case
        #   This operation prevents capitalization from being lost, as sometimes Mondo has used lowercase.
        df['synonym'] = df.apply(lambda row:
            row['synonym_case_source'] if MONDO_ABBREV_URI in row['synonym_type'] else row['synonym'], axis=1)
        # - Add ROBOT columns for each synonym scope
        synonym_scopes = ['exact', 'broad', 'narrow', 'related']
        for scope in synonym_scopes:
            preds = [f'oboInOwl:has{scope.capitalize()}Synonym', f'oio:has{scope.capitalize()}Synonym']
            for col in ['synonym', 'source_id', 'synonym_type']:
                df[scope + '_' + col] = df.apply(
                    lambda row: row[col] if row['synonym_scope'] in preds else '', axis=1)
        # - Renames
        df = df.rename(columns={'synonym_scope': 'synonym_scope_source'})
    # - Order & sorting
    order_cols = [x for x in order_cols if x in df.columns]
    sort_cols = [x for x in sort_cols if x in df.columns]
    df = df[order_cols].sort_values(by=sort_cols)

    # Save & return
    if save:
        df2 = pd.concat([pd.DataFrame([HEADERS_TO_ROBOT_SUBHEADERS]), df])
        df2.to_csv(outpath, sep='\t', index=False)
    return df


def _read_sparql_output_tsv(path: Union[Path, str]) -> pd.DataFrame:
    """Read and format special kind of TSV that comes from SPARQL query output.

    todo: Could all .drop_duplicates() calls be done here instead?
    """
    return pd.read_csv(path, sep='\t').fillna('').rename(columns=lambda x: x.lstrip('?'))


def _remove_language_code(text: str, pattern=r'@([a-zA-Z]{2,3}(?:-[a-zA-Z-]+)?)$') -> str:
    """Remove language code from the end of string.

    pattern: Default will capture either of these cases, (1) String ends with @ followed by 2-3 characters,
     (2)  String ends with @ followed by 2-3 characters, followed by a -, followed by an number of characters.
     Complies with RDF & OWL's language tag formatting based on IETF's BCP 47 (Best Current Practice 47) standard.
    """
    match = re.search(pattern, text)
    return text[:match.start()] if match else text


def _filter_a_by_not_in_b(
        df_a: pd.DataFrame, df_b: pd.DataFrame, join_on: List[str]
) -> pd.DataFrame:
    """Filter out all rows not in common, given a `join_on`.

    Example use case: -added
    - df_a: Dataframe of synonym data from a source
    - df_b: Dataframe of synonym data from a source
    - join_on: columns to consider for determining row equivalence, e.g. ['mondo_id', 'synonym'] if we want to find
      synonyms in source but not in Mondo, assuming both data frames have mondo_id.

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
    ontology_db_path: Union[Path, str], mondo_synonyms_path: Union[Path, str],
    mondo_exclusion_configs: Union[Path, str], onto_synonym_types_path: Union[Path, str],
    mondo_mappings_path: Union[Path, str], onto_config_path: Union[Path, str], outpath_added: Union[Path, str],
    outpath_confirmed: Union[Path, str], outpath_updated: Union[Path, str],
    outpath_combined: Union[Path, str], outpath_deleted: Union[Path, str] = None,
):
    """Create outputs for syncing synonyms between Mondo and its sources.

    todo: update when -deleted is reactivated
    :param outpath_deleted: Optional. This case isn't fully fleshed out yet.

    todo: possible refactor: labels: Maybe could be done more cleanly and consistently. At first, wanted to add to both
     source_df and mondo_df, but this caused _x and _y cols during joins, or I would have to join on those cols as well.
     So I arbitrarily chose mondo_df. This is fine in all cases but -added, where they're added in a custom way.
    """
    # Read configurations
    with open(mondo_exclusion_configs, 'r') as stream:
        mondo_exclusion_configs: Dict[str, Any] = yaml.safe_load(stream)['exclusions']
    # Get basic info for source
    owned_prefix_map: PREFIX_MAP = get_owned_prefix_map(onto_config_path)
    conv = curies.Converter.from_prefix_map(owned_prefix_map)
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
    mappings_df['source_prefix'] = mappings_df['source_id'].apply(lambda x: x.split(':')[0])
    mappings_df = mappings_df[mappings_df['source_prefix'].isin(owned_prefix_map.keys())]
    del mappings_df['source_prefix']

    # - filter obsoletes (from mappings_df --> source_df & mondo_df)
    #  - filter obsoleted in Mondo
    mappings_df = mappings_df[~mappings_df['mondo_label'].str.startswith('obsolete')]

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
    mapping_pairs_set = set(mappings_df[['mondo_id', 'source_id']].apply(tuple, axis=1))
    if len(mappings_df) == 0:
        logging.warning(f'Synonym Sync: No mappings found for source {source_name}. Exiting.')
        return

    # Fetch excluded synonyms
    mondo_exclusions_df = pd.DataFrame(mondo_exclusion_configs['synonyms']).rename(columns={
        'id': 'mondo_id', 'scope': 'synonym_scope', 'value': 'synonym'})
    mondo_exclusions_df['synonym_lower'] = mondo_exclusions_df['synonym'].str.lower()

    # Query synonyms: source
    source_df: pd.DataFrame = _query_synonyms(mappings_df['source_id'].tolist(), source_db)\
        .rename(columns={'curie': 'source_id'})
    source_df['synonym_lower'] = source_df['synonym'].str.lower()
    source_df['source_label'] = source_df['source_id'].map(source_labels)
    source_df.drop_duplicates(inplace=True)
    # - get synonym_types: declared by the source
    source_types_df: pd.DataFrame = _read_sparql_output_tsv(
        onto_synonym_types_path).rename(columns={'cls_id': 'source_id'})
    # -- remove synonym xref provenance
    # todo?: keep? it may be useful in the future to keep/use this data
    del source_types_df['dbXref']  # leaves: source_id, synonym_scope, synonym, synonym_type
    # -- URIs --> CURIEs
    source_types_df['source_id'] = source_types_df['source_id'].apply(lambda x: conv.compress(x))
    # -- filter non-source-owned terms (i.e. imported from other ontologies, e.g. ChEBI)
    source_types_df = source_types_df[~source_types_df['source_id'].isna()]
    # -- CURIEs --> URIs
    source_types_df['synonym_type'] = source_types_df['synonym_type'].apply(_curies_to_uris_from_delim_str)
    uri_prefixes: Set[str] = set([x.split(':')[0] for x in source_types_df['synonym_type']]).difference({'', 'http'})
    if uri_prefixes:
        raise RuntimeError('Error: CURIE(s) detected in URI-typed field "synonym_type": ' + ', '.join(uri_prefixes))
    # -- remove language codes
    source_types_df['synonym'] = source_types_df['synonym'].apply(_remove_language_code)
    source_types_df.drop_duplicates(inplace=True)
    # -- filter out rows with no types; can cause duplicate rows (other rows were probably from xref axioms)
    source_types_df = source_types_df[source_types_df['synonym_type'] != '']
    # -- property conversions
    source_types_df['synonym_type'] = source_types_df['synonym_type'].apply(lambda x: x.replace(
        'http://purl.obolibrary.org/obo/OMO_0003012', MONDO_ABBREV_URI))
    # -- merge in synonym types
    source_df = source_df.merge(source_types_df, on=['source_id', 'synonym_scope', 'synonym'], how='left').fillna('')
    # - get synonym_types: inferred
    abbrev_exclusions: Set[str] = set(mondo_exclusion_configs['synonym-type-abbreviation'])
    source_df['synonym_type'] = source_df.apply(
        lambda row: _add_synonym_type_inferences(row, abbrev_exclusions), axis=1)

    # Query synonyms: Mondo
    mondo_df: pd.DataFrame = _read_sparql_output_tsv(mondo_synonyms_path)\
        .rename(columns={'cls_id': 'mondo_id', 'synonym_type': 'synonym_type_mondo', 'dbXref': 'source_id'})
    mondo_df['synonym_lower'] = mondo_df['synonym'].str.lower()
    # todo: utilize curies package; handle more cases
    # - URIs --> CURIEs
    mondo_df['source_id'] = mondo_df['source_id'].apply(lambda x: x.replace('https://orcid.org/', 'ORCID:'))
    # - CURIEs --> URIs
    mondo_df['synonym_type_mondo'] = mondo_df['synonym_type_mondo'].apply(_curies_to_uris_from_delim_str)
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
        'synonym_x': 'synonym_case_mondo', 'synonym_y': 'synonym_case_source'})  # keep Mondo casing if different
    confirmed_df = confirmed_df[confirmed_df[['mondo_id', 'source_id']].apply(tuple, axis=1).isin(mapping_pairs_set)]
    confirmed_df = _add_syn_variation_cols(confirmed_df)
    del confirmed_df['mondo_evidence']
    confirmed_df = _common_operations(confirmed_df, outpath_confirmed, mondo_exclusions_df=mondo_exclusions_df)
    confirmed_df['case'] = 'confirmed'

    # -updated
    #  Cases where scope has is different in source
    updated_df = mondo_df.merge(source_df, on=['synonym_lower'], how='inner').rename(columns={
        'synonym_scope_x': 'synonym_scope_mondo', 'synonym_scope_y': 'synonym_scope',
        'synonym_x': 'synonym_case_mondo', 'synonym_y': 'synonym_case_source'})  # keep Mondo casing if different
    updated_df = updated_df[updated_df[['mondo_id', 'source_id']].apply(tuple, axis=1).isin(mapping_pairs_set)]
    updated_df = _add_syn_variation_cols(updated_df)
    updated_df = updated_df[updated_df['synonym_scope_mondo'] != updated_df['synonym_scope']]
    updated_df = _common_operations(updated_df, outpath_updated, mondo_exclusions_df=mondo_exclusions_df)
    updated_df['case'] = 'updated'

    # -added
    #  Cases where synonym exists in source term but not in mapped Mondo term
    # - add mapped mondo IDs
    source_df_with_mondo_ids = source_df.merge(mappings_df[[
        'source_id', 'mondo_id', 'mondo_label']], on=['source_id'], how='inner')
    source_df_with_mondo_ids['synonym_case_source'] = source_df_with_mondo_ids['synonym']
    # - leave only synonyms that don't exist on given Mondo IDs
    added_df = _filter_a_by_not_in_b(source_df_with_mondo_ids, mondo_df, ['mondo_id', 'synonym_lower'])
    added_df = added_df[added_df[['mondo_id', 'source_id']].apply(tuple, axis=1).isin(mapping_pairs_set)]
    added_df = _common_operations(added_df, outpath_added, mondo_exclusions_df=mondo_exclusions_df)
    added_df['case'] = 'added'

    # -deleted
    #  Cases where synonym exists in Mondo term, but not in mapped source term
    deleted_df = pd.DataFrame()
    # todo: -deleted: reactivate when ready.
    #  - depends on more than just 1 source not having synonym. it must (i) exist on no mapped source terms, and (ii)
    #  have no other qualifying evidence (I think just: ORCID & MONDO;notVerified),
    #  - considerations: what role source_id plays in this logic. this may be outdated
    #  - ensure has labels
    # todo: do 100% of mondo and source terms in here have labels? I think they should.
    # todo: unsure what role mondo excluded synonyms will have here
    # todo: i think this implementation is outdated post source_id refactor
    if outpath_deleted:
        deleted_df = mondo_df.merge(
            source_df, on=['synonym_scope', 'synonym_lower'], how='left', indicator=True)
        deleted_df = deleted_df[deleted_df['_merge'] == 'left_only'].drop('_merge', axis=1)  # also can do: mondo_id=nan
        deleted_df = _filter_a_by_not_in_b(deleted_df, updated_df, ['mondo_id', 'source_id', 'synonym_lower'])
        deleted_df = _common_operations(deleted_df, outpath_deleted, mondo_exclusions_df=mondo_exclusions_df)
        deleted_df['case'] = 'deleted'

    # Write outputs
    combined_cases_df = pd.concat([confirmed_df, added_df, updated_df, deleted_df], ignore_index=True)\
        .fillna('')
    combined_cases_df = _common_operations(combined_cases_df, outpath_combined, df_is_combined=True)
    combined_cases_df['source'] = source_name
    combined_cases_df = pd.concat([pd.DataFrame([HEADERS_TO_ROBOT_SUBHEADERS]), combined_cases_df])
    combined_cases_df.to_csv(outpath_combined, sep='\t', index=False)


def cli():
    """Command line interface."""
    parser = ArgumentParser(
        prog='sync-synonyms',
        description='Create outputs for syncing synonyms between Mondo and its sources.')
    parser.add_argument(
        '-o', '--ontology-db-path', required=True,
        help='Path to SemanticSQL sqlite `.db` file for the given source ontology.')
    parser.add_argument(
        '-m', '--mondo-synonyms-path', required=True,
        help='Path to a TSV containing information about Mondo synonyms. Columns: ?mondo_id, ?dbXref, ?synonym_scope, '
             '?synonym, synonym_type.')
    parser.add_argument(
        '-e', '--mondo-exclusion-configs', required=True,
        help='Path to a YAML which includes information such as (i) synonyms to exclude, (ii) synonyms for which to '
             'exclude addition of "abbreviation" synonym type.')
    parser.add_argument(
        '-O', '--onto-synonym-types-path', required=True,
        help='Path to a TSV containing information about synonyms for the source. Columns: ?mondo_id, ?dbXref, '
             '?synonym_scope, ?synonym, synonym_type.')
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
        '-d', '--outpath-deleted', required=False,  # todo: change to True when adding back this feature
        help='Path to ROBOT template TSV to create which will contain synonym deletions; exists in Mondo but not '
             'in source(s) for a given mapping.')
    parser.add_argument(
        '-u', '--outpath-updated', required=True,
        help='Path to ROBOT template TSV to create which will contain updates to synonym scope predicate; cases where '
             'the synonym exists in Mondo and on the mapped source term, but the scope predicate is different.')
    parser.add_argument(
        '-b', '--outpath-combined', required=True,
        help='Path to curation file which is a concatenation of all cases.')
    sync_synonyms(**vars(parser.parse_args()))


if __name__ == '__main__':
    cli()
