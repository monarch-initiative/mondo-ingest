"""Excluded terms xrefed-in Mondo

Resources
- GitHub issue: https://github.com/monarch-initiative/mondo-ingest/issues/31
- GitHub PR: https://github.com/monarch-initiative/mondo-ingest/pull/35
"""
import os
from argparse import ArgumentParser
from typing import Dict, List

import pandas as pd


# Vars
# # Static
import yaml

THIS_SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
ANALYSIS_DIR = THIS_SCRIPT_DIR
PROJECT_DIR = os.path.join(ANALYSIS_DIR, '..', '..')
ONTOLOGY_DIR = os.path.join(PROJECT_DIR, 'src', 'ontology')
TEMP_DIR = os.path.join(ONTOLOGY_DIR, 'tmp')
REPORTS_DIR = os.path.join(ONTOLOGY_DIR, 'reports')
METADATA_DIR = os.path.join(ONTOLOGY_DIR, 'metadata')
MIRROR_DIR = os.path.join(ONTOLOGY_DIR, 'mirror')
MAPPINGS_DIR = TEMP_DIR
SIGNATURE_FILES_DIR = REPORTS_DIR
OUTDIR = REPORTS_DIR
OUTFILE_ARGS = {
    'excluded_terms_in_mondo.tsv': 'outpath_excluded_terms_in_mondo',
    'excluded_terms_in_mondo_xrefs.tsv': 'outpath_excluded_terms_in_mondo_xrefs'
}
# # Config
CONFIG = {
    # todo: get list from mondo config yml: (i dont see that file here, and sssom file doesnt have this. in Mondo repo?)
    'ontologies': ['icd10cm'],
    # 'ontologies': ['doid', 'icd10cm', 'icd10who', 'ncit', 'omim', 'ordo'],
    'mondo_mappings_path': os.path.join(MAPPINGS_DIR, 'mondo.sssom.tsv'),
    'config_pattern': '{}.yml',
    'component_sig_pattern': 'component_signature-{}.tsv',
    'mirror_sig_pattern': 'mirror_signature-{}.tsv',
    # outpath: summary will be saved in same dir, with _summary at end of name
    'outpath_excluded_terms_in_mondo': os.path.join(OUTDIR, 'excluded_terms_in_mondo.tsv'),
    'outpath_excluded_terms_in_mondo_xrefs': os.path.join(OUTDIR, 'excluded_terms_in_mondo_xrefs.tsv'),
    'save': True,  # save dataframes to disk
}


# Functions
# TODO: use existing: https://github.com/monarch-initiative/mondo-ingest/pull/35#discussion_r918476599
#  - needs prefix_map (temporarily unused)
#  - https://bioregistry.readthedocs.io/en/latest/api/bioregistry.curie_from_iri.html?highlight=uri_to_curie
# noinspection PyUnusedLocal
def uri_to_curie(uri: str, prefix_map: Dict[str, str]) -> str:
    """Takes an ontological URI and returns a CURIE. Works on the following patterns:
    - http://.../PREFIX/CODE
    - http://.../PREFIX_CODE"""
    uri_list: List[str] = uri.split('/')
    end_bit = uri_list[-1]
    end_bit = end_bit.replace('>', '')  # sometimes URIs are wrapped in angle brackets <>
    if '_' in end_bit:
        curie = end_bit.replace('_', ':')
    else:
        curie = uri_list[-2] + ':' + end_bit
    return curie


def _term_prefix_to_uri(term_id: str, prefix_map: Dict[str, str]):
    """Given a term w/ a prefix, put a URI instead"""
    for prefix, uri in prefix_map.items():
        term_id = term_id.replace(prefix + ':', uri)
    return term_id


def load_and_format_tsv(
    onto_name: str, prefix_map: Dict[str, str], filename_pattern: str, _dir: str = SIGNATURE_FILES_DIR
) -> pd.DataFrame:
    """Load and format"""
    old_term_header = '?term'
    # Get path
    path = os.path.join(_dir, filename_pattern.format(onto_name))
    # Read
    df = pd.read_csv(path, sep='\t').fillna('')
    # Filter: https://stackoverflow.com/
    # questions/55941100/how-to-filter-pandas-dataframe-rows-which-contains-any-string-from-a-list
    permissible_uris = list(prefix_map.values())
    df2 = df[df[old_term_header].str.contains('|'.join(permissible_uris)).groupby(level=0).any()]
    # Format
    # I think these are false positives, so temporarily disabling warning
    # - https://stackoverflow.com/questions/20625582/how-to-deal-with-settingwithcopywarning-in-pandas
    pd.options.mode.chained_assignment = None  # default='warn'
    df2[old_term_header] = df2[old_term_header].str.strip()
    df2[old_term_header] = df2[old_term_header].apply(uri_to_curie, prefix_map=prefix_map)
    pd.options.mode.chained_assignment = 'warn'  # default='warn'
    df2 = df2.rename({old_term_header: 'term_id'})
    return df2


def run_excluded_terms_in_mondo(
    ontologies: List[str], mondo_mappings_path: str, config_pattern: str, component_sig_pattern: str,
    mirror_sig_pattern: str, outpath: str, save=CONFIG['save']
) -> Dict[str, pd.DataFrame]:
    """Wrapper to run for all ontologies: Find excluded terms in Mondo classes"""

    return {  # TODO
        '1': pd.DataFrame(),
        '2': pd.DataFrame()
    }


# TODO: add labels. Chris recommends: https://incatools.github.io/ontology-access-kit/cli.html#runoak-fill-table
def run_excluded_terms_in_mondo_xrefs(
    ontologies: List[str], mondo_mappings_path: str, config_pattern: str, component_sig_pattern: str,
    mirror_sig_pattern: str, outpath: str, save=CONFIG['save']
) -> Dict[str, pd.DataFrame]:
    """Wrapper to run for all ontologies: Find excluded terms in Mondo xrefs"""
    onto_field = 'ontology'
    term_id_field = 'term_id'
    term_label_field = 'term_label'
    mirror_field = '1_in_mirror_tsv'
    component_field = '2_in_component_tsv'
    mappings_field = '3_in_mondo_xrefs'
    analytical_field = 'in1_notIn2_in3'
    summary_count_field = 'n_in1_notIn2_in3'
    outpath_xref_summary = outpath.replace('.tsv', '_summary.tsv')
    mondo_mappings_df = pd.read_csv(mondo_mappings_path, sep='\t', comment='#').fillna('')
    mondo_mappings_set = set(mondo_mappings_df['object_id'])

    # todo?: Do we want only (a) certain prefixes? Or (b) just any prefix in the corresponding mirror/component file?
    #  ...if (b): Make map onto_names::prefix: DOID, (OMIM, OMIMPS), Orphanet, NCIT, ICD10CM ICD10WHO, SNOMED
    df_list: List[pd.DataFrame] = []
    df_summary_list: List[pd.DataFrame] = []
    for o in ontologies:
        # Prefixes
        onto_config_path = os.path.join(METADATA_DIR, config_pattern.format(o))
        with open(onto_config_path, 'r') as stream:
            onto_config = yaml.safe_load(stream)
        prefix_uri_map = onto_config['base_prefix_map']
        # Load datasets
        mirror_df = load_and_format_tsv(onto_name=o, prefix_map=prefix_uri_map, filename_pattern=mirror_sig_pattern)
        component_df = load_and_format_tsv(
            onto_name=o, prefix_map=prefix_uri_map, filename_pattern=component_sig_pattern)
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
        df_i = pd.DataFrame(list(term_appearances.values()))
        # Analyze
        df_i[onto_field] = o
        # todo: later: might be faster to initialize `term_appearances` above for loop, `copy()` it w/in loop, and do
        #  some analysis possibly after for loop.
        df_i[analytical_field] = df_i.apply(
            lambda row:
            (row[mirror_field] == True) and
            (row[component_field] == False) and
            (row[mappings_field] == True), axis=1)
        # Add labels
        # todo: apparently URIs probably not even needed
        # df_i['temp_term_id_with_uri'] = df_i['term_id'].apply(_term_prefix_to_uri, prefix_map=prefix_uri_map)
        # TODO: put at top of file
        from oaklib.resource import OntologyResource
        from oaklib.implementations.sqldb.sql_implementation import SqlImplementation
        # https://incatools.github.io/ontology-access-kit/introduction.html#basic-python-example
        # TODO `term_label_field`
        onto_path = os.path.join(MIRROR_DIR, f'{o}.owl')
        if not os.path.exists(onto_path):  # temp until can reliably get all ontologies as .owl in mirror/
            onto_path = onto_path.replace('.owl', '.ttl')
        resource = OntologyResource(slug=onto_path, local=True)
        si = SqlImplementation(resource)
        # labels = [x for x in si.get_labels_for_curies(list(df_i['term_id']))]
        labels = []
        for curie in list(df_i['term_id']):
            label = si.get_label_by_curie(curie)
            labels.append(label)
        # Main report: Format and return
        df_i = df_i[[onto_field,
                     term_id_field, term_label_field, mirror_field, component_field, mappings_field, analytical_field]]
        df_list.append(df_i)
        # Summary: Create, format, and return
        summary_count = len(df_i[df_i[analytical_field] == True])
        df_summary_i = pd.DataFrame([{
            onto_field: o,
            summary_count_field: summary_count,
            'pct_in1_notIn2_in3__over_in1': round(summary_count / len(mirror_set), 4) if summary_count > 0 else 0
        }])
        df_summary_list.append(df_summary_i)

    # Concat
    df = pd.concat(df_list)
    df_summary = pd.concat(df_summary_list)

    # Format
    df = df.sort_values(
        [onto_field, analytical_field, term_id_field, mirror_field, component_field, mappings_field],
        ascending=[True, False, True, False, False, False])
    df_summary = df_summary.sort_values([summary_count_field], ascending=[False])

    # Save & return
    if save:
        df.to_csv(outpath, sep='\t', index=False)
        df_summary.to_csv(outpath_xref_summary, sep='\t', index=False)

    return {outpath: df, outpath_xref_summary: df_summary}


def cli_validate(d: Dict) -> Dict:
    """Validate CLI args. Also updates these args if/as necessary"""
    # Remove unused args
    d = {k: v for k, v in d.items() if v}

    # Outpath
    # - valid?
    out_filename = os.path.basename(d['outpath'])
    if out_filename not in OUTFILE_ARGS:
        raise ValueError(f'Unrecognized output with filename {out_filename}. Must be 1 of: {list(OUTFILE_ARGS.keys())}')
    # - routing: find the proper arg for routing if not already present
    arg = OUTFILE_ARGS[out_filename]
    if arg not in d:
        d[arg] = d['outpath']
    # - absolute path: Assumes relative paths are relative to /src/ontology/
    if not os.path.isabs(d['outpath']):
        d['outpath'] = os.path.join(ONTOLOGY_DIR, d['outpath'])

    return d


def cli() -> Dict[str, pd.DataFrame]:
    """Command line interface."""
    parser = cli_get_parser()
    kwargs = parser.parse_args()
    kwargs_dict: Dict = vars(kwargs)
    kwargs_dict = cli_validate(kwargs_dict)
    outputs = {}
    d = {k: v for k, v in kwargs_dict.items() if k not in OUTFILE_ARGS.values()}  # allows simple args for run() funcs
    if 'outpath_excluded_terms_in_mondo_xrefs' in kwargs_dict:
        outputs = run_excluded_terms_in_mondo_xrefs(**d)
    if 'outpath_excluded_terms_in_mondo' in kwargs_dict:
        result = run_excluded_terms_in_mondo(**d)
        outputs = {**outputs, **result}
    return outputs


def cli_get_parser() -> ArgumentParser:
    """Add required fields to parser."""
    package_description = \
        'Determine which terms outside the term scope of the Mondo source alignment are xrefed in Mondo.'
    parser = ArgumentParser(description=package_description)

    parser.add_argument(
        '-on', '--ontologies',  required=False,
        default=CONFIG['ontologies'],
        help='List of ontology names to analyze.')
    parser.add_argument(
        '-m', '--mondo-mappings-path',  required=False,
        default=CONFIG['mondo_mappings_path'],
        help='Path to `mondo.sssom.tsv`.')
    parser.add_argument(
        '-c', '--config-pattern', required=False,
        default=CONFIG['config_pattern'],
        help='Python-formattable pattern for config `.yml` for the ontology which contains a `base_prefix_map` which'
             ' contains a list of prefixes owned by the ontology. Used to filter out terms.')
    parser.add_argument(
        '-cp', '--component-sig-pattern', required=False,
        default=CONFIG['component_sig_pattern'],
        help='Python-formattable pattern for component signature files.')
    parser.add_argument(
        '-mp', '--mirror-sig-pattern', required=False,
        default=CONFIG['mirror_sig_pattern'],
        help='Python-formattable pattern for mirror signature files.')
    # todo: Ideally to avoid confusion, should have only (a) -oi and -ox, or (b) -o.
    #  Pending resolution: https://github.com/monarch-initiative/mondo-ingest/pull/35#discussion_r930447057
    parser.add_argument(
        '-oi', '--outpath-excluded-terms-in-mondo',
        help='Path for output file for list of excluded terms in Mondo.')
    parser.add_argument(
        '-ox', '--outpath-excluded-terms-in-mondo-xrefs',
        help='Path for output file for list of excluded terms that have cross-references in Mondo.')
    parser.add_argument(
        '-o', '--outpath',
        help='Path for output file. The name matters. Must be one of either (a) '
             '`reports/excluded_terms_in_mondo_xrefs.tsv`, or (b) `reports/excluded_terms_in_mondo.tsv`, the `reports/`'
             ' dir being in `src/ontology/`. The name of the file will determine the analysis run, the results of which'
             ' will go into the file at that path.')
    return parser


# Execution
if __name__ == '__main__':
    cli()
