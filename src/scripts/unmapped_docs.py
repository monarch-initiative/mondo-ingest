"""Update documentation w/ tables of unmapped terms as well as summary stats.

Resources
- GitHub issue: https://github.com/mapping-commons/disease-mappings/issues/12
- GitHub PR: https://github.com/monarch-initiative/mondo-ingest/pull/111/
"""
import os
from glob import glob
from typing import List

import pandas as pd
from jinja2 import Template

from utils import DOCS_DIR, REPORTS_DIR


# Vars
TABLES_GLOB_PATTERN = os.path.join(REPORTS_DIR, '*_unmapped_terms.tsv')
JINJA_PATH = os.path.join(DOCS_DIR, 'reports', 'unmapped.md.jinja2')
OUT_PATH = os.path.join(DOCS_DIR, 'reports', 'unmapped.md')


# Functions
# todo: Try getting stats in the mappings_unmapped_docs.py step. If that isn't as effective, do it here.
def update_mapping_progress_in_docs():
    """Update mapping progress report in the documentation."""
    # Read sources
    # todo: what's best way to gather ontology names? There's a way in the makefile. Is this not right to do here?
    table_paths: List[str] = glob(TABLES_GLOB_PATTERN)
    ontologies = {}
    for path in table_paths:
        o = os.path.basename(path).replace('_unmapped_terms.tsv', '').upper()
        df = pd.read_csv(path, sep='\t').fillna('')
        markdown_table: str = df.to_markdown(index=False)
        n_unmapped = len(df[df['comment'] == 'Unmapped'])
        ontologies[o] = {
            'df': df,
            'markdown_table': markdown_table,
            'Total mappable terms': f"{len(df):,}",
            'Unmapped terms': f"{n_unmapped:,}",
            '% terms mapped': str(round((1 - (n_unmapped / len(df))) * 100, 1)) + '%',
        }

    # Generate stats
    stats_rows = [{**{'Ontology': o}, **{k: v for k, v in d.items() if k not in ['df', 'markdown_table']}}
                  for o, d in ontologies.items()]
    stats_markdown_table: str = pd.DataFrame(stats_rows).to_markdown(index=False)

    # Write output
    with open(JINJA_PATH, 'r') as file:
        template_str = file.read()
    template_obj = Template(template_str)
    instantiated_str = template_obj.render(
        ontologies={k: v['markdown_table'] for k, v in ontologies.items()},
        stats_markdown_table=stats_markdown_table)
    with open(OUT_PATH, 'w') as f:
        f.write(instantiated_str)


# Execution
if __name__ == '__main__':
    update_mapping_progress_in_docs()
