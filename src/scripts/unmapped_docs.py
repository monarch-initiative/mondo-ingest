"""Update documentation w/ tables of unmapped terms as well as summary stats.

Resources
- GitHub issue: https://github.com/mapping-commons/disease-mappings/issues/12
- GitHub PR: https://github.com/monarch-initiative/mondo-ingest/pull/111/
"""
import os
from glob import glob
from typing import Dict, List

import pandas as pd
from jinja2 import Template

from utils import DOCS_DIR, PROJECT_DIR, REPORTS_DIR

GLOB_PATTERN_FULL_TABLES = os.path.join(REPORTS_DIR, '*_mapping_status.tsv')
GLOB_PATTERN_SIMPLE_TABLES = os.path.join(REPORTS_DIR, '*_unmapped_terms.tsv')
UNMAPPED_DOCS_DIR = os.path.join(DOCS_DIR, 'reports')
JINJA_MAIN_PAGE = """# Mapping progress report
{{ stats_markdown_table }}

`Ontology`: Name of ontology  
`Tot terms`: Total terms in ontology  
`Tot excluded`: Total terms Mondo has excluded from mapping / integrating  
`Tot deprecated`: Total terms that the ontology source itself has deprecated  
`Tot mappable (!excluded, !deprecated)`: Total mappable candidates for Mondo; all terms that are not excluded or 
deprecated.  
`Tot mapped (mappable)`: Total mapped terms (that are mappable in Mondo). Includes exact, broad, and narrow mappings.  
`Tot unmapped (mappable)`: Total unmapped terms (that are mappable in Mondo)  
`% unmapped (mappable)`: % unmapped terms (that are mappable in Mondo)

To run the workflow that creates this data, refer to the [workflows documentation](../developer/workflows.md)."""
OUT_PATH = os.path.join(UNMAPPED_DOCS_DIR, 'unmapped.md')
JINJA_ONTO_PAGES = """## {{ ontology_name }}
[Interactive FlatGithub table](https://flatgithub.com/monarch-initiative/mondo-ingest?filename={{ source_data_path }})

### Unmapped mappable terms _(!excluded, !deprecated)_
{{ table }}"""


def update_mapping_progress_in_docs():
    """Update mapping progress report in the documentation."""
    # Read sources
    # todo: what's best way to gather ontology names? There's a way in the makefile. Is this not right to do here?
    status_table_paths: List[str] = glob(GLOB_PATTERN_FULL_TABLES)
    simple_table_paths: List[str] = glob(GLOB_PATTERN_SIMPLE_TABLES)

    # Create main page
    stats_rows: List[Dict] = []
    for path in status_table_paths:
        ontology_name = os.path.basename(path).replace('_mapping_status.tsv', '')
        df = pd.read_csv(path, sep='\t').fillna('')
        mappable_df = df[(df['is_excluded'] == False) & (df['is_deprecated'] == False)]
        unmapped_mappable_df = mappable_df[mappable_df['is_mapped'] == False]
        unmapped_mappable_df = unmapped_mappable_df.drop(columns=['is_mapped', 'is_excluded', 'is_deprecated'])
        n_mappable = len(mappable_df)
        n_unmapped_mappable = len(unmapped_mappable_df)
        n_deprecated = f"{len(df[df['is_deprecated']] == True):,}"
        stats_rows.append({
            'Ontology': f'[{ontology_name.upper()}](./unmapped_{ontology_name.lower()}.md)',
            'Tot terms': f"{len(df):,}",
            'Tot excluded': f"{len(df[df['is_excluded'] == True]):,}",
            'Tot deprecated': n_deprecated,
            'Tot deprecated unmapped': f"{len(df[(df['is_deprecated'] == True) & (df['is_mapped'] == False)]):,}",
            'Tot mappable _(!excluded, !deprecated)_': f"{n_mappable:,}",
            'Tot mapped _(mappable)_': f"{n_mappable - n_unmapped_mappable:,}",
            'Tot unmapped _(mappable)_': f"{n_unmapped_mappable:,}",
            '% unmapped _(mappable)_':
                str(round((n_unmapped_mappable / n_mappable) * 100, 1)) + '%' if n_mappable else '100%',
        })
    stats_df = pd.DataFrame(stats_rows).sort_values(['% unmapped _(mappable)_'], ascending=False)
    instantiated_str: str = Template(JINJA_MAIN_PAGE).render(stats_markdown_table=stats_df.to_markdown(index=False))
    with open(OUT_PATH, 'w') as f:
        f.write(instantiated_str)

    # Create individual pages
    for path in simple_table_paths:
        ontology_name = os.path.basename(path).replace('_unmapped_terms.tsv', '')
        outpath = os.path.join(UNMAPPED_DOCS_DIR, f'unmapped_{ontology_name.lower()}.md')
        df = pd.read_csv(path, sep='\t').fillna('')
        path = path.replace('_unmapped_terms', '_mapping_status')  # display 'mapping status' file instead
        relpath = os.path.realpath(path).replace(PROJECT_DIR + '/', '')
        instantiated_str: str = Template(JINJA_ONTO_PAGES).render(
            ontology_name=ontology_name.upper(), table=df.to_markdown(index=False), source_data_path=relpath)
        with open(outpath, 'w') as f:
            f.write(instantiated_str)


if __name__ == '__main__':
    update_mapping_progress_in_docs()
