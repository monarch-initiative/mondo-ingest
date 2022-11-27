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


# Vars
USE_CACHE = False  # todo: add as cli param. this is for robot/semsql queries


# Functions
def run(
    onto_path: str, exclusions_path: str, mirror_signature_path: str, sssom_map_path: str, onto_config_path: str,
    outpath: str, use_cache: bool = USE_CACHE,
) -> pd.DataFrame:
    """Run

    todo's
     - change get_labels() to semsql when fixed: https://github.com/monarch-initiative/mondo-ingest/issues/136
    """
    # TODO: try this temp fix for ORDO and check result
    onto_path = onto_path.replace('components/', 'mirror/')

    # Read sources
    with open(onto_config_path, 'r') as stream:
        onto_config = yaml.safe_load(stream)
        prefix_map: Dict[str, str] = onto_config['base_prefix_map']
    converter = curies.Converter.from_prefix_map(prefix_map)
    all_terms: Set[str] = set(pd.read_csv(mirror_signature_path, sep='\t').fillna('')['?term'])  # <IRI>
    all_terms: Set[Union[CURIE, None]] = \
        set([converter.compress(x.replace('>', '').replace('<', '')) for x in all_terms])
    exclusions: Set[CURIE] = set(pd.read_csv(exclusions_path, header=None, names=['id']).fillna('')['id'])
    mappings: Set[CURIE] = set(pd.read_csv(sssom_map_path, sep='\t', comment='#').fillna('')['object_id'])

    # Determine unmapped terms
    unmapped: List[CURIE] = sorted([x for x in (all_terms - exclusions - mappings) if x])  # if not x: not in prefix_map
    all_terms: List[CURIE] = sorted([x for x in all_terms if x])  # if not x: not in prefix_map
    unmapped_comments: List[str] = ['Unmapped' if x in unmapped else '' for x in all_terms]

    # Get labels & create table
    all_labels: List[str] = get_labels(
        onto_path=onto_path, curie_list=all_terms, prefix_map=prefix_map, use_cache=use_cache)
    mappable_df = pd.DataFrame({'subject_id': all_terms, 'subject_label': all_labels, 'comment': unmapped_comments})

    # Sort
    if len(mappable_df) > 0:
        mappable_df = mappable_df.sort_values(['comment', 'subject_id', 'subject_label'], ascending=[False, True, True])

    # Save & return
    mappable_df.to_csv(outpath, sep='\t', index=False)
    return mappable_df


def cli():
    """Command line interface."""
    parser = ArgumentParser('Creates TSVs and of unmapped terms as well as summary statistics.')
    # todo: add back when fixed: until https://github.com/monarch-initiative/mondo-ingest/issues/136
    # parser.add_argument('-d', '--db-path', required=True, help='Path to SemanticSQL sqlite ONTO_NAME.db.')
    parser.add_argument('-O', '--onto-path', required=True, help='Optional. Path to the ontology file to query.')
    parser.add_argument('-o', '--outpath', required=True, help='Path to create unmapped-ONTO_NAME.tsv.')
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
    run(**vars(parser.parse_args()))


# Execution
if __name__ == '__main__':
    cli()
