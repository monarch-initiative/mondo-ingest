"""Takes in the full ontology and the exclusions tsv and extracts a simple list of terms from it.
Outputs two files:
1. a simple list of terms (config/ONTO_NAME_term_exclusions.txt)
2. a simple two column file with the term_id and the exclusion reason

# Resources
- GitHub issue: https://github.com/monarch-initiative/mondo-ingest/issues/22
- ICD10CM exclusions, online: https://docs.google.com/spreadsheets/d/1cZPUReTl34Vu2a03tm2921ehARiIpp4fjeQfS27XzKA/edit#gid=1119821904
- Ophanet/ORDO exclusions, online: https://docs.google.com/spreadsheets/d/16ftBJ8mYqEvSEVNi1tGxIlDfL88vYrs7tSUjSnGqrBw/edit#gid=0

TODO's
  - todo: Do we need to worry about edge case where exclusion table is empty? (e.g. we include such a table for all
     ontologies, but there exists 1 where we don't exclude anything.
  - todo: later: see below: #x1: regex results: would be good to filter out by IRI or prefix that is not from source
     ontology, but how to determine the appropriate prefix just based on the 2 file params, but could have edge cases.
  - todo: later: see below: #x2
  - todo: later: see below: #x3
  - todo: later: see below: #x4: Switch from SPARQL to OAK. (SqliteImpl() is faster than SparqlWrapper (which uses rdflib)
  - todo: later: When constructing exclusion TSV: bug: ICD10CM:C7A-C7A reported as term, but should be ICD10CM:C7A
  - todo: later: QA: possible conflicts in icd10cm_exclusions.tsv: Add a check to raise an error in event of a parent
     class having `True` for `exclude_children`, but the child class has `False`.
"""
import os
import subprocess
from argparse import ArgumentParser
from typing import Dict, List, Union

from jinja2 import Template
import pandas as pd


# Vars
# # Config
CONFIG = {
    'use_cache': False,
    'include_superclass': False,  # is this the correct name for what this does: * property path qualifier
    'save': True,  # save dataframes to disk
    'regex_prefix': 'REGEX:'  # used to know which rows in exclusion TSVs are regex pattern searches
}

# # Static
THIS_SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
SCRIPTS_DIR = os.path.join(THIS_SCRIPT_DIR, '..')
PROJECT_DIR = os.path.join(SCRIPTS_DIR, '..')
ONTOLOGY_DIR = os.path.join(PROJECT_DIR, 'src', 'ontology')
TEMP_DIR = os.path.join(ONTOLOGY_DIR, 'tmp')
CACHE_DIR = TEMP_DIR
CONFIG_DIR = os.path.join(ONTOLOGY_DIR, 'config')
SPARQL_DIR = os.path.join(PROJECT_DIR, 'sparql')
SPARQL_CHILD_INCLUSION_PATH = os.path.join(SPARQL_DIR, 'get-terms-children.sparql.jinja2')
SPARQL_TERM_REGEX_PATH = os.path.join(SPARQL_DIR, 'get-terms-by-regex.sparql.jinja2')

# Functions
# TODO: use: https://bioregistry.readthedocs.io/en/latest/api/bioregistry.curie_from_iri.html?highlight=get_curie#bioregistry.curie_from_iri
def uri_to_curie(uri: str) -> str:
    """Takes an ontological URI and returns a CURIE. Works on the following patterns:
    - http://.../PREFIX/CODE
    - http://.../PREFIX_CODE"""
    uri_list: List[str] = uri.split('/')
    end_bit = uri_list[-1]
    if '_' in end_bit:
        curie = end_bit.replace('_', ':')
    else:
        curie = uri_list[-2] + ':' + end_bit
    return curie


# todo: later #x2: terms vs regexp: this would be better as a class or done some other way probably
# todo: later #x3: could be nice to add param to auto-do uri_to_curie()
def sparql_jinja2_robot_query(
    query_template_path: str, onto_path: str, use_cache=CONFIG['use_cache'],
    include_superclass=CONFIG['include_superclass'], cache_suffix: str = None,
    terms: List[str] = None,
    regexp: str = None
) -> pd.DataFrame:
    """Query ontology using SPARQL query file
    include_superclass: See: # https://www.w3.org/TR/sparql11-query/#propertypaths
    cache_suffix: Caches are named using the input ontology and SPARQL files. However, it can be the case that
      there are two different queries which use these same files, but have other differences. This param is used
      to distinguish between such cases.
    """
    # Basic vars
    query_template_filename = os.path.basename(query_template_path)
    onto_filename = os.path.basename(onto_path)
    results_dirname = onto_filename.replace('/', '-').replace('.', '-') + \
        '__' + query_template_filename.replace('.', '-')
    if cache_suffix:
        results_dirname = results_dirname + '__' + cache_suffix
    results_dirpath = os.path.join(CACHE_DIR, 'robot', results_dirname)
    results_filename = 'results.csv'
    command_save_filename = 'command.sh'
    results_path = os.path.join(results_dirpath, results_filename)
    command_save_path = os.path.join(results_dirpath, command_save_filename)
    instantiated_query_path = os.path.join(results_dirpath, 'query.sparql')
    command_str = f'robot query --input {onto_path} --query {instantiated_query_path} {results_path}'

    # Instantiate template
    with open(query_template_path, 'r') as f:
        template_str = f.read()
    template_obj = Template(template_str)
    if not terms and not regexp:
        raise RuntimeError('sparql_jinja2_robot_query: Must pass either `terms` or `regexp`.')
    elif terms and regexp:
        raise RuntimeError('sparql_jinja2_robot_query: Must pass only 1: `terms` or `regexp`.')
    elif terms:
        instantiated_str = template_obj.render(
            property_path_qualifier='*' if include_superclass else '+',
            values=' '.join(terms))
    elif regexp:
        instantiated_str = template_obj.render(regexp=regexp)

    # Cache and run
    os.makedirs(results_dirpath, exist_ok=True)
    if not (os.path.exists(results_path) and use_cache):
        with open(instantiated_query_path, 'w') as f:
            # noinspection PyUnboundLocalVariable
            f.write(instantiated_str)
        with open(command_save_path, 'w') as f:
            f.write(command_str)
        subprocess.run(command_str.split())

    # Read results and return
    try:
        df = pd.read_csv(results_path).fillna('')
    except pd.errors.EmptyDataError:
        # remove: so that it doesn't read this from cache, though it could be that there were really no results.
        os.remove(results_path)
        # could also do `except pd.errors.EmptyDataError as err`, `raise err` or give option for this as a param to func
        df = pd.DataFrame()  # could also return None

    return df


def expand_ontological_exclusions(
    onto_path: str, exclusions_df: pd.DataFrame, cache_suffix: str = None,
    export_fields=['term_id', 'exclusion_reason'], uri_fields=['term_id', 'child_id']
) -> pd.DataFrame:
    """Using an ontology file and an exclusions file, query and get return an extensional list of exclusions.
    cache_suffix: Used by and explained in sparql_jinja2_robot_query()."""
    # Variable names: kids0=Children excluded; kids1=Children included
    df_kids1 = exclusions_df[exclusions_df['exclude_children'] == False]
    df_kids0 = exclusions_df[exclusions_df['exclude_children'] == True]
    terms_kids1: List[str] = list(set(df_kids1['term_id']))  # QA: set() removes any duplicates
    df_kids1_results: pd.DataFrame = sparql_jinja2_robot_query(
        terms=terms_kids1,
        query_template_path=SPARQL_CHILD_INCLUSION_PATH,
        onto_path=onto_path,
        cache_suffix=cache_suffix)

    # Massage results
    # # Convert URI back to prefix
    for fld in uri_fields:
        df_kids1_results[fld] = df_kids1_results[fld].apply(uri_to_curie)
    # # JOIN: To get exclusion_reason
    df_kids1_results2 = pd.merge(df_kids1_results, exclusions_df, how='left', on='term_id').fillna('')
    # # Drop parent term data
    df_kids1_results2 = df_kids1_results2[['child_id', 'exclusion_reason']]
    # # Rename child fields as they are now top-level terms
    df_kids1_results2 = df_kids1_results2.rename(columns={'child_id': 'term_id'})
    # # Drop unneeded fields
    df_kids0 = df_kids0[export_fields]
    df_kids1_results2 = df_kids1_results2[export_fields]

    # CONCAT: Combine term child results w/ terms where children were excluded
    df_results = pd.concat([df_kids0, df_kids1_results2]).fillna('')

    return df_results


def run(
    onto_path: str, exclusions_path: str, relevant_signature_path: str, onto_name: str, save=CONFIG['save']
) -> Union[Dict[str, pd.DataFrame], None]:
    """Run"""
    # Vars
    df_explicit_results = None
    df_regex_results = None
    exclusion_fields = ['exclusion_reason', 'exclude_children']
    sep = '\t' if exclusions_path.endswith('.tsv') else ',' if exclusions_path.endswith('.csv') else ''
    df_results_path = os.path.join(CONFIG_DIR, f'{onto_name}_exclusion_reasons.robot.template.tsv')
    df_results_simple_path = os.path.join(CONFIG_DIR, f'{onto_name}_term_exclusions.txt')

    # Prepare data
    df = pd.read_csv(exclusions_path, sep=sep).fillna('')
    df['term_id'] = df['term_id'].apply(lambda x: x.strip())
    if len(df) == 0:
        return None

    # - Split into two: 1 with regexp patterns, and 1 with explicit term_id
    df_regex = df[df['term_label'].str.startswith(CONFIG['regex_prefix'])]
    df_explicit = df.filter(items=set(df.index) - set(df_regex.index), axis=0)

    # Query 1: on explicit term_id
    if len(df_explicit) > 0:
        df_explicit_results = expand_ontological_exclusions(onto_path, df_explicit, cache_suffix='1')

    # Query 2: on regex pattern
    # todo: later: #x4: use OAK: When ready, can use maybe use xxxImplementation().basic_search(regex_pattern)
    #  ...where xxxImplementation is the one recommended in one of these discussions:
    #  https://github.com/INCATools/ontology-access-kit/issues/134
    #  https://incatools.github.io/ontology-access-kit/intro/tutorial02.html
    search_results: List[pd.DataFrame] = []
    for index, row in df_regex.iterrows():
        regex_pattern = row['term_label'].replace(CONFIG['regex_prefix'], '')
        search_result_df: pd.DataFrame = sparql_jinja2_robot_query(
            onto_path=onto_path,
            query_template_path=SPARQL_TERM_REGEX_PATH,
            regexp=regex_pattern,
            cache_suffix=f'r{str(index)}')
        if len(search_result_df) > 0:
            search_result_df['term_id'] = search_result_df['term_id'].apply(uri_to_curie)
            # todo later: #x1: would be good to filter out by IRI or prefix that is not from source ontology
            #  ...This can be done (a) in Python, or (b) in SPARQL, if using that.
            # search_result_df = search_result_df[search_result_df['term_id'].str.startswith(prefix)]
            for fld in exclusion_fields:
                search_result_df[fld] = row[fld]
            search_results.append(search_result_df)
    if search_results:
        # - Combine each of the regex search results
        df_regex_pre_results = pd.concat(search_results)
        # - Query for children
        df_regex_results = expand_ontological_exclusions(onto_path, df_regex_pre_results, cache_suffix='2')

    # Combine & massage
    # - CONCAT: Combine results of all queries
    df_results = pd.concat([x for x in [df_explicit_results, df_regex_results] if x is not None])
    # - Drop duplicates: As there is likely to be overlap between (a) explicitly listed terms, and (b) Regex-selected
    # terms. It is also theoretically possible that there may be some cases where there is a different exclusion_reason
    # for a term that is within both (a) and (b). In that case, duplicate terms will remain, showing both reasons.
    df_results = df_results.drop_duplicates()
    # - Filter: terms not in relevant_signature.txt, e.g. terms actually in ICD / that we care about
    df_relevant_terms = pd.read_csv(relevant_signature_path).fillna('')
    df_relevant_terms['term'] = df_relevant_terms['term'].apply(uri_to_curie)
    relevant_terms: List[str] = list(set(df_relevant_terms['term']))
    df_results = df_results[df_results['term_id'].isin(relevant_terms)]
    # - df_results_simple: Simpler dataframe which is easier to use downstream for other purposes
    df_results_simple = df_results[['term_id']]
    # - df_results: Add special meta rows
    # todo: Utilize `has_exclusion_reason`, pending modno#5177 completion:
    #  https://github.com/monarch-initiative/mondo/issues/5177#issue-1304502840
    df_added_row = pd.DataFrame([{'term_id': 'ID', 'exclusion_reason': 'AI rdfs:seeAlso'}])
    df_results = pd.concat([df_added_row, df_results])

    # Save & return
    if save:
        df_results.to_csv(df_results_path, sep='\t', index=False)
        df_results_simple.to_csv(df_results_simple_path, index=False, header=False)

    return {
        df_results_path: df_results,
        df_results_simple_path: df_results_simple
    }


def cli_get_parser() -> ArgumentParser:
    """Add required fields to parser."""
    package_description = \
        'Takes in a full ontology and an exclusions TSV and extracts a simple list of terms.\n'\
        'Outputs two files:\n'\
        '1. a simple list of terms (config/ONTO_NAME_term_exclusions.txt)\n'\
        '2. a simple two column file with the term_id and the exclusion reason\n'
    parser = ArgumentParser(description=package_description)

    parser.add_argument(
        '-o', '--onto-path',
        help='Path to the ontology file to query.')
    parser.add_argument(
        '-e', '--exclusions-path',
        help='Path to a TSV which should have the following fields: `term_id` (str), `term_label` (str), '
             '`exclusion_reason` (str), and `exclude_children` (bool).')
    parser.add_argument(
        '-s', '--relevant-signature-path',
        help='Path to a "relevant signature" file, which contains a list of all of the terms in an ontology that are '
             'of that ontology itself and relevant, as opposed to, for example, classes from another ontology that'
             ' happen to be in the ontological file passed in `--onto-path`.')
    parser.add_argument(
        '-n', '--onto-name',
        help='Name of the ontology.')

    return parser


def cli_validate(d: Dict) -> Dict:
    """Validate CLI args. Also updates these args if/as necessary"""
    # File paths: Relative->Absolute
    # - Likely that they will be passed as relative paths with respect to ONTOLOGY_DIR.
    # - This checks for that and updates to absolute path if necessary.
    path_arg_keys = ['exclusions_path', 'onto_path']
    for k in path_arg_keys:
        path = d[k]
        if not os.path.exists(path):
            d[k] = os.path.join(ONTOLOGY_DIR, path)

    # Check if exists
    for k in path_arg_keys:
        if not os.path.exists(d[k]):
            raise FileNotFoundError(d[k])

    return d


def cli() -> Dict[str, pd.DataFrame]:
    """Command line interface."""
    parser = cli_get_parser()
    kwargs = parser.parse_args()
    kwargs_dict: Dict = vars(kwargs)
    kwargs_dict = cli_validate(kwargs_dict)
    return run(**kwargs_dict)


# Execution
if __name__ == '__main__':
    cli()
