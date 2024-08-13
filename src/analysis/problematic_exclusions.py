"""Excluded terms xrefed-in Mondo

Resources
- GitHub issue: https://github.com/monarch-initiative/mondo-ingest/issues/31
- GitHub PR: https://github.com/monarch-initiative/mondo-ingest/pull/35
"""
import os
import subprocess
from argparse import ArgumentParser
from typing import Dict

import curies
import yaml
import pandas as pd
from jinja2 import Template


# Vars
# # Static
THIS_SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
ANALYSIS_DIR = THIS_SCRIPT_DIR
PROJECT_DIR = os.path.join(ANALYSIS_DIR, '..', '..')
ONTOLOGY_DIR = os.path.join(PROJECT_DIR, 'src', 'ontology')
TEMP_DIR = os.path.join(ONTOLOGY_DIR, 'tmp')
CACHE_DIR = TEMP_DIR
REPORTS_DIR = os.path.join(ONTOLOGY_DIR, 'reports')
METADATA_DIR = os.path.join(ONTOLOGY_DIR, 'metadata')
MIRROR_DIR = os.path.join(ONTOLOGY_DIR, 'mirror')
MAPPINGS_DIR = TEMP_DIR
SIGNATURE_FILES_DIR = REPORTS_DIR
OUTDIR = REPORTS_DIR
SPARQL_STR_GET_LABELS = """
{% for sparql_prefix_line in prefixes %}{{ sparql_prefix_line }}{% endfor %}
prefix owl:  <http://www.w3.org/2002/07/owl#>
prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>

select ?term_id ?term_label where {
    VALUES ?term_id { {{values}} }
    ?term_id a owl:Class;
      rdfs:label ?term_label .
}"""
# # Config
CONFIG = {
    'use_cache': False,
    'save': True,  # save dataframes to disk
}


# Functions
def load_and_format_tsv(path: str, prefix_map: Dict[str, str]) -> pd.DataFrame:
    """Load and format"""
    old_term_header = '?term'
    # Read
    df = pd.read_csv(path, sep='\t').fillna('')
    # Filter: https://stackoverflow.com/
    # questions/55941100/how-to-filter-pandas-dataframe-rows-which-contains-any-string-from-a-list
    permissible_uris = list(prefix_map.values())
    df2 = df[df[old_term_header].str.contains('|'.join(permissible_uris)).groupby(level=0).any()]
    # Format
    # pd.options.mode.chained_assignment: `SettingWithCopyWarning` probably a false positive, so temp disabling warning.
    # - SettingWithCopyWarning: A value is trying to be set on a copy of a slice from a DataFrame. Try using
    # .loc[row_indexer,col_indexer] = value instead
    # - See: https://stackoverflow.com/questions/20625582/how-to-deal-with-settingwithcopywarning-in-pandas
    pd.options.mode.chained_assignment = None  # default='warn'
    df2[old_term_header] = df2[old_term_header].str.strip()
    # todo: when fixed upstream, remove this angle bracket removal operation
    df2[old_term_header] = df2[old_term_header].apply(lambda uri: uri.replace('<', '').replace('>', ''))
    uri_converter = curies.Converter.from_prefix_map(prefix_map)
    df2[old_term_header] = df2[old_term_header].apply(uri_converter.compress)
    pd.options.mode.chained_assignment = 'warn'  # default='warn'
    df2 = df2.rename({old_term_header: 'term_id'})
    return df2


# todo: refactor to use utils.py get_labels()
# todo: In the future, refactor to use OAK.
# noinspection DuplicatedCode
def populate_labels(
    df: pd.DataFrame, onto_path: str, prefix_map: Dict[str, str], template_str=SPARQL_STR_GET_LABELS,
    use_cache=CONFIG['use_cache']
) -> pd.DataFrame:
    """Get labels for terms

    # todo: use this when OAK ready
    # from oaklib.resource import OntologyResource
    # from oaklib.implementations.sqldb.sql_implementation import SqlImplementation
    # # https://incatools.github.io/ontology-access-kit/introduction.html#basic-python-example
    # onto_path = os.path.join(MIRROR_DIR, f'{o}.owl')
    # if not os.path.exists(onto_path):  # temp until can reliably get all ontologies as .owl in mirror/
    #     onto_path = onto_path.replace('.owl', '.ttl')
    # resource = OntologyResource(slug=onto_path, local=True)
    # si = SqlImplementation(resource)
    # labels = [x for x in si.get_labels_for_curies(list(df_i['term_id']))]
    # labels = []
    # for curie in list(df_i['term_id']):
    #     label = si.get_label_by_curie(curie)
    #     labels.append(label)
    """
    # Get appropriate terms
    # idealy would use vars from before
    term_id_field = 'term_id'
    term_label_field = 'term_label'
    terms = list(df[term_id_field])
    terms = [x for x in terms if any([x.startswith(y) for y in prefix_map.keys()])]

    # Instantiate template
    prefix_sparql_strings = [f'prefix {k}: <{v}>\n' for k, v in prefix_map.items()]
    template_obj = Template(template_str)
    instantiated_str = template_obj.render(
        prefixes=prefix_sparql_strings,
        values=' '.join(terms))

    # Basic vars
    query_template_filename = 'get-labels'
    onto_filename = os.path.basename(onto_path)
    results_dirname = onto_filename.replace('/', '-').replace('.', '-')
    results_dirname = results_dirname + '__' + query_template_filename.replace('.', '-')
    # noinspection DuplicatedCode
    results_dirpath = os.path.join(CACHE_DIR, 'robot', results_dirname)
    results_filename = 'results.csv'
    command_save_filename = 'command.sh'
    results_path = os.path.join(results_dirpath, results_filename)
    command_save_path = os.path.join(results_dirpath, command_save_filename)
    instantiated_query_path = os.path.join(results_dirpath, 'query.sparql')
    command_str = f'robot query --input {onto_path} --query {instantiated_query_path} {results_path}'

    # Cache and run
    os.makedirs(results_dirpath, exist_ok=True)
    if not (os.path.exists(results_path) and use_cache):
        with open(instantiated_query_path, 'w') as f:
            # noinspection PyUnboundLocalVariable
            f.write(instantiated_str)
        with open(command_save_path, 'w') as f:
            f.write(command_str)
        subprocess.run(command_str.split(), capture_output=True, text=True)

    # Read results and return
    try:
        df2 = pd.read_csv(results_path).fillna('')
    except pd.errors.EmptyDataError:
        # remove: so that it doesn't read this from cache, though it could be that there were really no results.
        os.remove(results_path)
        # could also do `except pd.errors.EmptyDataError as err`, `raise err` or give option for this as a param to func
        raise RuntimeError('No results found when trying to get labels for terms.')

    # Massage
    # todo: suboptimal that I have to do this a second time just so i can join results
    uri_converter = curies.Converter.from_prefix_map(prefix_map)
    df2[term_id_field] = df2[term_id_field].apply(uri_converter.compress)
    term_label_map = {}
    for _i, row in df2.iterrows():
        term_label_map[row[term_id_field]] = row[term_label_field]

    # JOIN results
    df_joined = pd.DataFrame()
    if len(df) > 0:
        rows = []
        for _i, row in df.iterrows():
            d_row = dict(row)
            d_row[term_label_field] = term_label_map.get(d_row[term_id_field], '')
            rows.append(d_row)
        df_joined = pd.DataFrame(rows)

    return df_joined


def problematic_exclusions(
    onto_path: str, onto_config_path: str, component_signature_path: str, mirror_signature_path: str,
    mondo_mappings_path: str, outpath: str, save=CONFIG['save']
) -> Dict[str, pd.DataFrame]:
    """For a given ontology corresponding to the files passed, find excluded terms that still exist in Mondo xrefs"""
    term_id_field = 'term_id'
    term_label_field = 'term_label'
    mirror_field = '1_in_mirror_tsv'
    component_field = '2_in_component_tsv'
    mappings_field = '3_in_mondo_xrefs'
    analytical_field = 'in1_notIn2_in3'
    summary_count_field = 'n_in1_notIn2_in3'
    summary_pct_field = 'pct_in1_notIn2_in3__over_in1'
    outpath_xref_summary = outpath.replace('.tsv', '_summary.tsv')
    mondo_mappings_df = pd.read_csv(mondo_mappings_path, sep='\t', comment='#').fillna('')
    mondo_mappings_set = set(mondo_mappings_df['object_id'])

    # Prefixes
    with open(onto_config_path, 'r') as stream:
        onto_config = yaml.safe_load(stream)
    prefix_uri_map = onto_config['base_prefix_map']

    # Load datasets
    mirror_df = load_and_format_tsv(path=mirror_signature_path, prefix_map=prefix_uri_map)
    component_df = load_and_format_tsv(path=component_signature_path, prefix_map=prefix_uri_map)
    # todo?: maybe using column '?term' is better since could be more columns w/ diff order, but I figured it was
    #  ...more likely that the column name '?term' could change, so I simply picked out the assumed only column [0].
    mirror_set = set(mirror_df[list(mirror_df.columns)[0]])
    component_set = set(component_df[list(component_df.columns)[0]])

    # Determine set membership
    term_appearances = {}
    for term in mirror_set:
        term_appearances[term] = {
            term_id_field: term, mirror_field: True, component_field: False, mappings_field: False}
    for term in component_set:
        if term not in term_appearances:
            term_appearances[term] = {term_id_field: term, mirror_field: False, mappings_field: False}
        term_appearances[term][component_field] = True
    for term in mondo_mappings_set:
        if term not in term_appearances:
            term_appearances[term] = {term_id_field: term, mirror_field: False, component_field: False}
        term_appearances[term][mappings_field] = True
    df = pd.DataFrame(list(term_appearances.values()))

    # Analyze
    # todo: later: might be faster to initialize `term_appearances` above for loop, `copy()` it w/in loop, and do
    #  some analysis possibly after for loop.
    df[analytical_field] = df.apply(
        lambda row:
        (row[mirror_field] == True) and
        (row[component_field] == False) and
        (row[mappings_field] == True), axis=1)

    # Filter
    # todo?: later: faster if this first filter appeared before 'analyze', but probably not by much
    # - remove any terms that are not 'owned' by the ontology
    df['prefix'] = df[term_id_field].apply(lambda x: x.split(':')[0])
    df = df[df['prefix'].isin(list(prefix_uri_map.keys()))]
    df.drop('prefix', inplace=True, axis=1)
    # - leave only the problematic exclusions
    df = df[df[analytical_field] == True]

    # Add labels
    if len(df) > 0:
        df = populate_labels(df=df, onto_path=onto_path, prefix_map=prefix_uri_map)
    else:
        df[term_label_field] = ''

    # Format
    df = df[[term_id_field, term_label_field, mirror_field, component_field, mappings_field, analytical_field]]
    df = df.sort_values(
        [term_label_field, analytical_field, term_id_field, mirror_field, component_field, mappings_field],
        ascending=[False, True, False, False, False, False])

    # Create summary
    summary_count = len(df[df[analytical_field] == True])
    df_summary = pd.DataFrame([{
        summary_count_field: summary_count,
        summary_pct_field: round(summary_count / len(mirror_set), 4) if summary_count > 0 else 0
    }])
    df_summary = df_summary.sort_values([summary_count_field], ascending=[False])

    # Save & return
    if save:
        df.to_csv(outpath, sep='\t', index=False)
        df_summary.to_csv(outpath_xref_summary, sep='\t', index=False)

    return {outpath: df, outpath_xref_summary: df_summary}


def cli() -> Dict[str, pd.DataFrame]:
    """Command line interface."""
    package_description = \
        'Determine which terms outside the term scope of the Mondo source alignment are xrefed in Mondo.'
    parser = ArgumentParser(description=package_description)
    parser.add_argument('-O', '--onto-path', required=True, help='Optional. Path to the ontology file to query.')
    parser.add_argument('-m', '--mondo-mappings-path', required=True, help='Path to `mondo.sssom.tsv`.')
    parser.add_argument(
        '-c', '--onto-config-path', required=True,
        help='Path to a config `.yml` for the ontology which contains a `base_prefix_map` which contains a '
             'list of prefixes owned by the ontology. Used to filter out terms.')
    parser.add_argument(
        '-cs', '--component-signature-path', required=True,
        help='Path to a "component signature" file, which contains a list of class URIs from Mondo\'s '
             '"alignment module" for the ontology, an alignment module being defined as the list of classes we care '
             'about (e.g. all diseases).')
    parser.add_argument(
        '-ms', '--mirror-signature-path', required=True,
        help='Path to a "mirror signature" file, which contains a list of class URIs from the unaltered '
             'source ontology.')
    parser.add_argument(
        '-o', '--outpath', required=True,
        help='Path for output file for list of excluded terms that have cross-references in Mondo.')
    d: Dict = vars(parser.parse_args())
    return problematic_exclusions(**d)


# Execution
if __name__ == '__main__':
    cli()
