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
COLLATE_IN_MONDO_ONLY_DEFAULT_PATH = REPORTS_DIR / 'sync-subClassOf.direct-in-mondo-only.tsv'
ROBOT_SUBHEADER = [{
    'subject_mondo_id': 'ID',
    'subject_mondo_label': '',
    'object_mondo_id': '',
    'subject_source_id': '>A oboInOwl:source',
    'object_source_id': '',
    'object_mondo_label': '',
}]
EX_ONTO_NAME = 'ordo'  # ['ordo', 'doid', 'icd10cm', 'icd10who', 'omim', 'ncit']
EX_DEFAULTS = {  # todo: #remove-temp-defaults
    'outpath_added': str(REPORTS_DIR / f'{EX_ONTO_NAME}.subclass.added.robot.tsv'),
    'outpath_added_obsolete': str(REPORTS_DIR / f'{EX_ONTO_NAME}.subclass.added-obsolete.robot.tsv'),
    'outpath_confirmed': str(REPORTS_DIR / f'{EX_ONTO_NAME}.subclass.confirmed.robot.tsv'),
    'onto_config_path': str(METADATA_DIR / f'{EX_ONTO_NAME}.yml'),
    'mondo_db_path': str(TMP_DIR / 'mondo.db'),
    'mondo_ingest_db_path': str(TMP_DIR / 'mondo-ingest.db'),
    'mondo_mappings_path': str(TMP_DIR / 'mondo.sssom.tsv'),
    'outpath_in_mondo_only': str(REPORTS_DIR / f'{EX_ONTO_NAME}{IN_MONDO_ONLY_FILE_STEM}'),
    'use_cache': False,
}