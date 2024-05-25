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
from oaklib import get_implementation_from_shorthand
from oaklib.types import CURIE, URI

from utils import remove_angle_brackets


def create_mapping_status_tables(
    db_path: str, exclusions_path: str, mondo_mappings_path: str, onto_config_path: str, outpath_full: str,
    outpath_simple: str
) -> Dict[str, pd.DataFrame]:
    """Create mapping status tables"""
    # Load sources
    # - prefix_preplacement_map: Cases where mondo-ingest prefixes differ from bioregistry/OAK, e.g. Orphanet vs ORDO
    # todo: refactor duplicate/similar blocks to a single function
    with open(onto_config_path, 'r') as stream:
        onto_config = yaml.safe_load(stream)
        prefix_map: Dict[str, str] = onto_config['base_prefix_map']
        owned_prefixes: List[str] = list(prefix_map.keys())
        converter = curies.Converter.from_prefix_map(prefix_map)
        prefix_replacement_map = {
            f'{alias}:': f'{preferred}:' for preferred, alias in onto_config['prefix_aliases'].items()} \
            if 'prefix_aliases' in onto_config else {}
    excluded_terms: Set[CURIE] = set(pd.read_csv(exclusions_path, header=None, names=['id']).fillna('')['id'])
    mapped_terms: Set[CURIE] = set(pd.read_csv(mondo_mappings_path, sep='\t', comment='#').fillna('')['object_id'])
    oi = get_implementation_from_shorthand(db_path)

    # Get all terms and labels
    ids_all: List[Union[CURIE, URI]] = [x for x in oi.entities(filter_obsoletes=False)]
    ids_all = remove_angle_brackets(ids_all)
    ids_sans_deprecated: List[Union[CURIE, URI]] = [x for x in oi.entities(filter_obsoletes=True)]
    ids_sans_deprecated = remove_angle_brackets(ids_sans_deprecated)
    ids_sans_deprecated: Set[Union[CURIE, URI]] = set(ids_sans_deprecated)
    id_labels_all: List[tuple] = [x for x in oi.labels(ids_all)]
    id_labels_all_map: Dict[Union[CURIE, URI], str] = {x[0]: x[1] for x in id_labels_all}

    # Filter to owned terms; convert to CURIEs
    curie_labels: Dict[CURIE, str] = {}
    curies_deprecated: Set[CURIE] = set()
    for _id, label in id_labels_all_map.items():
        curie: CURIE = _id if converter.is_curie(_id) else converter.compress(_id)
        for alias, preferred in prefix_replacement_map.items():
            curie = curie.replace(alias, preferred) if curie else curie
        if curie and curie.split(':')[0] in owned_prefixes:
            curie_labels[curie] = label
            if _id not in ids_sans_deprecated:
                curies_deprecated.add(curie)

    # Build dataframe
    is_mapped: List[bool] = [x in mapped_terms for x in curie_labels.keys()]
    is_excluded: List[bool] = [x in excluded_terms for x in curie_labels.keys()]
    is_deprecated: List[bool] = [x in curies_deprecated for x in curie_labels.keys()]
    df = pd.DataFrame({
        'subject_id': curie_labels.keys(), 'subject_label': curie_labels.values(), 'is_mapped': is_mapped, 'is_excluded': is_excluded,
        'is_deprecated': is_deprecated})
    if len(df) == 0:
        raise RuntimeError('Mapping status: No "owned terms" found in the ontology. Not expected.')

    # Sort
    df['label_missing'] = df['subject_label'].apply(lambda x: x == '')
    df = df.sort_values(
        ['is_mapped', 'is_excluded', 'is_deprecated', 'label_missing', 'subject_id'],  # 'subject_label'
        ascending=[True, True, True, True, True])
    df = df.drop(columns=['label_missing'])

    # Simple table
    df_simple = df[
        (df['is_excluded'] == False) & (df['is_deprecated'] == False) & (df['is_mapped'] == False)]
    df_simple = df_simple.drop(columns=['is_mapped', 'is_excluded', 'is_deprecated'])
    df_simple = df_simple.sort_values(['subject_label', 'subject_id'], ascending=[True, True])

    # Save & return
    df.to_csv(outpath_full, sep='\t', index=False)
    df_simple.to_csv(outpath_simple, sep='\t', index=False)

    return {'full': df, 'simple': df_simple}


def cli():
    """Command line interface."""
    parser = ArgumentParser('Creates TSVs and of unmapped terms as well as summary statistics.')
    parser.add_argument('-d', '--db-path', required=True, help='Path to SemanticSQL sqlite ONTO_NAME.db.')
    parser.add_argument(
        '-o', '--outpath-full', required=True,
        help='Path to create a TSV with a list of all terms and columns: subject_id, subject_label, is_mapped, '
             'is_excluded, is_deprecated.')
    parser.add_argument(
        '-O', '--outpath-simple', required=True,
        help='Path to create a TSV with a list of all unmapped mappable terms and columns: subject_id, subject_label.')
    parser.add_argument(
        '-e', '--exclusions-path', required=True,
        help='Path to a TXT file; a line-break delimited list of term IDs excluded from Mondo for a given ontology.')
    parser.add_argument(
        '-c', '--onto-config-path', required=True,
        help='Path to a config `.yml` for the ontology which contains a `base_prefix_map` which contains a '
             'list of prefixes owned by the ontology. Used to filter out terms.')
    parser.add_argument(
        '-m', '--mondo-mappings-path', required=True,
        help='Path to file containing all known Mondo mappings, in SSSOM format.')
    create_mapping_status_tables(**vars(parser.parse_args()))


if __name__ == '__main__':
    cli()
