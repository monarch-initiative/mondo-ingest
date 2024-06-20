"""Whenever new synonym or label in upstream source, want to add it to Mondo. If the label is not the Mondo label or
existing synonym, it will become a synonym.
"""
from argparse import ArgumentParser
from datetime import datetime
from pathlib import Path
from typing import Union, List, Tuple, Dict, Set

import pandas as pd
from oaklib import get_adapter
from oaklib.datamodels.ontology_metadata import Annotation
from oaklib.implementations import SqlImplementation
from oaklib.types import CURIE, PRED_CURIE

from src.scripts.utils import PREFIX_MAP, get_owned_prefix_map


# todo: reactivate if needed
# HERE = Path(os.path.abspath(os.path.dirname(__file__)))
# SRC_DIR = HERE.parent
# PROJECT_ROOT = SRC_DIR.parent
# sys.path.insert(0, str(PROJECT_ROOT))
# from src.scripts.utils import ONTOLOGY_DIR


def _get_synonyms(ids: List[CURIE], db: SqlImplementation) -> pd.DataFrame:
    """Get synonym triples from sqlite DB"""
    # todo: del this commented out stuff at end. leaving here in case I decide to change impl back from set to dict
    # id_syns_map: Dict[CURIE, List[Tuple[PRED_CURIE, str]]] = {_id: [] for _id in ids}
    # for _id in ids:
    #     for pred, alias in sorted(db.alias_relationships(_id)):
    #         id_syns_map[_id].append((pred, alias))

    tups: Set[Tuple[CURIE, PRED_CURIE, str]] = set()
    for _id in ids:
        for pred, alias in sorted(db.alias_relationships(_id)):
            # - filter all but synonyms: prior in pipeline have already converted other props such as 'label' to syns
            # todo: is this the best filter? is there more that can appear that should be filtered out? Should instead
            #  not filter by things we want out, but by the list of synonym preds we want in?
            if pred == 'rdfs:label':
                continue
            tups.add((_id, pred, alias))
    df = pd.DataFrame(tups, columns=['curie', 'synonym_scope', 'synonym'])
    return df


# TODO
def sync_synonyms(
    ontology_db_path: Union[Path, str], mondo_db_path: Union[Path, str], mondo_mappings_path: Union[Path, str],
    onto_config_path: Union[Path, str], outpath_added: Union[Path, str], outpath_updated: Union[Path, str]
):
    """Whenever new synonym or label in upstream source, want to add it to Mondo. If the label is not the Mondo label or
     existing synonym, it will become a synonym."""
    # Iterate over mappings
    mappings_df = pd.read_csv(mondo_mappings_path, sep='\t', comment='#')
    # todo: refactor filtering by prefixes
    #  check if this pattern has been used elsewhere; I think it has. and abstract into func for these 3 lines; 'filter prefixes'
    #  - OR use this?: get_all_owned_terms()
    #    - it seems long and messy compared to these 3 lines, but is more comprehensive. I could make get_all_owned_terms() a simple 3 line func and then make a separate func for all edge cases?
    # - filter by source
    owned_prefix_map: PREFIX_MAP = get_owned_prefix_map(onto_config_path)
    mappings_df['object_prefix'] = mappings_df['object_id'].apply(lambda x: x.split(':')[0])
    mappings_df = mappings_df[mappings_df['object_prefix'].isin(owned_prefix_map.keys())]
    del mappings_df['object_prefix']

    # Query synonyms
    print(f'Querying synonyms')
    # - Source
    # todo: do I need the db's elsewhere? if not, refactor to instantiate them inside the func
    source_db: SqlImplementation = get_adapter(ontology_db_path)
    t0 = datetime.now()
    source_df: pd.DataFrame = _get_synonyms(mappings_df['object_id'].tolist(), source_db)
    source_df = source_df.rename(columns={'curie': 'source_id'})
    source_df['mondo_id'] = ''  # todo: do I want to add this at this stage?
    source_df = source_df[['mondo_id', 'synonym_scope', 'synonym', 'source_id']]  # todo: do I want to add this at this stage?
    t1 = datetime.now()
    print(f'- queried source in n seconds: {(t1 - t0).seconds}')
    # - Mondo
    mondo_db: SqlImplementation = get_adapter(mondo_db_path)
    mondo_df: pd.DataFrame = _get_synonyms(mappings_df['subject_id'].tolist(), mondo_db)
    mondo_df = mondo_df.rename(columns={'curie': 'mondo_id'})
    t2 = datetime.now()
    print(f'- queried Mondo (basic info) in n seconds: {(t2 - t1).seconds}')
    #  - fetch sources for Mondo synonyms
    # TODO: fetch synonym source
    # todo: might want to consider subsetting like 100 rows just for demo
    # todo: pr comment: performance _axiom_annotations(): 20k rows, while mondo_df had 56k rows in 15-20 min. although set of mondo ID in these rows was 6509 while in mondo_df was 9706
    rows2: List[Tuple[CURIE, PRED_CURIE, str, CURIE]] = []
    i = 0
    for row in mondo_df.itertuples():
        t2_i = datetime.now()
        i += 1
        # noinspection PyProtectedMember,PyUnresolvedReferences doesnt_detect_named_tuples
        anns: List[Annotation] = [x for x in mondo_db._axiom_annotations(row.mondo_id, row.synonym_scope, value=row.synonym)]
        # noinspection PyUnresolvedReferences doesnt_detect_named_tuples
        rows2.extend([(row.mondo_id, row.synonym_scope, row.synonym, ann.object) for ann in anns])
        if i % 50 == 0:
            print(f'queried {i} of {len(mondo_df)} Mondo IDs in n seconds: {(datetime.now() - t2_i).seconds}')

    # todo: based on performance, consider: _axiom_annotations_multi(
    # todo: address sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) too many SQL variables
    rows2: List[Tuple[CURIE, PRED_CURIE, str, CURIE]] = []
    mondo_ids: List[CURIE] = mondo_df['mondo_id'].tolist()
    batch_size = 5000  # addresses: (sqlite3.OperationalError) too many SQL variables
    preds = mondo_df['synonym_scope'].unique()
    i = 0
    for pred in preds:
        i += 1
        for j in range(0, len(mondo_ids), batch_size):
            t2_i = datetime.now()
            mondo_ids_subset = mondo_ids[j:j + batch_size]
            # noinspection PyProtectedMember
            anns: List[Annotation] = [x for x in mondo_db._axiom_annotations_multi(
                mondo_ids_subset, pred,
                # values=mondo_df['synonym'].tolist()
            )]
            print(f'- queried Mondo (synonym sources), predicate {i} of {len(preds)}, {batch_size} Mondo IDs ({j+batch_size} so far of {len(mondo_ids)}) in n seconds: {(datetime.now() - t2_i).seconds}')
            # noinspection PyUnresolvedReferences doesnt_detect_named_tuples
            rows2.extend([(ann.subject, pred, ann.value, ann.object) for ann in anns])  # TODO: this work?

    t3 = datetime.now()
    print(f'- queried Mondo (synonym sources) in n seconds: {(t3 - t2).seconds}')
    mondo_df2 = pd.DataFrame(rows2, columns=['mondo_id', 'synonym_scope', 'synonym', 'source_id'])

    # TODO: filter by source_id in owned prefixes
    pass

    # TODO: set diffs
    print()

    print()
    # TODO: sources for mondo synonyms
    #  - we can get this via sparql. but can we get via OAK?
    #  - this will help to add source to existing synonyms from other sources, or remove from specific sources
    # TODO: synonym type, e.g. DEPRACATED



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
