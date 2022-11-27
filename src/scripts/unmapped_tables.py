"""Generates a TSV of mapping progress for a given ontology, by term, in the format below.

| subject_id   | subject_label              | comment   |
|:-------------|:---------------------------|:----------|
| DOID:12345   | Variation of toxoplasmosis | Unmapped  |
| DOID:9969    | carotenemia                |           |

Resources
- GitHub issue: https://github.com/mapping-commons/disease-mappings/issues/12
- GitHub PR: https://github.com/monarch-initiative/mondo-ingest/pull/111/
"""
from argparse import ArgumentParser
from typing import Dict, List, Set, Union

import curies
import pandas as pd
import yaml
from oaklib.types import CURIE

from utils import get_labels


NULLABLE_BOOL = Union[bool, None]


def create_mapping_status_tables(
    onto_path: str, exclusions_path: str, mirror_signature_path: str, sssom_map_path: str, onto_config_path: str,
    outpath_full: str, outpath_simple: str, use_cache_labels: bool = False,
) -> Dict[str, pd.DataFrame]:
    """Run

    todo's
     - change get_labels() to semsql when fixed: https://github.com/monarch-initiative/mondo-ingest/issues/136
    """
    # TODO: Remove this hackery when NCIT error fixed: https://github.com/monarch-initiative/mondo-ingest/issues/171
    if 'ncit' in onto_path.lower():
        # return {'full': pd.DataFrame(), 'simple': pd.DataFrame()}
        # This uses cached version of plain mirror signature for NCIT
        mirror_signature_path = mirror_signature_path.replace('-incl-deprecated', '')

    # Read sources
    with open(onto_config_path, 'r') as stream:
        onto_config = yaml.safe_load(stream)
        prefix_map: Dict[str, str] = onto_config['base_prefix_map']
    converter = curies.Converter.from_prefix_map(prefix_map)
    mirror_df = pd.read_csv(mirror_signature_path, sep='\t').fillna('')
    mirror_df['?term'] = mirror_df['?term'].apply(lambda x: converter.compress(x.replace('>', '').replace('<', '')))
    all_terms: Set[CURIE] = set(mirror_df['?term'])

    # TODO: Remove this hackery when NCIT error fixed: https://github.com/monarch-initiative/mondo-ingest/issues/171
    if 'ncit' in onto_path.lower():
        deprecated_terms = set()
    else:
        deprecated_terms: Set[CURIE] = set(mirror_df[mirror_df['?deprecated'] == True]['?term'])

    excluded_terms: Set[CURIE] = set(pd.read_csv(exclusions_path, header=None, names=['id']).fillna('')['id'])
    mapped_terms: Set[CURIE] = set(pd.read_csv(sssom_map_path, sep='\t', comment='#').fillna('')['object_id'])

    # Determine unmapped terms
    # - `if not x`: means not in `prefix_map`, so not a relevant term for this ontology
    all_terms: List[CURIE] = sorted([x for x in all_terms if x])
    is_mapped: List[NULLABLE_BOOL] = [x in mapped_terms for x in all_terms]
    is_excluded: List[NULLABLE_BOOL] = [x in excluded_terms for x in all_terms]
    # TODO: Remove this hackery when NCIT err fixed: https://github.com/monarch-initiative/mondo-ingest/issues/171
    if 'ncit' in onto_path.lower():
        is_deprecated: List[NULLABLE_BOOL] = [None] * len(all_terms)
    else:
        is_deprecated: List[NULLABLE_BOOL] = [x in deprecated_terms for x in all_terms]

    # Get labels & create table
    # todo: maybe refactor to get terms and labels from this func. more stable?
    # TODO: Remove this hackery when NCIT err fixed: https://github.com/monarch-initiative/mondo-ingest/issues/171
    if 'ncit' in onto_path.lower():
        all_labels: List[str] = [''] * len(all_terms)
    else:
        all_labels: List[str] = get_labels(
            onto_path=onto_path, curie_list=all_terms, prefix_map=prefix_map, use_cache=use_cache_labels)
    df = pd.DataFrame({
        'subject_id': all_terms, 'subject_label': all_labels, 'is_mapped': is_mapped, 'is_excluded': is_excluded,
        'is_deprecated': is_deprecated})

    if len(df) == 0:
        return {'full': df, 'simple': df}

    # Sort
    df['label_missing'] = df['subject_label'].apply(lambda x: x == '')
    df = df.sort_values(
        ['is_mapped', 'is_excluded', 'is_deprecated', 'label_missing', 'subject_id'],  # 'subject_label'
        ascending=[True, True, True, True, True])
    df = df.drop(columns=['label_missing'])

    # Simple table
    # todo: when fixed (https://github.com/monarch-initiative/mondo-ingest/issues/171): `df['is_deprecated'] == False`
    df_simple = df[
        (df['is_excluded'] == False) & (df['is_deprecated'].isin([False, None])) & (df['is_mapped'] == False)]
    df_simple = df_simple.drop(columns=['is_mapped', 'is_excluded', 'is_deprecated'])
    df_simple = df_simple.sort_values(['subject_label', 'subject_id'], ascending=[True, True])

    # Save & return
    df.to_csv(outpath_full, sep='\t', index=False)
    df_simple.to_csv(outpath_simple, sep='\t', index=False)

    return {'full': df, 'simple': df_simple}


def cli():
    """Command line interface."""
    parser = ArgumentParser('Creates TSVs and of unmapped terms as well as summary statistics.')
    # todo: add back when fixed: until https://github.com/monarch-initiative/mondo-ingest/issues/136
    # parser.add_argument('-d', '--db-path', required=True, help='Path to SemanticSQL sqlite ONTO_NAME.db.')
    parser.add_argument('-n', '--onto-path', required=True, help='Optional. Path to the ontology file to query.')
    parser.add_argument('-o', '--outpath-full', required=True,
                        help='Path to create a TSV with a list of all terms and columns: subject_id, subject_label, '
                             'is_mapped, is_excluded, is_deprecated.')
    parser.add_argument('-O', '--outpath-simple', required=True,
                        help='Path to create a TSV with a list of all unmapped mappable terms and columns: subject_id, '
                             'subject_label.')
    parser.add_argument(
        '-e', '--exclusions-path', required=True,
        help='Path to a TXT file; a line-break delimited list of term IDs excluded from Mondo for a given ontology.')
    parser.add_argument(
        '-c', '--onto-config-path', required=True,
        help='Path to a config `.yml` for the ontology which contains a `base_prefix_map` which contains a '
             'list of prefixes owned by the ontology. Used to filter out terms.')
    parser.add_argument(
        '-s', '--sssom-map-path', required=True,
        help='Path to file containing all known Mondo mappings, in SSSOM format.')
    parser.add_argument(
        '-m', '--mirror-signature-path', required=True,
        help='Path to a "mirror signature" file, which contains a list of class URIs from the unaltered '
             'source ontology.')
    parser.add_argument(
        '-C', '--use-cache-labels', required=False, action='store_true', default=False,
        help='When fetching labels for terms, the results will be cached. When doing a new run, use this flag if you '
             'want to speed things up and use the cache.')
    create_mapping_status_tables(**vars(parser.parse_args()))


if __name__ == '__main__':
    cli()
