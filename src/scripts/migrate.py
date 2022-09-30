"""Slurp migration pipeline

Basically, we:
1. Look at all unmapped terms T
2. If all of parents of T are mapped, designate for slurping (we only slurp if parents are already slurped, iteratively)
3. Extract basic information about T and export as ROBOT template

Resources
- https://incatools.github.io/ontology-access-kit/
- https://incatools.github.io/ontology-access-kit/intro/tutorial02.html

TODO's (major):
  -
"""
from argparse import ArgumentParser
from typing import Dict, List, Set, Union

import pandas as pd
import yaml
from oaklib.implementations import ProntoImplementation
from oaklib.types import CURIE, URI

from utils import CACHE_DIR, PREFIX, Term, _get_all_owned_terms, _get_next_available_mondo_id, \
    get_excluded_terms, get_mondo_term_ids, _load_ontology


ROBOT_TEMPLATE_HEADER = {
    'mondo_id': 'ID', 'mondo_label': 'LABEL', 'xref': 'A oboInOwl:hasDbXref',
    'xref_source': '>A oboInOwl:source SPLIT=|', 'original_label': '', 'definition': 'A IAO:0000115', 'parents': 'SC %'}


def slurp(
    ontology_path: str, onto_config_path: str, onto_exclusions_path: str, sssom_map_path: str, min_id: int, max_id: int,
    mondo_terms_path: str, slurp_dir_path: str, outpath: str, use_cache=False
) -> pd.DataFrame:
    """Run slurp pipeline for given ontology
    todo: Speed: tried on an older computer and it was indeed too slow. Has to do w/ term class / utils, probably.
    """
    # Read inputs
    ontology: ProntoImplementation = _load_ontology(ontology_path, use_cache)
    with open(onto_config_path, 'r') as stream:
        onto_config = yaml.safe_load(stream)
        owned_prefix_map: Dict[PREFIX, URI] = onto_config['base_prefix_map']
    sssom_df: pd.DataFrame = pd.read_csv(sssom_map_path, comment='#', sep='\t')
    excluded_terms: Set[CURIE] = get_excluded_terms(onto_exclusions_path)
    mondo_term_ids: Set[int] = get_mondo_term_ids(mondo_terms_path, slurp_dir_path)

    # Intermediates
    owned_terms: List[Term] = _get_all_owned_terms(
        ontology=ontology, owned_prefix_map=owned_prefix_map, ontology_path=ontology_path, cache_dir_path=CACHE_DIR,
        onto_config_path=onto_config_path, use_cache=use_cache)
    owned_term_curies: List[CURIE] = [x.curie for x in owned_terms]
    sssom_object_ids: Set[Union[URI, CURIE]] = set(sssom_df['object_id'])  # Usually CURIE, but spec allows URI
    unmapped_terms: List[Term] = [x for x in owned_terms if x.curie not in sssom_object_ids]
    slurp_candidates = [x for x in unmapped_terms if x.curie not in excluded_terms]  # remove exclusions

    # Determine slurpable terms
    # - Slurpable term: A term for which all parents are already slurped. In other words, no parent is owned by the
    # ontology but unmapped in Mondo.
    next_mondo_id = min_id
    terms_to_slurp: List[Dict[str, str]] = []
    for t in slurp_candidates:
        # If all T.parents mapped, and at least one of them is an exact or narrow match, designate T for slurping
        # (i.e. only slurp if parents are already slurped)
        qualified_parents = True
        parent_mondo_ids = []
        for parent_curie in t.direct_owned_parent_curies:
            # Conversely, if any of T.parents is unmapped, T is not to be slurped
            if parent_curie in sssom_object_ids:
                parent_df: pd.DataFrame = sssom_df[sssom_df['object_id'] == parent_curie]
                parent_mondo_id = parent_df.to_dict('records')[0]['subject_id']
                parent_mondo_ids.append(parent_mondo_id)
            if parent_curie not in sssom_object_ids and parent_curie in owned_term_curies:
                qualified_parents = False
                break
        if qualified_parents:
            next_mondo_id, mondo_term_ids = _get_next_available_mondo_id(next_mondo_id, max_id, mondo_term_ids)
            # mondo_id = 'MONDO:' + ('0' * (len(str(next_mondo_id)) - 7)) + str(next_mondo_id)  # min->max needs no pad
            mondo_id = 'MONDO:' + str(next_mondo_id)
            mondo_label = t.label.lower() if t.label else ''
            terms_to_slurp.append({
                'mondo_id': mondo_id, 'mondo_label': mondo_label, 'xref': t.curie, 'xref_source': 'MONDO:equivalentTo',
                'original_label': t.label if t.label else '', 'definition': t.definition if t.definition else '',
                'parents': '|'.join(parent_mondo_ids)})

    result = pd.DataFrame([ROBOT_TEMPLATE_HEADER] + terms_to_slurp)
    result.to_csv(outpath, sep="\t", index=False)
    return result


# todo: add way to not read from cache, but write to cache
def cli():
    """Command line interface."""
    package_description = \
        'Slurp pipeline: Integrate new terms from other ontologies into Mondo.'
    parser = ArgumentParser(description=package_description)
    parser.add_argument(
        '-o', '--ontology-path', required=True,
        help='Path to ontology file, e.g. an `.owl` file.')
    parser.add_argument(
        '-c', '--onto-config-path', required=True,
        help='Path to a config `.yml` for the ontology which contains a `base_prefix_map` which contains a '
             'list of prefixes owned by the ontology. Used to filter out terms.')
    parser.add_argument(
        '-e', '--onto-exclusions-path', required=True,
        help='Path to a text file, e.g with naming pattern `<ontology>_term_exclusions.txt` which contains a list of '
             ' terms that are exclueded from inclusion into Mondo. Should be a plain file of line break delimited terms'
             '; only 1 column with no column header.')
    parser.add_argument(
        '-s', '--sssom-map-path', required=True,
        help='Path to file containing all known Mondo mappings, in SSSOM format.')
    parser.add_argument(
        '-m', '--min-id', required=True,
        help='The Mondo ID from which we want to begin to possibly allow for assignment of new Mondo IDs for any'
             ' unslurped terms.')
    parser.add_argument(
        '-M', '--max-id', required=True,
        help='The max Mondo ID we should ever assign for any unslurped terms.')
    parser.add_argument(
        '-t', '--mondo-terms-path', required=True,
        help='Path to a file that contains a list of all Mondo terms.')
    parser.add_argument(
        '-l', '--slurp-dir-path', required=True,
        help='Path to `slurp/` dir where other slurp files are checked so that any assigned Mondo IDs are not re-used')
    parser.add_argument(
        '-O', '--outpath', required=True,
        help='Path to save the output slurp `.tsv` file, containing list of new terms to integrate into Mondo.')
    parser.add_argument(
        '-C', '--use-cache', required=False, action='store_true', default=False,
        help='Use cached ontology and owned_terms objects?')
    d: Dict = vars(parser.parse_args())

    # Reformatting
    d['min_id'] = int(d['min_id'])
    d['max_id'] = int(d['max_id'])
    # todo: Paths: Convert to absolute paths, as I've done before? Or expect always be run from src/ontology and ok?

    # Run
    slurp(**d)


if __name__ == '__main__':
    cli()
