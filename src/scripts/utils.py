"""Slurp migration pipeline: utils

todo: refactor various scripts/ files to import paths from here
"""
import os
import pickle
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Union

import curies
import pandas as pd
import yaml
from jinja2 import Template
from oaklib import OntologyResource
from oaklib.implementations import ProntoImplementation, SqlImplementation
from oaklib.interfaces.basic_ontology_interface import BasicOntologyInterface, RELATIONSHIP
from oaklib.types import CURIE, URI
from pandas.errors import EmptyDataError


# todo: move these to a new config.py
PREFIX = str
PREFIX_MAP = Dict[PREFIX, URI]
TRIPLE = RELATIONSHIP
SCRIPTS_DIR = os.path.dirname(os.path.realpath(__file__))
PROJECT_DIR = os.path.realpath(os.path.join(SCRIPTS_DIR, '..', '..'))
ONTOLOGY_DIR = os.path.join(PROJECT_DIR, 'src', 'ontology')
METADATA_DIR = os.path.join(ONTOLOGY_DIR, 'metadata')
REPORTS_DIR = os.path.join(ONTOLOGY_DIR, 'reports')
SLURP_DIR = os.path.join(ONTOLOGY_DIR, 'slurp')
SPARQL_DIR = os.path.join(PROJECT_DIR, 'src', 'sparql')
TEMP_DIR = os.path.join(ONTOLOGY_DIR, 'tmp')
DOCS_DIR = os.path.join(PROJECT_DIR, 'docs')
CACHE_DIR = TEMP_DIR
DEFAULT_PREFIXES_CSV = os.path.join(ONTOLOGY_DIR, 'config', 'prefixes.csv')
MONDO_PREFIX_MAP: PREFIX_MAP = {
    'MONDO': 'http://purl.obolibrary.org/obo/MONDO_'
}


# todo: there are remaining todo's in this class
class Term:
    """A lightweight class representing an ontological (e.g. RDF/OWL) term class."""

    # todo: I have heard you're not supposed to default to empty list, but doing this is better UX
    #  ...because don't need to handle possible "TypeError: 'NoneType' object is not iterable". However, I might
    #  ...want to re-look into why this is advised not to do.
    def __init__(
        self, uri: URI = None, curie: CURIE = None, label: str = None, definition: str = None,
        direct_owned_parent_uris: List[Union[URI, CURIE]] = [],
        direct_owned_parent_curies: List[Union[URI, CURIE]] = [],
        ontology: ProntoImplementation = None, owned_prefix_map: Dict[PREFIX, URI] = None,
        general_prefix_map: Dict[PREFIX, URI] = None
    ):
        """Initialize a term.

        ontology: Requires use of `oaklib`, particularly the `ProntoImplementation`.
        owned_prefix_map: A prefix_map that includes *only* of the prefixes 'owned' by the ontology. Used to
        general_prefix_map: A general prefix_map. For conversion of URIs and CURIEs, even if not owned by ontology.
        direct_owned_parent_uris: Some items will be CURIE if URI not available and conversion fails
        direct_owned_parent_curies: Some items will be URI if CURIE not available and conversion fails"""
        if not (uri or curie):
            raise ValueError('Term: Must supply either `uri` or `curie`.')
        self.label = label
        self.definition = definition
        self.ontology = ontology
        self.owned_prefix_map = owned_prefix_map
        self.general_prefix_map = general_prefix_map
        if owned_prefix_map or general_prefix_map:
            self._converter = curies.Converter.from_prefix_map(
                general_prefix_map if general_prefix_map else owned_prefix_map)
        self.uri = uri
        self.curie = curie
        self.direct_owned_parent_uris = direct_owned_parent_uris
        self.direct_owned_parent_curies = direct_owned_parent_curies
        if uri and not curie:
            self.curie = self._converter.compress(uri)
        if curie and not uri:
            self.uri = self._converter.expand(curie)
        if direct_owned_parent_uris and not direct_owned_parent_curies:
            self.direct_owned_parent_curies = [self._converter.compress(x) for x in direct_owned_parent_uris]
        if direct_owned_parent_curies and not direct_owned_parent_uris:
            self.direct_owned_parent_uris = [self._converter.expand(x) for x in direct_owned_parent_curies]
        if ontology or owned_prefix_map or general_prefix_map:
            self.fetch_missing_props(
                ontology=ontology, owned_prefix_map=owned_prefix_map, general_prefix_map=general_prefix_map)

    # Deactivated. parents are being fetched in batch right now
    # todo: Refer to "todo #1" on _get_direct_owned_parents() for more details
    # def _get_direct_owned_parents(
    #     self, ontology: ProntoImplementation = None, owned_prefix_map: Dict[PREFIX, URI] = None
    # ) -> List[URI]:
    #     """Wrapper for: _get_direct_owned_parents()
    #
    #     Side effects: Also sets self.direct_owned_parent_curies"""
    #     # Get params from wherever supplied
    #     prefix_map = owned_prefix_map if owned_prefix_map else self.owned_prefix_map
    #     onto = ontology if ontology else self.ontology
    #     if not (prefix_map and onto):
    #         raise ValueError('Term._get_direct_owned_parents(): Must supply both `ontology` and `owned_prefix_map`.')
    #
    #     self.direct_owned_parent_uris = _get_direct_owned_parent_uris(
    #         curie=self.curie, ontology=self.ontology, owned_prefix_map=self.owned_prefix_map)
    #     if self.direct_owned_parent_uris:
    #         self.direct_owned_parent_curies = [self._converter.compress(x) for x in self.direct_owned_parent_uris]
    #     return self.direct_owned_parent_uris

    def fetch_missing_props(
        self, ontology: ProntoImplementation = None, general_prefix_map: Dict[PREFIX, URI] = None,
        owned_prefix_map: Dict[PREFIX, URI] = None
    ):
        """For any undefined properties, try to set their values using available params.

        ontology: Requires use of `oaklib`, particularly the `ProntoImplementation`.
        owned_prefix_map: A prefix_map that includes *only* of the prefixes 'owned' by the ontology. Used to
        general_prefix_map: A general prefix_map. For conversion of URIs and CURIEs, even if not owned by ontology."""
        # Get params from wherever supplied
        ontology = ontology if ontology else self.ontology
        general_prefix_map = general_prefix_map if general_prefix_map else self.general_prefix_map
        owned_prefix_map = owned_prefix_map if owned_prefix_map else self.owned_prefix_map
        if not (ontology or general_prefix_map or owned_prefix_map):
            raise ValueError('Term.fetch_missing_props(): Must supply at least one param.')

        # Set: uri, curie
        prefix_map = general_prefix_map if general_prefix_map else owned_prefix_map
        if prefix_map and self.uri and not self.curie:
            converter = self._converter if self._converter else curies.Converter.from_prefix_map(prefix_map)
            curie = converter.compress(self.uri)
            self.curie = curie if curie != self.uri else None
        elif prefix_map and self.curie and not self.uri:
            converter = curies.Converter.from_prefix_map(prefix_map)
            uri = converter.expand(self.curie)
            self.uri = uri if uri != self.curie else None

        # Set: label, definition
        # todo: Assign in batch (when OAK supports): I feel like would be faster to do outside the Term class itself
        #  ...e.g. build a dict of CURIE-> Term, then use use ontology.labels() on all curie_list and set label
        #  ...Right now, OAK ProntoImplementation labels() is just proxy for label(), though SqlImplementation has, and
        #  ...Both of them have definition() but not definitions().
        if ontology:
            self.label = ontology.label(self.uri)
            if not self.label:
                self.label = ontology.label(self.curie)
            self.definition = ontology.definition(self.uri)
            if not self.definition:
                self.definition = ontology.definition(self.curie)

        # Set: direct_owned_parent_uris
        # todo #1: Linked to work on _get_direct_owned_parents(), pending OAK fixes
        # if ontology and owned_prefix_map:
        #     self.direct_owned_parent_uris = self._get_direct_owned_parents(
        #         owned_prefix_map=owned_prefix_map if owned_prefix_map else self.owned_prefix_map)

    def __repr__(self):
        return f'<Term({self.curie if self.curie else self.uri})>'


def _load_ontology(ontology_path: str, use_cache=False) -> ProntoImplementation:
    """Load ontology"""
    cache_path_ontology = os.path.join(
        CACHE_DIR, f'{os.path.basename(ontology_path)}.pickle')

    if use_cache and os.path.exists(cache_path_ontology):
        # todo: Does loading from cache even save time? seemed to take ~16 sec
        ontology = pickle.load(open(cache_path_ontology, 'rb'))
    else:
        # todo's: Ontology implementation selection
        #  i. If trouble, can try `SparqlImplementation`, but ~6 min to load and queries slow (cuz rdflib)
        #  ii. use Sql > Pronto when .entities() fixed: https://github.com/INCATools/ontology-access-kit/issues/235
        # ontology = SqlImplementation(OntologyResource(slug=ontology_path, local=True))
        ontology = ProntoImplementation(OntologyResource(slug=ontology_path, local=True))  # ~17 sec
        if use_cache:
            with open(cache_path_ontology, 'wb') as f:
                pickle.dump(ontology, f, protocol=pickle.HIGHEST_PROTOCOL)

    return ontology


def get_monarch_curies_converter(from_prefixes_csv: Union[str, Path] = DEFAULT_PREFIXES_CSV) -> curies.Converter:
    """:param from_prefixes_csv: Path to a CSV with prefix in first column and URI stem in second."""
    if not from_prefixes_csv:
        # https://curies.readthedocs.io/en/latest/tutorial.html#loading-a-pre-defined-context
        return curies.get_monarch_converter()
    df = pd.read_csv(from_prefixes_csv)
    df['yaml'] = df.apply(lambda x: f'{x["prefix"]}: {x["base"]}', axis=1)
    prefix_map = yaml.safe_load('\n'.join(df['yaml']))
    conv = curies.Converter.from_prefix_map(prefix_map)
    return conv


def _get_next_available_mondo_id(min_id: int, max_id: int, mondo_ids: Set[int]) -> (int, Set[int]):
    """Starting from `min_id`, count up and check until finding the next ID.

    :returns: (int) next mondo ID; (Set[int]) New set of Mondo IDs, assuming 'next mondo ID' is included."""
    next_id = int(min_id)
    while True:
        next_id = next_id + 1
        if next_id > max_id:
            raise ValueError('Ran out of valid IDs to assign for new slurpable Mondo terms. Either `min_id`, `max_id`, '
                             'or both should be changed to allow for new assignments.')
        if next_id not in mondo_ids:
            break
    mondo_ids.add(next_id)
    return next_id, mondo_ids


def remove_angle_brackets(uris: Union[URI, List[URI]]) -> Union[URI, List[URI]]:
    """Remove angle brackets from URIs, e.g.:
    <https://omim.org/entry/100050> --> https://omim.org/entry/100050"""
    str_input = isinstance(uris, str)
    uris = [uris] if str_input else uris
    uris2 = []
    for x in uris:
        x = x[1:] if x.startswith('<') else x
        x = x[:-1] if x.endswith('>') else x
        uris2.append(x)
    return uris2[0] if str_input else uris2


def get_mondo_term_ids(mondo_terms_path: str, slurp_id_map: Dict[str, str]) -> Set[int]:
    """From path to file of mondo terms, get set of Mondo IDs as integers.
    # todo: Consider using `curie_list` package, though needing another prefix_map only for this seems even less optimal
    """
    # Get mondo IDs from Mondo
    mondo_base_uri = 'http://purl.obolibrary.org/obo/MONDO_'
    mondo_termlist_df = pd.read_csv(mondo_terms_path, comment='#', sep='\t')
    mondo_term_uris: List[str] = list(mondo_termlist_df['?term'])
    mondo_term_uris = remove_angle_brackets(mondo_term_uris)
    existing_ids: Set[int] = set()
    for x in mondo_term_uris:
        if not x.startswith(mondo_base_uri):
            continue
        existing_ids.add(int(x.replace('http://purl.obolibrary.org/obo/MONDO_', '')))

    # Get interim slurp-assigned Mondo IDs
    slurp_ids: Set[int] = set([int(x.split(':')[1]) for x in slurp_id_map.values()])
    existing_ids.update(slurp_ids)

    return existing_ids


def get_owned_prefix_map(onto_config_path: str) -> PREFIX_MAP:
    """Get owned prefix_map"""
    with open(onto_config_path, 'r') as stream:
        onto_config = yaml.safe_load(stream)
    owned_prefix_map: PREFIX_MAP = onto_config['base_prefix_map']
    return owned_prefix_map


# todo: Improvement. Currently, we're returning 'owned terms', which are defined as all the terms that are listed and
#  have the proper prefix. but, we need to improve this and import the ones 'of interest'. so this should come from the
#  the terms list from mapping_status or component signature
def get_all_owned_terms(
    ontology: Union[BasicOntologyInterface, SqlImplementation, ProntoImplementation],
    owned_prefix_map: Dict[PREFIX, URI], ontology_path: str = None, mode=['term', 'uri', 'curie'][0], silent=True,
    cache_dir_path: str = '', ontology_name: str = '', filter_obsoletes=True, use_cache=False,
) -> List[Union[Term, URI, CURIE]]:
    """Get all relevant owned terms

    ontology: Haven't decided yet which implementation I'll use. Would use superclass, but they use mult inheritance.
    owned_prefix_map: All the prefixes that are 'owned' by the ontology. Keys are CURIE prefixes and values are URIs.
    mode: If 'uri', returns terms as URIs, else CURIEs if 'curie'.
    cache_path: If present, read and return cache if exists, else will write to cache.
    todo: owned_terms: if slow, can speed this up by grouping prefixes by splitting on : and filter out
    """
    if use_cache and not (cache_dir_path and ontology_name):
        raise ValueError('If using "use_cache", also need both "cache_dir_path" and "ontology_name.')
    t0 = datetime.now()
    if mode not in ['term', 'uri', 'curie']:
        raise ValueError('`_get_curies_all_owned_terms()`: `mode` must be one of "uri", "curie", or "term".')

    # Cache: read
    cache_path = os.path.join(
        cache_dir_path,
        f'migrate_owned_terms_{ontology_name}.pickle')
    if cache_path and os.path.exists(cache_path) and use_cache:
        return pickle.load(open(cache_path, 'rb'))

    # Get all terms: CURIES or URIs
    term_refs: List[Union[URI, CURIE]] = [x for x in ontology.entities(filter_obsoletes=filter_obsoletes)]

    # Get CURIES
    uri_terms_owned: List[URI] = []
    curie_terms_owned: List[CURIE] = []
    for t in term_refs:
        if t.startswith('http'):
            uri_terms_owned.append(t)
        else:
            curie_terms_owned.append(t)
    uri_terms_owned = [x for x in uri_terms_owned if any([x.startswith(y) for y in owned_prefix_map.values()])]
    curie_terms_owned = [x for x in curie_terms_owned if any([x.startswith(y) for y in owned_prefix_map.keys()])]

    uri_converter = curies.Converter.from_prefix_map(owned_prefix_map)
    # Note: These code blocks are a little redundant with each other, but probably easier to read this way.
    owned_terms: Union[List[Term], List[CURIE], List[URI]]
    if mode == 'curie':  # include all terms even if can't compress
        curie_terms_2 = []
        for uri in uri_terms_owned:
            curie = uri_converter.compress(uri)
            curie_terms_2.append(curie if curie else uri)
        owned_terms = curie_terms_owned + curie_terms_2
    elif mode == 'uri':  # include all terms even if this can't expand
        uri_terms_2 = []
        for curie in curie_terms_owned:
            uri = uri_converter.expand(curie)
            uri_terms_2.append(uri if uri else curie)
        owned_terms = uri_terms_owned + uri_terms_2
    else:  # Term
        # Get parents through SPARQL
        # - Need to pass curie_list to sparql; otherwise get: error: "Unresolved prefixed name: https:"
        query_terms = curie_terms_owned + [uri_converter.compress(x) for x in uri_terms_owned]
        direct_parents_df: pd.DataFrame = jinja_sparql(
            onto_path=ontology_path,
            jinja_path=os.path.join(PROJECT_DIR, 'src', 'sparql', 'get-terms-direct-parents.sparql.jinja2'),
            prefix_map=owned_prefix_map, use_cache=use_cache, values=' '.join(query_terms))
        direct_parents_df = direct_parents_df.applymap(uri_converter.compress)
        direct_owned_parents_map = {}
        for _index, row in direct_parents_df.iterrows():
            if row['term_id'] not in direct_owned_parents_map:
                direct_owned_parents_map[row['term_id']] = []
            if row['parent_id'] and any([row['parent_id'].startswith(x) for x in owned_prefix_map.keys()]):
                direct_owned_parents_map[row['term_id']].append(row['parent_id'])

        # Converting to curie_list for the purpose of lookup in above map
        uri_terms_owned2 = []
        curie_terms_owned2 = curie_terms_owned
        for uri in uri_terms_owned:
            curie = uri_converter.compress(uri)
            if curie == uri:
                uri_terms_owned2.append(uri)
            else:
                curie_terms_owned2.append(curie)

        # Create Term objects
        owned_terms: List[Term] = []
        for uri in uri_terms_owned2:
            owned_terms.append(Term(uri=uri, owned_prefix_map=owned_prefix_map, ontology=ontology,
                                    direct_owned_parent_curies=direct_owned_parents_map.get(uri, [])))
        for curie in curie_terms_owned2:
            owned_terms.append(Term(curie=curie, owned_prefix_map=owned_prefix_map, ontology=ontology,
                                    direct_owned_parent_curies=direct_owned_parents_map.get(curie, [])))

    t1 = datetime.now()
    # Cache: write
    if cache_path and use_cache:
        with open(cache_path, 'wb') as f:
            pickle.dump(owned_terms, f, protocol=pickle.HIGHEST_PROTOCOL)
    if not silent:
        # ~21 sec: not sure if it's how I'm using OAK/curie_list, or the libs themselves.
        print('Completed compilation of all terms in x seconds: ', (t1 - t0).seconds)

    return owned_terms


# Note: More performant to fetch all parents in batch, which is how it's being done in slurp right now
# noinspection PyUnusedLocal
def _get_direct_owned_parent_uris(
    ontology: ProntoImplementation, owned_prefix_map: Dict[PREFIX, URI], curie: CURIE
) -> List[URI]:
    """Get URIs of direct parents of a class. Only returns parents that are 'owned' by the ontology.

    ontology: Haven't decided yet which implementation I'll use. Would use superclass, but they use mult inheritance.
    owned_prefix_map: All the prefixes that are 'owned' by the ontology. Keys are CURIE prefixes and values are URIs.

    todo #1: When OAK (ProntoImpleemntation or SqlImplementation) is fixed, re-implement
      - ensure that gets only direct is_a parents, not further ancestors
    """
    # These vars are here for stability reasons, just in case I get CURIES where I expect URIs or vice versa.
    subclass_preds = [x + 'subClassOf' for x in ['rdfs:', 'http://www.w3.org/2000/01/rdf-schema#']]
    owned_prefixes = set(owned_prefix_map.keys())
    uri_converter = curies.Converter.from_prefix_map(owned_prefix_map)

    direct_owned_parent_uris: List[URI] = []
    # rels1: List[CURIE] = ontology.hierararchical_parents(curie)
    # resl2: List[CURIE] = ontology.outgoing_relationship_map(curie).get('rdfs:subClassOf', [])
    # rels: List[TRIPLE] = [x for x in ontology.relationships(subjects=[curie])]
    # for rel in rels:
    #     subject, predicate, obj = rel
    #     object_curie: CURIE = uri_converter.compress(obj) if obj.startswith('http') else obj
    #     if predicate in subclass_preds and object_curie.split(':')[0] in owned_prefixes:
    #         subject_uri: URI = subject if subject.startswith('http') else uri_converter.expand(subject)
    #         direct_owned_parent_uris.append(subject_uri)
    # direct_owned_parent_uris = [x for x in direct_owned_parent_uris if x]

    return direct_owned_parent_uris


def get_excluded_terms(path) -> Set[CURIE]:
    """From path to a simple line break delimited text file with no header, get list of terms that are excluded from
    inclusion into Mondo."""
    try:
        return set(pd.read_csv(path, header=None)[0])
    except EmptyDataError:  # empty file
        return set()


# noinspection DuplicatedCode
def jinja_sparql(
    onto_path: str, jinja_path: str, prefix_map: Dict[str, str] = None, use_cache=False, verbose=False, **kwargs
) -> pd.DataFrame:
    """Run jinja on sparql"""
    prefix_sparql_strings = [f'prefix {k}: <{v}>' for k, v in prefix_map.items()] if prefix_map else None

    # Instantiate template
    with open(jinja_path, 'r') as file:
        template_str = file.read()
    template_obj = Template(template_str)
    # todo: hard-coded to 'prefixes' ok?
    instantiated_str = template_obj.render({**kwargs, **{'prefixes': prefix_sparql_strings}}) if prefix_map \
        else template_obj.render(**kwargs)

    # Basic vars
    query_template_filename = os.path.basename(jinja_path).replace('.jinja2', '').replace('.sparql', '')
    # noinspection DuplicatedCode
    onto_filename = os.path.basename(onto_path)
    results_dirname = onto_filename.replace('/', '-').replace('.', '-')
    results_dirname = results_dirname + '__' + query_template_filename.replace('.', '-')
    # todo: eventually use oak, or have all the existing funcs like this use this general one in utils.py
    # noinspection DuplicatedCode
    results_dirpath = os.path.join(CACHE_DIR, 'robot', results_dirname)
    results_filename = 'results.csv'
    command_save_filename = 'command.sh'
    results_path = os.path.join(results_dirpath, results_filename)
    command_save_path = os.path.join(results_dirpath, command_save_filename)
    instantiated_query_path = os.path.join(results_dirpath, 'query.sparql')
    command_str = f'robot query --input {onto_path} --query {instantiated_query_path} {results_path}'

    # Cache and run
    # - If return from cache, empties existing cache before running
    os.makedirs(results_dirpath, exist_ok=True)
    if not (os.path.exists(results_path) and use_cache):
        if os.path.exists(results_path):
            os.remove(results_path)
        with open(instantiated_query_path, 'w') as f:
            f.write(instantiated_str)
        with open(command_save_path, 'w') as f:
            f.write(command_str)
        try:
            result = subprocess.run(command_str.split(), capture_output=True, text=True)
        except FileNotFoundError as e:
            if 'robot' in str(e):
                # joeflack4 2023/04/25: Suddenly my PATH is wrong. Could be virtualenvwrapper+PyCharm issue.
                command_str = command_str.replace('robot query', '/usr/local/bin/robot query')
                result = subprocess.run(command_str.split(), capture_output=True, text=True)
            else:
                raise e
        stderr, stdout = result.stderr, result.stdout
        if verbose:
            print(stdout)
            print(stderr, file=sys.stderr)

    # Read results and return
    try:
        df = pd.read_csv(results_path).fillna('')
    except pd.errors.EmptyDataError:
        # remove: so that it doesn't read this from cache, though it could be that there were really no results.
        os.remove(results_path)
        # could also do `except pd.errors.EmptyDataError as err`, `raise err` or give option for this as a param to func
        # raise RuntimeError('No results found.')
        df = pd.DataFrame()

    return df


def get_labels(
    onto_path: str, curie_list: List[CURIE] = None, uri_list: List[URI] = None, prefix_map: Dict[str, str] = None,
    use_cache=False
) -> List[Union[str, None]]:
    """Get labels for all terms within the given ontology

    If label not found, returns None at the given index.

    todo's
      - There should not be duplicates. I think some of these terms have multiple labels. should address this.
    """
    if curie_list and uri_list:
        raise ValueError('Must provide either curie_list or uri_list, not both.')
    elif curie_list and not prefix_map:
        raise ValueError('Must provide prefix_map if providing curie_list.')
    values = curie_list if curie_list else uri_list
    df: pd.DataFrame = jinja_sparql(
        onto_path=onto_path, jinja_path=os.path.join(SPARQL_DIR, 'get-labels.sparql.jinja2'), prefix_map=prefix_map,
        use_cache=use_cache, values=' '.join(values))
    df = df.drop_duplicates(subset=['term_id'])
    return list(df['label'])


def get_converter(onto_config_path: Union[str, Path]) -> curies.Converter:
    """Get a prefix/URI prefix Converter."""
    with open(onto_config_path, 'r') as stream:
        onto_config = yaml.safe_load(stream)
        prefix_map: Dict[str, str] = onto_config['base_prefix_map']
        converter = curies.Converter.from_prefix_map(prefix_map)
    return converter
