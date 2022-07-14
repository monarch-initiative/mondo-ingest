"""Excluded terms xrefed-in Mondo

Resources
- GitHub issue: https://github.com/monarch-initiative/mondo-ingest/issues/31
- GitHub PR: https://github.com/monarch-initiative/mondo-ingest/pull/35
"""
import os
import sys
from argparse import ArgumentParser
from typing import Dict, List

import pandas as pd


# Vars
# # Static
THIS_SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
ANALYSIS_DIR = os.path.join(THIS_SCRIPT_DIR, '..')
PROJECT_DIR = os.path.join(ANALYSIS_DIR, '..', '..')
MAPPINGS_DIR = os.path.join(THIS_SCRIPT_DIR, 'ignored', 'mappings')
REPORTS_DIR = os.path.join(PROJECT_DIR, 'src', 'ontology', 'reports')
SIGNATURE_FILES_DIR = REPORTS_DIR
OUTDIR = REPORTS_DIR
# # Config
CONFIG = {
    # todo: get list from mondo config yml:
    'ontologies': ['doid', 'icd10cm', 'icd10who', 'ncit', 'omim', 'ordo'],
    'mondo_mappings_path': os.path.join(MAPPINGS_DIR, 'mondo.sssom.tsv'),
    'component_sig_pattern': 'component_signature-{}.tsv',
    'mirror_sig_pattern': 'mirror_signature-{}.tsv',
    # outpath: summary will be saved in same dir, with _summary at end of name
    'outpath': os.path.join(OUTDIR, 'excluded_terms_xrefed_in_mondo.tsv'),
    'save': True,  # save dataframes to disk
}


# Functions
def uri_to_curie(uri: str) -> str:
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


def load_and_format_tsv(onto_name: str, pattern: str, _dir: str = SIGNATURE_FILES_DIR) -> pd.DataFrame:
    """Load and format"""
    # Get path
    path = os.path.join(_dir, pattern.format(onto_name))
    # Read
    df = pd.read_csv(path, sep='\t').fillna('')
    # Format
    df['?term'] = df['?term'].apply(lambda x: x.strip())
    df['?term'] = df['?term'].apply(uri_to_curie)
    df = df.rename({'?term': 'term_id'})
    return df


def run(
    ontologies: List[str], mondo_mappings_path: str, component_sig_pattern: str, mirror_sig_pattern: str,
    outpath: str, save=CONFIG['save']
) -> Dict[str, pd.DataFrame]:
    """Wrapper to run for all ontologies"""
    onto_field = 'ontology'
    term_id_field = 'term_id'
    mirror_field = '1_in_mirror_tsv'
    component_field = '2_in_component_tsv'
    mappings_field = '3_in_mondo_xrefs'
    analytical_field = 'in1_notIn2_in3'
    summary_count_field = 'n_in1_notIn2_in3'
    summary_outpath = outpath.replace('.tsv', '_summary.tsv')
    mondo_mappings_df = pd.read_csv(mondo_mappings_path, sep='\t', comment='#').fillna('')
    mondo_mappings_set = set(mondo_mappings_df['object_id'])

    # todo?: Do we want only (a) certain prefixes? Or (b) just any prefix in the corresponding mirror/component file?
    #  ...if (b): Make map onto_names::prefix: DOID, (OMIM, OMIMPS), Orphanet, NCIT, ICD10CM ICD10WHO, SNOMED
    df_list: List[pd.DataFrame] = []
    df_summary_list: List[pd.DataFrame] = []
    for o in ontologies:
        # Load datasets
        mirror_df = load_and_format_tsv(o, mirror_sig_pattern)
        component_df = load_and_format_tsv(o, component_sig_pattern)
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
        # todo: might be faster to initialize `term_appearances` above for loop, `copy()` it w/in loop, and do some
        #  ...analysis possibly after for loop.
        df_i[analytical_field] = df_i.apply(
            lambda row:
            (row[mirror_field] == True) and
            (row[component_field] == False) and
            (row[mappings_field] == True), axis=1)
        summary_count = len(df_i[df_i[analytical_field] == True])
        df_summary_i = pd.DataFrame([{
            onto_field: o,
            summary_count_field: summary_count,
            'pct_in1_notIn2_in3__over_in1': round(summary_count / len(mirror_set), 4) if summary_count > 0 else 0
        }])
        # Format & return
        df_i = df_i[[onto_field, term_id_field, mirror_field, component_field, mappings_field, analytical_field]]
        df_list.append(df_i)
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
        df_summary.to_csv(summary_outpath, sep='\t', index=False)

    return {outpath: df, summary_outpath: df_summary}


def cli_validate(d: Dict) -> Dict:
    """Validate CLI args. Also updates these args if/as necessary"""
    # Check if exists
    for k in ['mondo_mappings_path']:
        if not os.path.exists(d[k]):
            print('Run `mondo-mappings` from `src/ontology` to generate this file.', file=sys.stderr)
            raise FileNotFoundError(d[k])

    return d


def cli() -> Dict[str, pd.DataFrame]:
    """Command line interface."""
    parser = cli_get_parser()
    kwargs = parser.parse_args()
    kwargs_dict: Dict = vars(kwargs)
    kwargs_dict = cli_validate(kwargs_dict)
    return run(**kwargs_dict)


def cli_get_parser() -> ArgumentParser:
    """Add required fields to parser."""
    package_description = \
        'Determine which terms outside the term scope of the Mondo source alignment are xrefed in Mondo.'
    parser = ArgumentParser(description=package_description)

    parser.add_argument(
        '-on', '--ontologies',
        default=CONFIG['ontologies'],
        help='List of ontology names to analyze.')
    parser.add_argument(
        '-m', '--mondo-mappings-path',
        default=CONFIG['mondo_mappings_path'],
        help='Path to `mondo.sssom.tsv`.')
    parser.add_argument(
        '-cp', '--component-sig-pattern',
        default=CONFIG['component_sig_pattern'],
        help='Python-formattable pattern for component signature files.')
    parser.add_argument(
        '-mp', '--mirror-sig-pattern',
        default=CONFIG['mirror_sig_pattern'],
        help='Python-formattable pattern for mirror signature files.')
    parser.add_argument(
        '-o', '--outpath',
        default=CONFIG['outpath'],
        help='Outpath for file reporting on excluded terms xref\'ed in Mondo.')

    return parser


# Execution
if __name__ == '__main__':
    cli()
