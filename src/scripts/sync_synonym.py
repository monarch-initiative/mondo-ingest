"""Ontology synchronization
# Resources
- GitHub issue: https://github.com/monarch-initiative/mondo-ingest/issues/87
"""
import os
from argparse import ArgumentParser

import pandas as pd
from oaklib.implementations import ProntoImplementation

# Vars
SCRIPTS_DIR = os.path.dirname(os.path.realpath(__file__))
PROJECT_DIR = os.path.join(SCRIPTS_DIR, '..', '..')
ONTOLOGY_DIR = os.path.join(PROJECT_DIR, 'src', 'ontology')
# REPORTS_DIR = os.path.join(ONTOLOGY_DIR, 'reports')
# METADATA_DIR = os.path.join(ONTOLOGY_DIR, 'metadata')
# CONFIG_DIR = os.path.join(ONTOLOGY_DIR, 'config')
SYNC_DIR = os.path.join(ONTOLOGY_DIR, 'sync')
TEMP_DIR = os.path.join(ONTOLOGY_DIR, 'tmp')
CACHE_DIR = TEMP_DIR


# TODO: these funcs obsolete
# Functions
# TODO: 1 func for each step. do they have sep outputs?
def sync_subclassof_axioms():
    """Synchronizes subClassOf axioms."""
    pass


def sync_xrefs():
    """Synchronizes cross-references."""
    pass


def sync_definitions():
    """Synchronizes term definitions."""
    pass


def sync_obsoletion():
    """Synchronizes term obsoletions."""
    pass


# TODO: If synonym is not already in Mondo, add it into a sync/%-synonyms.robot.template.tsv
def sync_synonyms(ontology: ProntoImplementation, mondo: ProntoImplementation, outpath_synonyms: str, cache=False):
    """Whenever new synonym or label in upstream source, want to add it to Mondo. If the label is not the Mondo label or
     existing synonym, it will become a synonym."""
    # todo: params: ontology,mondo: Can OAK support synonyms / other needs? Or should I use sparql?
    print()


# TODO
def run(
    ontology_path: str, mondo_path: str, mondo_sans_exclusions_path: str, sssom_map_path: str, onto_config_path: str,
    outpath_synonyms: str, outpath: str, cache=False
):
    """Run"""
    # Prefixes
    # TODO: read ontology_path (repurpose from slurp) (cache it? dk if it really saves time. can time it)
    ontology = None
    # TODO: read mondo_path
    mondo = None
    # TODO: read mondo_sans_exclusions_path (do I even need mondo.owl if using this?)
    mondo_sans_axiom_exclusions = None
    # TODO: read sssom_map_path
    sssom_df = pd.DataFrame()
    # TODO: onto_config_path: Needed?
    # with open(config_path, 'r') as stream:
    #     onto_config = yaml.safe_load(stream)
    # prefix_uri_map = onto_config['base_prefix_map']

    # TODO:
    # todo: @nico: Clarify; says 'axioms', but does this apply to xrefs, defs, obsoletions, synonyms?
    # Algo
    # https://github.com/monarch-initiative/mondo-ingest/issues/27
    # 1. Remove all support from O_t in all axioms in O_s
    # 2. Import all axioms from O_t that is not in O_s or O_reject.
    # 3. Add support for all axioms in O_s that are in O_t.
    # 4. Human reviewer looks at all new axioms O_s (O_t-(O_s+O_reject)).
    #    - If the axiom is bad, add the axiom to (O_reject)
    # 5. Repeat process (start from 1) until all axioms are good (if all bad axioms are removed in the first run, just
    #    one second run is needed).
    # 6. Optionally, human reviewer looks at all axioms in O_t that now lost all support.
    #    - If the axiom is bad, add the axiom to (O_reject)
    # 7. (reduce is not run) (kgcl/sssom cross-product)
    sync_synonyms(ontology=ontology, mondo=mondo, outpath_synonyms=outpath_synonyms, cache=cache)  # TODO
    sync_subclassof_axioms()  # todo
    sync_xrefs()  # todo
    sync_definitions()  # todo
    sync_obsoletion()  # todo
    print(outpath)  # todo: write update?


def cli():
    """Command line interface."""
    package_description = \
        'Ontology synchronization pipeline. Automates integration of updates from other ontologies into Mondo.'
    parser = ArgumentParser(description=package_description)
    parser.add_argument(
        '-O', '--ontology-path', required=True,
        help='Path to the ontology file to sync from into Mondo.')
    parser.add_argument(
        '-m', '--mondo-path', required=True,
        help='Path to `mondo.owl`.')
    parser.add_argument(  # todo: change name to mondo-sans-axiom-exclusions-path? If so: update makefile, debug configs
        '-e', '--mondo-sans-exclusions-path', required=True,
        help='Path to a copy of Mondo that excludes certain axioms.')
    parser.add_argument(
        '-s', '--sssom-map-path', required=True,
        help='Path to file containing all known Mondo mappings, in SSSOM format.')
    # TODO: Is this needed?
    parser.add_argument(
        '-c', '--onto-config-path', required=True,
        help='Path to a config `.yml` for the ontology which contains a `base_prefix_map` which contains a '
             'list of prefixes owned by the ontology. Used to filter out terms.')
    parser.add_argument(
        '-os', '--outpath-synonyms', required=True,
        help='Path to robot template TSV to create whicih will contain synonyms that aren\'t yet integrated into Mondo '
             'for given ontoogy.')
    # TODO: will this be the same as --mondo-path?
    parser.add_argument(
        '-o', '--outpath', required=True,
        help='Path to variation of `mondo.owl` to create/update.')
    parser.add_argument(
        '-C', '--cache', required=False,
        help='Cache intermediaries? E.g. results of queries for a given ontology.')
    run(**vars(parser.parse_args()))


# Execution
if __name__ == '__main__':
    cli()
