"""Takes in the full ontology and the exclusions tsv and extracts a simple list of terms from it.
Outputs two files:
1. a simple list of terms (config/ONTO_NAME_term_exclusions.txt)
2. a simple two column file with the term_id and the exclusion reason

# Resources
- GitHub issue: https://github.com/monarch-initiative/mondo-ingest/issues/22
- ICD10CM exclusions, online:
  https://docs.google.com/spreadsheets/d/1cZPUReTl34Vu2a03tm2921ehARiIpp4fjeQfS27XzKA/edit#gid=1119821904
- Ophanet/ORDO exclusions, online:
  https://docs.google.com/spreadsheets/d/16ftBJ8mYqEvSEVNi1tGxIlDfL88vYrs7tSUjSnGqrBw/edit#gid=0
- Mondo exclusion reasons: https://mondo.readthedocs.io/en/latest/editors-guide/exclusion-reasons/

TODO's
  - todo: later: see below: #x3
  - todo: later: see below: #x4: SPARQL to OAK. (SqliteImpl() is faster than SparqlWrapper (which uses rdflib)
  - todo: later: QA: possible conflicts in icd10cm_exclusions.tsv: Add a check to raise an error in event of a parent
     class having `True` for `exclude_children`, but the child class has `False`.
"""
import os
import subprocess
from argparse import ArgumentParser
from typing import Dict, List, Union

import yaml
import pandas as pd
from jinja2 import Template


# Vars
# # Config
CONFIG = {
    'use_cache': False,
    'save': True,  # save dataframes to disk
    'regex_prefix': 'REGEX:'  # used to know which rows in exclusion TSVs are regex pattern searches
}

# # Static
THIS_SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
SCRIPTS_DIR = THIS_SCRIPT_DIR
PROJECT_DIR = os.path.join(SCRIPTS_DIR, '..', '..')
ONTOLOGY_DIR = os.path.join(PROJECT_DIR, 'src', 'ontology')
REPORTS_DIR = os.path.join(ONTOLOGY_DIR, 'reports')
METADATA_DIR = os.path.join(ONTOLOGY_DIR, 'metadata')
TEMP_DIR = os.path.join(ONTOLOGY_DIR, 'tmp')
CACHE_DIR = TEMP_DIR
CONFIG_DIR = os.path.join(ONTOLOGY_DIR, 'config')
SPARQL_DIR = os.path.join(PROJECT_DIR, 'src', 'sparql')
SPARQL_CHILD_INCLUSION_PATH = os.path.join(SPARQL_DIR, 'get-terms-children.sparql.jinja2')
SPARQL_TERM_REGEX_PATH = os.path.join(SPARQL_DIR, 'get-terms-by-regex.sparql.jinja2')


# Functions
# TODO: evaluate https://github.com/cthoyt/curies , which likely has fully superseded new bioregistry option
#  https://github.com/biopragmatics/bioregistry/issues/480#issuecomment-1199235747
def uri_to_curie(uri: str, prefix_map: Dict[str, str]) -> str:
    """Takes an ontological URI and returns a CURIE. Works on the following patterns
    todo: eventually OAK might also have an optimal solution for this."""
    if uri.startswith('<'):
        uri = uri[1:]
    if uri.endswith('>'):
        uri = uri[:-1]
    curie = None
    for k, v in prefix_map.items():
        if uri.startswith(v):
            curie = uri.replace(v, f"{k}:")
    if not curie:
        err = f'Could not locate a suitable URI base in `prefix_map`:\n- uri: {uri}\n- prefix_map: {prefix_map}'
        raise ValueError(err)
    return curie


# todo: later #x3: could be nice to add param to auto-do uri_to_curie(), or just replace this with OAK
def sparql_jinja2_robot_query(
    query_template_path: str, onto_path: str, use_cache=CONFIG['use_cache'],
    cache_suffix: str = None, prefixes: List[str] = None, terms: List[str] = None, regexp: str = None
) -> pd.DataFrame:
    """Query ontology using SPARQL query file
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
            prefixes=prefixes,
            values=' '.join(terms))
    elif regexp:
        instantiated_str = template_obj.render(
            prefixes=prefixes,
            regexp=regexp)

    # Cache and run
    os.makedirs(results_dirpath, exist_ok=True)
    if not (os.path.exists(results_path) and use_cache):
        with open(instantiated_query_path, 'w') as f:
            # noinspection PyUnboundLocalVariable
            f.write(instantiated_str)
        with open(command_save_path, 'w') as f:
            f.write(command_str)
        result = subprocess.run(command_str.split(), capture_output=True, text=True)
        stderr, stdout = result.stderr, result.stdout
        if stderr:
            raise RuntimeError(stderr)
        elif stdout and 'error' in stdout or 'ERROR' in stdout:
            raise RuntimeError(stdout)

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
    onto_path: str, exclusions_df: pd.DataFrame, prefix_map: Dict[str, str], cache_suffix: str = None,
    export_fields=['term_id', 'exclusion_reason'], uri_fields=['term_id', 'child_id']
) -> pd.DataFrame:
    """Using an ontology file and an exclusions file, query and get return an extensional list of exclusions.
    cache_suffix: Used by and explained in sparql_jinja2_robot_query()."""
    # Variable names: kids0=Children excluded; kids1=Children included
    prefix_sparql_strings = [f'prefix {k}: <{v}>' for k, v in prefix_map.items()]
    df_kids1 = exclusions_df[exclusions_df['exclude_children'] == True]
    df_kids0 = exclusions_df[exclusions_df['exclude_children'] != True]

    # Terms w/ non-excluded children
    if len(df_kids1) > 0:
        terms_kids1: List[str] = list(set(df_kids1['term_id']))  # QA: set() removes any duplicates
        df_kids1_results_1st: pd.DataFrame = sparql_jinja2_robot_query(
            prefixes=prefix_sparql_strings,
            terms=terms_kids1,
            query_template_path=SPARQL_CHILD_INCLUSION_PATH,
            onto_path=onto_path,
            cache_suffix=cache_suffix)

        # Massage results
        # # Convert URI back to prefix
        for fld in uri_fields:
            df_kids1_results_1st[fld] = df_kids1_results_1st[fld].apply(uri_to_curie, prefix_map=prefix_map)
        # # JOIN: To get exclusion_reason
        df_kids1_results = pd.merge(df_kids1_results_1st, exclusions_df, how='left', on='term_id').fillna('')
        # # Drop parent term data
        df_kids1_results = df_kids1_results[['child_id', 'exclusion_reason']]
        # # Rename child fields as they are now top-level terms
        df_kids1_results = df_kids1_results.rename(columns={'child_id': 'term_id'})
    else:
        df_kids1_results = df_kids1  # empty, but columns needed for concat below

    # Terms w/ excluded children
    pass  # the list itself is all we need; no query necessary

    # Massage
    # - Drop unneeded fields
    df_kids0 = df_kids0[export_fields]
    df_kids1_results = df_kids1_results[export_fields]

    # CONCAT: Combine term child results w/ terms where children were excluded
    df_results = pd.concat([df_kids0, df_kids1_results]).fillna('')

    return df_results


def read_and_format_signature_file(path: str, prefix_map: Dict[str, str], return_type=['df', 'set'][0]) -> pd.DataFrame:
    """Read and format signature file"""
    df = pd.read_csv(path).fillna('')
    col = list(df.columns)[0]  # all sig files have 1 col: typically 'term' or '?term'
    term_uris = list(df[col])
    prefix_uris = list(prefix_map.values())
    relevant_terms = [term for term in term_uris if any([uri in term for uri in prefix_uris])]
    df2 = pd.DataFrame()
    if relevant_terms:
        df2 = pd.DataFrame([{'term_id': term} for term in relevant_terms])
        df2['term_id'] = df2['term_id'].apply(uri_to_curie, prefix_map=prefix_map)
    if return_type == 'set':
        df2 = set(df2['term_id']) if len(df2) > 0 else set()
    return df2


def get_non_inclusions(
    mirror_signature_path: str, component_signature_path: str, prefix_map: Dict[str, str]
) -> pd.DataFrame:
    """Get non-inclusions. """
    mirror_set = read_and_format_signature_file(mirror_signature_path, prefix_map, return_type='set')
    component_set = read_and_format_signature_file(component_signature_path, prefix_map, return_type='set')
    non_inclusions_ids = [x for x in mirror_set if x not in component_set]
    non_inclusions_rows = [{'term_id': x, 'exclusion_reason': 'MONDO:excludeNonDisease'} for x in non_inclusions_ids]

    return pd.DataFrame(non_inclusions_rows)


def expand_intensional_exclusions(
    onto_path: str, exclusions_path: str, prefix_map: Dict[str, str],
) -> pd.DataFrame:
    """Expand intensional exclusions"""
    # Vars
    df_explicit_results = pd.DataFrame()
    df_regex_results = pd.DataFrame()
    exclusion_fields = ['exclusion_reason', 'exclude_children']
    sep = '\t' if exclusions_path.endswith('.tsv') else ',' if exclusions_path.endswith('.csv') else ''
    # Prepare data
    df = pd.read_csv(exclusions_path, sep=sep).fillna('')
    df['term_id'] = df['term_id'].apply(lambda x: x.strip())

    # - Split into two: 1 with regexp patterns, and 1 with explicit term_id
    df_regex = df[df['term_label'].str.startswith(CONFIG['regex_prefix'])]
    df_explicit = df.filter(items=set(df.index) - set(df_regex.index), axis=0)

    # Query 1: on explicit term_id
    if len(df_explicit) > 0:
        df_explicit_results = expand_ontological_exclusions(
            onto_path=onto_path, exclusions_df=df_explicit, prefix_map=prefix_map,
            cache_suffix='1')

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
            search_result_df['term_id'] = search_result_df['term_id'].apply(uri_to_curie, prefix_map=prefix_map)
            for fld in exclusion_fields:
                search_result_df[fld] = row[fld]
            search_results.append(search_result_df)
    if search_results:
        # - Combine each of the regex search results
        df_regex_pre_results = pd.concat(search_results)
        # - Query for children
        df_regex_results = expand_ontological_exclusions(
            onto_path=onto_path, exclusions_df=df_regex_pre_results, cache_suffix='2', prefix_map=prefix_map)

    # Combine & massage
    # - CONCAT: Combine results of all queries
    df_results = pd.DataFrame()
    if any([len(x) > 0 for x in [df_explicit_results, df_regex_results]]):
        df_results = pd.concat([x for x in [df_explicit_results, df_regex_results] if x is not None])
    # - Drop duplicates: As there is likely to be overlap between (a) explicitly listed terms, and (b) Regex-selected
    # terms. It is also theoretically possible that there may be some cases where there is a different exclusion_reason
    # for a term that is within both (a) and (b). In that case, duplicate terms will remain, showing both reasons.
    df_results = df_results.drop_duplicates()

    return df_results


def run(
    onto_path: str, exclusions_path: str, mirror_signature_path: str, component_signature_path: str,
    config_path: str, outpath_txt: str, outpath_robot_template_tsv: str, save=CONFIG['save']
) -> Union[Dict[str, pd.DataFrame], None]:
    """Run"""
    # Prefixes
    with open(config_path, 'r') as stream:
        onto_config = yaml.safe_load(stream)
    prefix_uri_map = onto_config['prefix_map']

    # Get excluded terms
    expanded_intensional_exclusions_df = expand_intensional_exclusions(
        onto_path=onto_path, exclusions_path=exclusions_path, prefix_map=prefix_uri_map)
    non_inclusions_df = get_non_inclusions(
        mirror_signature_path=mirror_signature_path, component_signature_path=component_signature_path,
        prefix_map=prefix_uri_map)
    df_results = pd.concat([expanded_intensional_exclusions_df, non_inclusions_df])
    if len(df_results) == 0:
        df_results = pd.DataFrame()
        df_results['term_id'] = ''

    # Filter out non-owned
    owned_prefixes = list(onto_config['base_prefix_map'].keys())
    df_results['prefix'] = df_results['term_id'].apply(lambda x: x.split(':')[0])
    df_results = df_results[df_results['prefix'].isin(owned_prefixes)]
    df_results.drop('prefix', inplace=True, axis=1)

    # Sort
    if len(df_results) > 0:
        df_results = df_results.sort_values(['term_id', 'exclusion_reason'])

    # Add simplified version
    # - df_results_simple: Simpler dataframe which is easier to use downstream for other purposes
    df_results_simple = pd.DataFrame(set(df_results['term_id']))
    # - df_results: Add special meta rows
    df_added_row = pd.DataFrame([{'term_id': 'ID', 'exclusion_reason': 'AI MONDOREL:has_exclusion_reason'}])
    df_results = pd.concat([df_added_row, df_results])

    # Save & return
    if save:
        df_results.to_csv(outpath_robot_template_tsv, sep='\t', index=False)
        df_results_simple.to_csv(outpath_txt, index=False, header=False)

    return {
        outpath_robot_template_tsv: df_results,
        outpath_txt: df_results_simple
    }


def cli_validate(d: Dict) -> Dict:
    """Validate CLI args. Also updates these args if/as necessary"""
    # File paths: Relative->Absolute
    # - Likely that they will be passed as relative paths with respect to ONTOLOGY_DIR.
    # - This checks for that and updates to absolute path if necessary.
    # todo: should be an easy way to determine if a string is a path (even if no file exists there)
    path_arg_keys = [x for x in list(d.keys()) if x.endswith('path') and 'outpath' not in x]
    for k in path_arg_keys:
        path = d[k]
        if not os.path.exists(path):
            d[k] = os.path.join(ONTOLOGY_DIR, path)

    # Check if exists
    for k in path_arg_keys:
        if not os.path.exists(d[k]):
            raise FileNotFoundError(d[k])

    return d


def cli_get_parser() -> ArgumentParser:
    """Add required fields to parser."""
    package_description = \
        'Takes in a full ontology and an exclusions TSV and extracts a simple list of terms.\n'\
        'Outputs two files:\n'\
        '1. a simple list of terms (e.g. ONTO_NAME_term_exclusions.txt)\n'\
        '2. a simple two column file with the term_id and the exclusion reason (e.g. ' \
        'ONTO_NAME_exclusion_reasons.robot.template.tsv)\n'
    parser = ArgumentParser(description=package_description)

    parser.add_argument(
        '-o', '--onto-path', required=True, help='Path to the ontology file to query.')
    parser.add_argument(
        '-c', '--config-path', required=True,
        help='Path to a config `.yml` for the ontology which contains a `base_prefix_map` which contains a '
             'list of prefixes owned by the ontology. Used to filter out terms, as well as `prefix_map`, which contains'
             ' all prefixes and is used for querying.')
    parser.add_argument(
        '-e', '--exclusions-path', required=True,
        help='Path to a TSV which should have the following fields: `term_id` (str), `term_label` (str), '
             '`exclusion_reason` (str), and `exclude_children` (bool).')
    parser.add_argument(
        '-m', '--mirror-signature-path', required=True,
        help='Path to a "mirror signature" file, which contains a list of class URIs from the unaltered '
             'source ontology.')
    parser.add_argument(
        '-cs', '--component-signature-path', required=True,
        help='Path to a "component signature" file, which contains a list of class URIs from Mondo\'s '
             '"alignment module" for the ontology, an alignment module being defined as the list of classes we care '
             'about (e.g. all diseases).')
    parser.add_argument(
        '-ot', '--outpath-txt', required=True,
        help='Path to create ONTO_NAME_term_exclusions.txt.')
    parser.add_argument(
        '-or', '--outpath-robot-template-tsv', required=True,
        help='Path to create ONTO_NAME_exclusion_reasons.robot.template.tsv.')

    return parser


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
