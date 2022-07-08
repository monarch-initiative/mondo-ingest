"""Report ORDO mapping strings
Work described furthere here: https://github.com/monarch-initiative/mondo-ingest/issues/23

Resources
1. https://www.orpha.net/orphacom/cahiers/docs/GB/Orphanet_ICD10_coding_rules.pdf

Prerequisites to run this script:
1. `src/ontology/mirror/ordo.owl.owl` must be present. To get it, run `sh src/ontology/run.sh make component-download-ordo.owl`.

TODO's
TODO 1: `robot` --> `sh run.sh robot...`
"""
import json
import os
import subprocess
from typing import Dict

import pandas as pd


# Vars
# # Paths
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
SCRIPTS_DIR = os.path.join(SCRIPT_DIR, '..')
PROJECT_DIR = os.path.join(SCRIPTS_DIR, '..')
ONTOLOGY_DIR = os.path.join(PROJECT_DIR, 'src', 'ontology')
TEMP_DIR = os.path.join(ONTOLOGY_DIR, 'tmp')
CACHE_DIR = TEMP_DIR
SOURCES_DIR = os.path.join(PROJECT_DIR, 'src', 'ontology', 'tmp')
SPARQL_DIR = os.path.join(PROJECT_DIR, 'src', 'sparql')
# # Messages
REQS_ERR = '`{}` must be present. To get it, run `sh src/ontology/run.sh make component-download-ordo.owl`.'
# # Config
CONFIG = {
    'input_paths': {
        'ontology': os.path.join(SOURCES_DIR, 'ordo.owl.owl'),
        'ontology_backup': os.path.join(SOURCES_DIR, 'component-download-ordo.owl.owl'),
        'mapping_code_meanings': os.path.join(
            PROJECT_DIR, 'src', 'ontology', 'config', 'ordo-mapping-codes_relationship-curies.csv'),
        'sparql_query': os.path.join(SPARQL_DIR, 'ordo-select-mapping-annotations.sparql'),
    },
    'use_cache': False,
    '_print': True
}


# Functions
def sparql_file_query__via_robot(onto_path: str, query_path: str, use_cache=False) -> pd.DataFrame:
    """Query ontology using SPARQL query file"""
    # Basic vars
    results_filename = 'results.csv'
    command_save_filename = 'command.sh'
    results_dirname = os.path.basename(onto_path).replace('/', '-').replace('.', '-') + \
        '__' + os.path.basename(query_path).replace('.', '-')
    results_dirpath = os.path.join(CACHE_DIR, 'robot', results_dirname)
    command_save_path = os.path.join(results_dirpath, command_save_filename)
    results_path = os.path.join(results_dirpath, results_filename)

    # Use cache if exists and desired, else run and cache
    if not use_cache or (use_cache and not os.path.exists(results_path)):
        command_str = f'robot query --input {onto_path} --query {query_path} {results_path}'
        os.makedirs(results_dirpath, exist_ok=True)
        if not os.path.exists(results_path):
            with open(command_save_path, 'w') as f:
                f.write(command_str)
        subprocess.run(command_str.split())

    # Read results and return
    try:
        df = pd.read_csv(results_path).fillna('')
    except pd.errors.EmptyDataError as err:
        os.remove(results_path)  # done so that it doesn't read this from cache
        raise err

    return df


def get_ordo_mappings_report(
    onto_path: str, query_path: str, mapping_meanings_path: str, use_cache=False
) -> Dict:
    """Get ordo mappings
    :return Dict:Get map of unique ORDO mapping strings to relationship CURIEs """
    # Get mapping code meanings
    code_meanings_df: pd.DataFrame = pd.read_csv(mapping_meanings_path)
    code_meanings = {}
    for index, row in code_meanings_df.iterrows():
        code_meanings[row['ordo_mapping_code']] = row['relationship_curie']

    # Get current mapping annotations
    df: pd.DataFrame = sparql_file_query__via_robot(onto_path, query_path, use_cache)
    df['cls'] = df['cls'].apply(lambda uri: uri.split('_')[-1])
    df = df.rename(columns={'cls': 'class_id'})

    # Collect annotation info
    # - Get classes
    d = {}
    for index, row in df.iterrows():
        map_str: str = row['mapping_precision_string']
        if map_str not in d:
            d[map_str] = {'classes': []}
        d[map_str]['classes'].append(row['class_id'])
    # - Get n classes
    d = {
        k: {
            'classes': v['classes'],
            'n': len(v['classes'])
        }
        for k, v in d.items()
    }
    # - Collate info
    d2 = {}
    #  d2 keys: unique ORDO mapping codes
    #  d2 values: i. assumed formalized mapping predicate, ii. number of mappings, iii. list of Orphanet class IDs that
    #  ...are the subject of this predicate, iv. unique mapping strings.
    for k, v in d.items():
        code: str = k.split('(')[0].replace('-', '').strip()
        if code not in d2:
            d2[code] = {'classes': [], 'n': 0, 'unique_mapping_strings': [], 'relationship_curie': code_meanings[code]}
        d2[code]['classes'] += v['classes']
        d2[code]['n'] += v['n']
        d2[code]['unique_mapping_strings'].append(k)

    return d2


def run(input_paths: Dict[str, str] = CONFIG['input_paths'], use_cache=False, _print=True) -> Dict:
    """Prints results in JSON"""
    # Check prerequisites
    onto_path: str = input_paths['ontology']
    if not os.path.exists(onto_path):
        err = REQS_ERR.format(onto_path)
        onto_path: str = input_paths['ontology_backup']
        if not os.path.exists(onto_path):
            raise FileNotFoundError(err)

    # Get current mappings
    report: Dict = get_ordo_mappings_report(
        onto_path,
        input_paths['sparql_query'],
        input_paths['mapping_code_meanings'],
        use_cache)

    if _print:
        print(json.dumps(report, indent=4))

    return report


# Execution
if __name__ == '__main__':
    run(**CONFIG)
