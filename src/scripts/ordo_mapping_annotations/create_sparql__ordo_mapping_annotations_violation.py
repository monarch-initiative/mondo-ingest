"""Update ORDO mapping annotations to formalize them semantically.
Work described furthere here: https://github.com/monarch-initiative/mondo-ingest/issues/23

Resources
1. https://www.orpha.net/orphacom/cahiers/docs/GB/Orphanet_ICD10_coding_rules.pdf

Prerequisites to run this script:
1. `src/ontology/mirror/ordo.owl.owl` must be present. To get it, run `sh src/ontology/run.sh make tmp/mirror-ordo.owl`.
2. Your pwd (present working directory) should be `src/scripts/ordo_report_mapping_annotations` in order for local imports to work.

TODO's
TODO 1: `robot` --> `sh run.sh robot...`
"""
import os
from typing import Dict, List

from jinja2 import Template

from report_mapping_annotations import run as get_report


# Vars
# # Paths
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
SCRIPTS_DIR = os.path.join(SCRIPT_DIR, '..')
PROJECT_DIR = os.path.join(SCRIPTS_DIR, '..')
ONTOLOGY_DIR = os.path.join(PROJECT_DIR, 'src', 'ontology')
TEMP_DIR = os.path.join(ONTOLOGY_DIR, 'tmp')
CACHE_DIR = TEMP_DIR
SOURCES_DIR = os.path.join(PROJECT_DIR, 'src', 'ontology', 'mirror')
SPARQL_DIR = os.path.join(PROJECT_DIR, 'src', 'sparql')
# # Config
CONFIG = {
    'query_template_path': os.path.join(SPARQL_DIR, 'ordo-mapping-annotations-violation.sparql.jinja2')
}


# Functions
def sparql_jinja2_instantiate(query_template_path: str, mapping_strings: List[str]) -> str:
    """Query ontology using SPARQL query file"""
    # Instantiate template
    with open(query_template_path, 'r') as f:
        template_str = f.read()
    template_obj = Template(template_str)
    instantiated_str = template_obj.render(filter_strings=mapping_strings)
    instantiated_query_filename = os.path.basename(query_template_path).replace('.jinja2', '')
    instantiated_query_path = os.path.join(SPARQL_DIR, instantiated_query_filename)

    # Save to sparql dir
    with open(instantiated_query_path, 'w') as f:
        f.write(instantiated_str)

    return instantiated_query_path


def run(query_template_path: str):
    """Run"""
    # Get current mappings
    report: Dict = get_report()
    mapping_strings: List[str] = []
    for mapping_info in report.values():
        for string in mapping_info['unique_mapping_strings']:
            # Actual newlines break robot/sparql. Need literal text '\n'
            new_string = string.replace('\n', '\\n')
            mapping_strings.append(new_string)

    # Update template with mapping strings
    instantiated_query_path: str = sparql_jinja2_instantiate(query_template_path, mapping_strings)

    return instantiated_query_path


# Execution
if __name__ == '__main__':
    run(**CONFIG)
