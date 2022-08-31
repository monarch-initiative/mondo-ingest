"""Slurp migration pipeline

Resources
- https://incatools.github.io/ontology-access-kit/
- https://incatools.github.io/ontology-access-kit/intro/tutorial02.html

TODO's:
  -
"""
from argparse import ArgumentParser
from typing import Dict, List, Set, Tuple, Union

import curies
import pandas as pd
import oaklib
import yaml
from oaklib.implementations import ProntoImplementation, SqlImplementation
from oaklib.interfaces.basic_ontology_interface import RELATIONSHIP
from oaklib.resource import OntologyResource
from oaklib.types import CURIE, URI

TRIPLE = RELATIONSHIP


# TODO: implement this func
# todo: IDs should be int or str? prolly str
def determine_next_available_mondo_id(min_id: str, mondo_termlist_df: pd.DataFrame) -> str:
    """Starting from `min_id`, count up and check until finding the next ID."""
    next_id = str(0)
    return next_id


def _get_direct_owned_parents(ontology: ProntoImplementation, owned_prefix_map: Dict[str, str], uri: str) -> List[str]:
    """Get URIs of direct parents of a class. Only returns parents that are 'owned' by the ontology.

    ontology: Haven't decided yet which implementation I'll use. Would use superclass, but they use mult inheritance.
    owned_prefix_map: All the prefixes that are 'owned' by the ontology. Keys are CURIE prefixes and values are URIs.
    """
    # These vars are here for stability reasons, just in case I get CURIES where I expect URIs or vice versa.
    subclass_preds = [x + 'subClassOf' for x in ['rdfs:', 'http://www.w3.org/2000/01/rdf-schema#']]
    owned_prefixes = set(owned_prefix_map.keys())
    uri_converter = curies.Converter.from_prefix_map(owned_prefix_map)

    # TODO: Finish this, commit, update PR message, delete stuff in run()
    direct_owned_parent_uris: List[URI] = []
    rels: List[TRIPLE] = [x for x in ontology.relationships(subjects=[uri])]
    for rel in rels:
        subject, predicate, object = rel
        object_curie: CURIE = uri_converter.compress(object)  # This check is probably easier/faster if CURIE than URI
        if predicate in subclass_preds and object_curie.split(':')[0] in owned_prefixes:
            subject_uri: URI = uri_converter.expand(subject)  # Just in case got back a CURIE
            direct_owned_parent_uris.append(subject_uri)

    return direct_owned_parent_uris


def _get_all_owned_terms(
    ontology: Union[SqlImplementation, ProntoImplementation], owned_prefix_map: Dict[str, str], mode=['uri', 'curie'][0]
) -> List[str]:
    """Get all terms as CURIEs

    ontology: Haven't decided yet which implementation I'll use. Would use superclass, but they use mult inheritance.
    owned_prefix_map: All the prefixes that are 'owned' by the ontology. Keys are CURIE prefixes and values are URIs.
    mode: If 'uri', returns terms as URIs, else CURIEs if 'curie'.
    todo: owned_terms: if slow, can speed this up by grouping prefixes by splitting on : and filter out
    """
    if mode not in ['uri', 'curie']:
        raise ValueError('`_get_curies_all_owned_terms()`: `mode` must be one of "uri" or "curie".')

    # Get all terms: CURIES or URIs
    terms = [x for x in ontology.entities()]

    # Get CURIES
    uri_terms = []
    curie_terms_1 = []
    for t in terms:
        if t.startswith('http'):
            uri_terms.append(t)
        else:
            curie_terms_1.append(t)

    uri_converter = curies.Converter.from_prefix_map(owned_prefix_map)
    # Note: These code blocks are a little redundant with each other, but probably easier to read this way.
    if mode == 'curie':
        curie_terms_2 = []
        for uri in uri_terms:
            curie = uri_converter.compress(uri)
            if curie:
                curie_terms_2.append(curie)
        curie_terms = curie_terms_1 + curie_terms_2
        owned_terms = [x for x in curie_terms if any([x.startswith(y) for y in owned_prefix_map.keys()])]
    else:  # uri
        uri_terms_2 = []
        for uri in uri_terms:
            uri = uri_converter.expand(uri)
            if uri:
                uri_terms_2.append(uri)
        uri_terms = uri_terms + uri_terms_2
        owned_terms = [x for x in uri_terms if any([x.startswith(y) for y in owned_prefix_map.values()])]

    return owned_terms


def run(ontology_path: str, onto_config_path: str, sssom_map_path: str, min_id: str, mondo_terms_path: str, outpath: str) -> pd.DataFrame:
    """Run slurp pipeline for given ontology"""
    # Read inputs
    # todo's: Ontology implementation selection
    #  i. If trouble, can try `SparqlImplementation`, but ~6 min to load and queries slow (cuz rdflib)
    #  ii. use Sql > Pronto when .entities() fixed: https://github.com/INCATools/ontology-access-kit/issues/235
    with open(onto_config_path, 'r') as stream:
        onto_config = yaml.safe_load(stream)
        owned_prefix_map: Dict[str, str] = onto_config['base_prefix_map']
    # ontology = SqlImplementation(OntologyResource(slug=ontology_path, local=True))
    ontology = ProntoImplementation(OntologyResource(slug=ontology_path, local=True))
    sssom_df = pd.read_csv(sssom_map_path, comment='#', sep='\t')
    mondo_termlist_df = pd.read_csv(mondo_terms_path, comment='#', sep='\t')

    # TODO: delete this section
    # Get relationships
    edge_triples_uris_and_curies: List[Tuple] = [x for x in ontology.relationships()]
    # - If is URI, try to convert to CURIE
    edge_triples_curies: List[Tuple] = []
    owned_prefix_map: Dict[str, URI] = onto_config['base_prefix_map']
    uri_converter = curies.Converter.from_prefix_map(owned_prefix_map)
    for triple in edge_triples_uris_and_curies:
        new_triple = ()
        for uri_or_curie in triple:
            curie: CURIE = uri_converter.compress(uri_or_curie)
            new_triple += (curie,) if curie else (uri_or_curie,)
        edge_triples_curies.append(new_triple)
    # - Build lookup dict of all the direct parents of each term. Only includes direct parents owned by the ontology.
    term_parent_map: Dict[str, List[str]] = {}
    owned_prefixes = set(onto_config['base_prefix_map'].keys())
    for triple in edge_triples_curies:
        subject, predicate, object = triple
        if subject not in term_parent_map:
            term_parent_map[subject] = []
        if predicate == 'rdfs:subClassOf' and object.split(':')[0] in owned_prefixes:
            term_parent_map[subject].append(object)

    # TODO: For entities, get term URIs and CURIEs so I can do easy later
    #  - might want a func for this
    #  - make feature request for curies lib. Term class w/ URI and CURIE property.
    # Get slurpable terms
    slurpable_terms = []
    owned_term_uris: List[Union[URI, CURIE]] = _get_all_owned_terms(ontology, owned_prefix_map, mode='uri')
    sssom_object_ids: Set[CURIE] = set(sssom_df['object_id'])
    for t in owned_term_uris:
        if t not in sssom_object_ids:
            migrate = True
            # todo: finish _get_direct_parents()
            direct_parents: List[URI] = _get_direct_owned_parents(ontology, owned_prefix_map, t)
            slurpable_parents: List[URI] = []
            for parent in direct_parents:
                # TODO: parent['uri']
                if parent not in sssom_object_ids:
                    migrate = False
                    break
                else:
                    obj_data = sssom_df[sssom_df['object_id'] == parent]
                    pred = str(obj_data['predicate_id'])
                    if pred in ['skos:exactMatch', 'skos:narrowMatch']:
                        # In other words, if the parent is mapped, and the mapping is either exact or narrower, OK to add
                        # todo: Ok to add
                        slurpable_parents.append(obj_data['subject_id'])
                    else:
                        pass  # Its fine, just continue looking for other parents in this case
            if migrate and slurpable_parents:
                # TODO: implement this func:
                next_mondo_id = determine_next_available_mondo_id(min_id, mondo_termlist_df)  # satrting from min_id, then counting up and checking if it does not already exist.
                # todo: Find the correct way of doing this:
                label = oaklib.get_label(t)
                # todo: Find the correct way of doing this:
                definition = oaklib.get_definition(t)
                # TODO: Convert uri to curie
                slurpable_terms.append({'mondo_id': next_mondo_id, 'xref': t, 'label': label, 'definition': definition})

    result = pd.DataFrame(slurpable_terms)
    result.to_csv(outpath, sep="\t")
    return result


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
        '-m', '--sssom-map-path', required=True,
        help='Path to file containing all known Mondo mappings, in SSSOM format.')
    parser.add_argument(
        '-i', '--min-id', required=True,
        help='The ID from which we want to begin searching from in order to locate any currently unslurped terms.')
    parser.add_argument(
        '-t', '--mondo-terms-path', required=True,
        help='Path to a file that contains a list of all Mondo terms.')
    parser.add_argument(
        '-O', '--outpath', required=True,
        help='Path to save the output slurp `.tsv` file, containing list of new terms to integrate into Mondo.')
    d: Dict = vars(parser.parse_args())
    # todo: Convert paths to absolute paths, as I've done before? Or expect always be run from src/ontology and ok?
    run(**d)


if __name__ == '__main__':
    cli()
