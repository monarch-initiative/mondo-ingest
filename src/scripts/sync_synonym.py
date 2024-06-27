"""Whenever new synonym or label in upstream source, want to add it to Mondo. If the label is not the Mondo label or
existing synonym, it will become a synonym.
"""
from argparse import ArgumentParser
from pathlib import Path
from typing import Union, List, Tuple, Dict

import pandas as pd
from oaklib import get_adapter
from oaklib.implementations import SqlImplementation
from oaklib.types import CURIE, PRED_CURIE


# todo: reactivate if needed
# HERE = Path(os.path.abspath(os.path.dirname(__file__)))
# SRC_DIR = HERE.parent
# PROJECT_ROOT = SRC_DIR.parent
# sys.path.insert(0, str(PROJECT_ROOT))
# from src.scripts.utils import ONTOLOGY_DIR



# TODO
def sync_synonyms(
    ontology_db_path: Union[Path, str], mondo_db_path: Union[Path, str], mondo_mappings_path: Union[Path, str],
    onto_config_path: Union[Path, str], outpath_added: Union[Path, str], outpath_updated: Union[Path, str]
):
    """Whenever new synonym or label in upstream source, want to add it to Mondo. If the label is not the Mondo label or
     existing synonym, it will become a synonym."""
    #     For every term in source:
    #         For every synonym or label on term:
    #             Add row to robot template with correct evidence (with Mondo ID of course)
    source_db: SqlImplementation = get_adapter(ontology_db_path)
    source_ids_all: List[CURIE] = [
        x for x in [y for y in source_db.entities(filter_obsoletes=False)]]
    # if any([x.startswith(y) for y in owned_prefix_map.keys()]  # todo: filter by owned_prefix_map in metadata
    id_syns_map: Dict[CURIE, List[Tuple[PRED_CURIE, str]]] = {_id: [] for _id in source_ids_all}
    for source_id in source_ids_all:
        for pred, alias in sorted(source_db.alias_relationships(source_id)):
            # todo: filter out just synonyms
            # todo: why do some rdfs:label have None as alias? this isn't what I see in docs
            #  https://incatools.github.io/ontology-access-kit/guide/aliases.html although i guess doesn't matter
            id_syns_map[source_id].append((pred, alias))
    # todo: temp
    id_syns_map2 = {x: y for x, y in id_syns_map.items() if x.startswith('OMIM')}  # todo: filter out just synonyms
    print()

    # TODO: see what Mondo has for the given
    #  - what to do if the term isn't in Mondo? Just skip? I think so
    # Check Mondo
    # 1. Get exact matched Mondo IDs using mondo.sssom.tsv
    # 2. Query Mondo .db for current synonym info on that term
    print()



# todo: #1 make sure that the help text, short flags, etc is consistent etween files
def cli():
    """Command line interface."""
    package_description = \
        'Ontology synchronization pipeline. Automates integration of updates from other ontologies into Mondo.'
    parser = ArgumentParser(description=package_description)
    # TODO: Which way is better? (a) mondo-ingest.db, as subclass sync was doing? or (b) the individual source's.db?
    #  I think 'b' is better but IDR why I set up subclass sync w/ 'a'.
    parser.add_argument(
        '-d', '--ontology-db-path', required=False,
        help='Path to SemanticSQL sqlite `.db` file for the given source ontology.')
    parser.add_argument(
        '-D', '--mondo-db-path', required=False,
        help='Path to SemanticSQL sqlite `mondo.db`.')
    parser.add_argument(
        '-s', '--mondo-mappings-path', required=True,  # TODO: Is this arg needed?
        help='Path to file containing all known Mondo mappings, in SSSOM format.')
    parser.add_argument(
        '-c', '--onto-config-path', required=True,  # TODO: Is this arg needed?
        help='Path to a config `.yml` for the ontology which contains a `base_prefix_map` which contains a '
             'list of prefixes owned by the ontology. Used to filter out terms.')
    parser.add_argument(
        '-a', '--outpath-added', required=True,
        help='Path to robot template TSV to create which will contain synonyms that aren\'t yet integrated into Mondo '
             'for given ontoogy.')
    parser.add_argument(
        '-u', '--outpath-updated', required=True,
        help='Path to robot template TSV to create which will contain synonyms changes.')
    sync_synonyms(**vars(parser.parse_args()))


# Execution
if __name__ == '__main__':
    cli()
