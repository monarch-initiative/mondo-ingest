"""Update ORDO mapping annotations to formalize them semantically.
Work described furthere here: https://github.com/monarch-initiative/mondo-ingest/issues/23

Resources
1. https://www.orpha.net/orphacom/cahiers/docs/GB/Orphanet_ICD10_coding_rules.pdf

Prerequisites to run this script:
1. `src/ontology/mirror/ordo.owl.owl` must be present. To get it, run:
`sh src/ontology/run.sh make component-download-ordo.owl`.
2. Your pwd (present working directory) should be `src/scripts/ordo_report_mapping_annotations` in order for local
imports to work.

TODO's
TODO 1: `robot` --> `sh run.sh robot...`
"""
import os
import subprocess
from typing import Dict

from jinja2 import Template

from report_mapping_annotations import run as get_report


# Vars
# # Paths
# todo: I wonder if handling this duplicated code fragment (these path variables) would be a good idea.
# noinspection DuplicatedCode
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
        'sparql_query': os.path.join(SPARQL_DIR, 'ordo-replace-annotation-based-mappings.ru.jinja2'),
    },
    # output_path: If `run_command` is True, will generate this. However, this is not part of the pipeline, so this
    # ...output is probably just for ad-hoc analysis purposes.
    'output_path': os.path.join(PROJECT_DIR, 'ordo-new.owl'),
    'run_command': False  # If false, just instantiates templates and saves. If true, also runs them.
    # 'use_cache': True  # saves instantiated strings to cache/ anyway, but doesn't re-use them atm
}


# Functions
def sparql_jinja2_file_query__via_robot(
    onto_path: str, query_template_path: str, output_path: str, mapping_str__curie__map: Dict, run_command=False
) -> Dict[str, str]:
    """Query ontology using SPARQL query file

    :param: run_command (bool): If True, then in addition to instantiating the Jinja template, it will also run the
    instantiated queries.
    """
    results_dirname = os.path.basename(onto_path).replace('/', '-').replace('.', '-') + \
        '__' + os.path.basename(query_template_path).replace('.', '-')
    results_dirpath = os.path.join(CACHE_DIR, 'robot', results_dirname)
    command_save_filename = 'command.sh'
    command_save_path = os.path.join(results_dirpath, command_save_filename)
    if run_command:
        os.makedirs(results_dirpath, exist_ok=True)

    # Instantiate template
    with open(query_template_path, 'r') as f:
        template_str = f.read()
    template_obj = Template(template_str)
    instantiated_str = template_obj.render(mapping_str__curie__map=mapping_str__curie__map)
    instantiated_query_filename = os.path.basename(query_template_path).replace('.ru.jinja2', '.ru')
    instantiated_query_path = os.path.join(SPARQL_DIR, instantiated_query_filename)
    if run_command:
        instantiated_query_cache_path = os.path.join(results_dirpath, instantiated_query_filename)
        # if not (os.path.exists(instantiated_query_path) and use_cache):
        # Save to cache
        with open(instantiated_query_cache_path, 'w') as f:
            f.write(instantiated_str)
    # Save to sparql dir
    with open(instantiated_query_path, 'w') as f:
        f.write(instantiated_str)

    report = {}
    if run_command:
        command_str = f'robot query --input {onto_path} --update {instantiated_query_path} --output {output_path}'

        # Cache and run
        # if not (os.path.exists(results_path) and use_cache):
        with open(command_save_path, 'w') as f:
            f.write(command_str)
        subprocess.run(command_str.split(), capture_output=True, text=True)
        result = subprocess.run(['ls', '-l'], capture_output=True, text=True)

        # Warnings go to 'errors' as well
        report = {'info': result.stdout, 'errors': result.stderr}

    return report


def run(input_paths: Dict[str, str], output_path: str, run_command=False):
    """Run"""
    # Check prerequisites
    onto_path: str = input_paths['ontology']
    if not os.path.exists(onto_path):
        err = REQS_ERR.format(onto_path)
        onto_path: str = input_paths['ontology_backup']
        if not os.path.exists(onto_path):
            raise FileNotFoundError(err)

    # Get current mappings
    report: Dict = get_report(_print=False)
    mapping_str__curie__map: Dict[str, str] = {}
    for mapping_info in report.values():
        for string in mapping_info['unique_mapping_strings']:
            # Actual newlines break robot/sparql. Need literal text '\n'
            new_string = string.replace('\n', '\\n')
            mapping_str__curie__map[new_string] = mapping_info['relationship_curie']

    # Update mappings
    results: Dict[str, str] = sparql_jinja2_file_query__via_robot(
        onto_path,
        input_paths['sparql_query'],
        output_path,
        mapping_str__curie__map,
        run_command)

    return results


# Execution
if __name__ == '__main__':
    run(**CONFIG)
