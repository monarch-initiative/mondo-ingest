"""Deprecated terms that have xrefs in Mondo.

Resources
- GitHub issue: https://github.com/monarch-initiative/omim/issues/87
- GitHub PR: https://github.com/monarch-initiative/mondo-ingest/pull/108
"""
import os
from argparse import ArgumentParser
from glob import glob
from typing import Dict, List

import pandas as pd
from jinja2 import Template
from oaklib.types import CURIE

from utils import DOCS_DIR, PROJECT_DIR, REPORTS_DIR


FILENAME_GLOB_PATTERN = '*_mapped_deprecated_terms.robot.template.tsv'
PATH_GLOB_PATTERN = os.path.join(REPORTS_DIR, FILENAME_GLOB_PATTERN)
THIS_DOCS_DIR = os.path.join(DOCS_DIR, 'reports')
JINJA_MAIN_PAGE = """# Mapped deprecated terms
{{ stats_markdown_table }}

`Ontology`: Name of ontology    
`Tot deprecated in Mondo`: Total terms that the ontology source itself has deprecated which have existing xrefs in Mondo

To run the workflow that creates this data, refer to the [workflows documentation](../developer/workflows.md)."""
DOCS_OUT_PATH = os.path.join(THIS_DOCS_DIR, 'mapped_deprecated.md')
JINJA_ONTO_PAGES = """## {{ ontology_name }}
[Interactive FlatGithub table](https://flatgithub.com/monarch-initiative/mondo-ingest?filename={{ source_data_path }})

### Mapped deprecated terms
{{ table }}"""


def deprecated_in_mondo_docs():
    """Update documentation with info about deprecated terms still mapped to Mondo."""
    # Read sources
    # todo: what's best way to gather ontology names? There's a way in the makefile. Is this not right to do here?
    paths: List[str] = glob(PATH_GLOB_PATTERN)

    # Create pages & build stats
    stats_rows: List[Dict] = []
    for path in paths:
        ontology_name = os.path.basename(path).replace(FILENAME_GLOB_PATTERN[1:], '')
        ontology_page_relpath = f'./mapped_deprecated_{ontology_name.lower()}.md'
        df = pd.read_csv(path, sep='\t').fillna('')
        # Individual pages
        relpath = os.path.realpath(path).replace(PROJECT_DIR + '/', '')
        instantiated_str: str = Template(JINJA_ONTO_PAGES).render(
            ontology_name=ontology_name.upper(), table=df.to_markdown(index=False), source_data_path=relpath)
        with open(os.path.join(THIS_DOCS_DIR, ontology_page_relpath.replace('./', '')), 'w') as f:
            f.write(instantiated_str)
        # Stats
        stats_rows.append({
            'Ontology': f'[{ontology_name.upper()}]({ontology_page_relpath})',
            'Tot deprecated in Mondo': f"{len(df) - 1:,}",  # -1 because robot template subheader
        })

    # Stats: save
    stats_df = pd.DataFrame(stats_rows).sort_values(['Tot deprecated in Mondo'], ascending=False)
    instantiated_str: str = Template(JINJA_MAIN_PAGE).render(stats_markdown_table=stats_df.to_markdown(index=False))
    with open(DOCS_OUT_PATH, 'w') as f:
        f.write(instantiated_str)


def deprecated_in_mondo(mapping_status_path: str, mondo_mappings_path: str, outpath: str) -> pd.DataFrame:
    """Run"""
    mapping_status_df = pd.read_csv(mapping_status_path, sep='\t').fillna('')
    mondo_mappings_df = pd.read_csv(mondo_mappings_path, sep='\t', comment='#').fillna('')
    source_to_mondo_map: Dict[CURIE, List[CURIE]] = {}
    for _index, row in mondo_mappings_df.iterrows():
        source_to_mondo_map.setdefault(row['object_id'], []).append(row['subject_id'])

    # Locate bad mappings
    rows: List[Dict] = []
    mapped_dep_df = mapping_status_df[(mapping_status_df['is_mapped']) & (mapping_status_df['is_deprecated'])]
    mapped_dep: List[CURIE] = list(mapped_dep_df['subject_id']) if len(mapped_dep_df) > 0 else []
    for source_id in [x for x in mapped_dep if x in source_to_mondo_map]:
        for mondo_id in source_to_mondo_map[source_id]:
            rows.append({
                'mondo_id': mondo_id,
                'source_id': source_id,
                'source': 'MONDO:equivalentObsolete',
            })

    # Save and return
    rows = [{'mondo_id': 'ID', 'source_id': 'ID', 'source': 'A oboInOwl:source'}] + rows
    df = pd.DataFrame(rows).sort_values(by=['mondo_id', 'source_id'], ascending=[True, True])
    df.to_csv(outpath, index=False, sep='\t')

    return df


def cli() -> pd.DataFrame:
    """Command line interface"""
    parser = ArgumentParser(description='List all deprecated terms that have xrefs in Mondo.')
    # deprecated_in_mondo() args
    parser.add_argument('-o', '--outpath', required=False, help='Path for output.')
    parser.add_argument(
        '-s', '--mapping-status-path', required=False,
        help='Path to create a TSV with a list of all terms and columns: subject_id, subject_label, is_mapped, '
             'is_excluded, is_deprecated.')
    parser.add_argument(
        '-m', '--mondo-mappings-path', required=False,
        help='Path to file containing all known Mondo mappings, in SSSOM format.')
    # deprecated_in_mondo_docs() args
    parser.add_argument(
        '-d', '--docs', required=False, action='store_true',
        help='Generates documentation based on any existing "deprecated in Mondo" tables.')
    d: Dict = vars(parser.parse_args())
    docs = d.pop('docs')
    if docs and any([d[x] for x in d]):
        raise RuntimeError('If --docs, don\'t provide any other arguments.')
    return deprecated_in_mondo_docs() if docs else deprecated_in_mondo(**d)


# Execution
if __name__ == '__main__':
    cli()
