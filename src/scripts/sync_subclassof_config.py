"""Sync SubClass: config"""
import os
from pathlib import Path


HERE = Path(os.path.abspath(os.path.dirname(__file__)))
SRC_DIR = HERE.parent
PROJECT_ROOT = SRC_DIR.parent


ONTOLOGY_DIR = SRC_DIR / 'ontology'
REPORTS_DIR = ONTOLOGY_DIR / 'reports'
TMP_DIR = ONTOLOGY_DIR / 'tmp'
METADATA_DIR = ONTOLOGY_DIR / 'metadata'
IN_MONDO_ONLY_FILE_STEM = '.subclass.direct-in-mondo-only.tsv'
SELF_PARENTAGE_DEFAULT_FILE_STEM = '.subclass.self-parentage.tsv'
COLLATE_IN_MONDO_ONLY_DEFAULT_PATH = REPORTS_DIR / 'sync-subClassOf.direct-in-mondo-only.tsv'
COLLATE_SELF_PARENTAGE_DEFAULT_PATH = TMP_DIR / 'sync-subClassOf.added.self-parentage.tsv'
ROBOT_SUBHEADER = [{
    'subject_mondo_id': 'ID',
    'subject_mondo_label': '',
    'object_mondo_id': '',
    'subject_source_id': '>A oboInOwl:source',
    'object_source_id': '',
    'object_mondo_label': '',
}]
EX_ONTO_NAME = 'ordo'  # ['ordo', 'doid', 'icd10cm', 'icd10who', 'omim', 'ncit']
# todo: if not remove, dedupe from/with run_defaults(); maybe a func that returns this dict
EX_DEFAULTS = {  # todo: #remove-temp-defaults
    'outpath_added': str(REPORTS_DIR / f'{EX_ONTO_NAME}.subclass.added.robot.tsv'),
    'outpath_added_obsolete': str(REPORTS_DIR / f'{EX_ONTO_NAME}.subclass.added-obsolete.robot.tsv'),
    'outpath_confirmed': str(REPORTS_DIR / f'{EX_ONTO_NAME}.subclass.confirmed.robot.tsv'),
    'outpath_confirmed_direct_source_indirect_mondo': \
        str(REPORTS_DIR / f'{EX_ONTO_NAME}.subclass.confirmed-direct-source-indirect-mondo.robot.tsv'),
    'onto_config_path': str(METADATA_DIR / f'{EX_ONTO_NAME}.yml'),
    'mondo_db_path': str(TMP_DIR / 'mondo.db'),
    'mondo_ingest_db_path': str(TMP_DIR / 'mondo-ingest.db'),
    'mondo_mappings_path': str(TMP_DIR / 'mondo.sssom.tsv'),
    'outpath_direct_in_mondo_only': str(REPORTS_DIR / f'{EX_ONTO_NAME}{IN_MONDO_ONLY_FILE_STEM}'),
    'outpath_self_parentage': str(TMP_DIR / f'{EX_ONTO_NAME}{SELF_PARENTAGE_DEFAULT_FILE_STEM}'),
    'mondo_excluded_subclasses_path': str(TMP_DIR / 'mondo-excluded-subclasses.tsv'),
    'use_cache': False,
}
