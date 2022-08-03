"""Slurp migration pipeline

Resources
- https://incatools.github.io/ontology-access-kit/
- https://incatools.github.io/ontology-access-kit/intro/tutorial02.html

TODO's:
  -
"""
from argparse import ArgumentParser
from typing import Dict, List, Union

import curies
import pandas as pd
import oaklib
import yaml
from oaklib.implementations import ProntoImplementation, SqlImplementation
from oaklib.resource import OntologyResource


# TODO: implement this func
# todo: IDs should be int or str? prolly str
def determine_next_available_mondo_id(min_id: str, mondo_termlist_df: pd.DataFrame) -> str:
    """Starting from `min_id`, count up and check until finding the next ID."""
    next_id = str(0)
    return next_id


def _get_direct_parents(ontology: Union[ProntoImplementation, SqlImplementation], curie: str):
    """Get CURIEs of parents of a class
    ontology: Haven't decided yet which implementation I'll use. Would use superclass, but they use mult inheritance.
    """
    # todo: SqlImplementation: pending fixes:
    #  - entities(): https://github.com/INCATools/ontology-access-kit/issues/235
    #  - relationships(subjects=[CURIE]): https://github.com/INCATools/ontology-access-kit/issues/238
    if isinstance(ontology, SqlImplementation):
        # rels: Iterator[Tuple] = ontology.relationships([curie])
        pass
    if isinstance(ontology, ProntoImplementation):
        # todo: pending 0 results fix: https://github.com/INCATools/ontology-access-kit/issues/237
        # todo: I probably need only 1 of these
        # rels_in: Dict = ontology.incoming_relationship_map(curie)
        # rels_out: Dict = ontology.outgoing_relationship_map(curie)
        pass


    # TODO: How to get just the *direct* parents? look at relationships and see if rdfs:subClassOf?
    #  ...Until above issues fixed, will need to get all relationships at beginning of run() func and use that
    p = []
    # for rel, parents in rels.items():
    #     # print(f'  {rel} ! {ontology.get_label_by_curie(rel)}')
    #     for parent in parents:
    #         # print(f'    {parent} ! {ontology.get_label_by_curie(parent)}')
    #         p.append(parent)
    return p


def _get_curies_all_owned_terms(
    ontology: Union[SqlImplementation, ProntoImplementation], owned_prefix_map: Dict[str, str]
) -> List[str]:
    """Get all terms as CURIEs
    ontology: Haven't decided yet which implementation I'll use. Would use superclass, but they use mult inheritance.
    todo: owned_terms: if slow, can speed this up by grouping prefixes by splitting on : and filter out
    """
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

    # - Convert from URI if needed
    uri_converter = curies.Converter.from_prefix_map(owned_prefix_map)
    curie_terms_2 = []
    terms_with_no_known_prefix = []
    for uri in uri_terms:
        curie = uri_converter.compress(uri)
        if curie:
            curie_terms_2.append(curie)
        else:
            terms_with_no_known_prefix.append(uri)
    curie_terms = curie_terms_1 + curie_terms_2

    # Filter: Terms 'owned' by ontology
    owned_terms = [x for x in curie_terms if any([x.startswith(y) for y in owned_prefix_map.keys()])]

    return owned_terms


def run(ontology_path: str, onto_config_path: str, sssom_map_path: str, min_id: str, mondo_terms_path: str, outpath: str) -> pd.DataFrame:
    """Run slurp pipeline for given ontology"""
    # Prefixes
    with open(onto_config_path, 'r') as stream:
        onto_config = yaml.safe_load(stream)

    # Read source files
    # todo's: Ontology implementation selection
    #  i. If trouble, can try `SparqlImplementation`, but ~6 min to load and queries slow (cuz rdflib)
    #  ii. use Sql > Pronto when .entities() fixed: https://github.com/INCATools/ontology-access-kit/issues/235
    # ontology = SqlImplementation(OntologyResource(slug=ontology_path, local=True))
    ontology = ProntoImplementation(OntologyResource(slug=ontology_path, local=True))

    # TODO: Repurpose the following two working lines. use this to get all rels, convert to curies, then use.
    # ontology_sql = SqlImplementation(OntologyResource(slug=ontology_path, local=True))
    # all_rels = [x for x in ontology_sql.relationships()]  # len=32,926 (of triples)

    sssom_df = pd.read_csv(sssom_map_path, comment='#', sep='\t')
    mondo_termlist_df = pd.read_csv(mondo_terms_path, comment='#', sep='\t')

    # Initialize variables
    source_onto_curies: List[str] = _get_curies_all_owned_terms(ontology, owned_prefix_map=onto_config['base_prefix_map'])
    sssom_object_ids = set(sssom_df['object_id'])

    # Get slurpable terms
    slurpable_terms = []
    for t in source_onto_curies:
        if t not in sssom_object_ids:
            migrate = True
            # todo: finish _get_direct_parents()
            direct_parents: List[str] = _get_direct_parents(ontology, t)
            slurpable_parents: List[str] = []
            for parent in direct_parents:
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
