"""Slurp migration pipeline

Basically, we:
1. Look at all unmapped terms T
2. If all of parents of T are mapped, designate for slurping (we only slurp if parents are already slurped, iteratively)
3. Extract basic information about T and export as ROBOT template

Resources
- https://incatools.github.io/ontology-access-kit/
- https://incatools.github.io/ontology-access-kit/intro/tutorial02.html

todo: refactor to take in 'unmapped mapppable' terms i.e. reports/%_unmapped_terms.tsv instead of other params?
"""
import os
from argparse import ArgumentParser
from glob import glob
from typing import Dict, List, Set, Union

import pandas as pd
import yaml
from jinja2 import Template
from oaklib.implementations import ProntoImplementation
from oaklib.types import CURIE, URI

from utils import CACHE_DIR, DOCS_DIR, PREFIX, PROJECT_DIR, Term, _get_all_owned_terms, _get_next_available_mondo_id, \
    get_excluded_terms, get_mondo_term_ids, _load_ontology, SLURP_DIR


FILENAME_GLOB_PATTERN = '*.tsv'
PATH_GLOB_PATTERN = os.path.join(SLURP_DIR, FILENAME_GLOB_PATTERN)
THIS_DOCS_DIR = os.path.join(DOCS_DIR, 'reports')
OUT_PATH = os.path.join(THIS_DOCS_DIR, 'migrate.md')
JINJA_MAIN_PAGE = """# Migratable terms
{{ stats_markdown_table }}

### Codebook
`Ontology`: Name of ontology    
`Tot`: Total terms migratable

### Definitions
**Migratable term**: A term owned by the given ontology but unmapped in Mondo, which has either no parents, or if it has 
parents, all of its parents have already been mapped in Mondo.

### Workflows
To run the workflow that creates this data, refer to the [workflows documentation](../developer/workflows.md)."""
JINJA_ONTO_PAGES = """## {{ ontology_name }}
[Interactive FlatGithub table](https://flatgithub.com/monarch-initiative/mondo-ingest?filename={{ source_data_path }})

### Migratable terms
{{ table }}"""
ROBOT_TEMPLATE_HEADER = {
    'mondo_id': 'ID', 'mondo_label': 'LABEL', 'xref': 'A oboInOwl:hasDbXref',
    'xref_source': '>A oboInOwl:source SPLIT=|', 'original_label': '', 'definition': 'A IAO:0000115', 'parents': 'SC %'}

def _check_parent_conditions(t: Term, sssom_object_ids: Set[Union[URI, CURIE]], sssom_df: pd.DataFrame) -> bool:
    """This is an optional, stricter check on slurp candidacy / order.

    For a term to be immediately migratable, it must either (a) have no parents, or (b) have no valid parents in Mondo
    (i.e. all of its parent terms are marked obsolete in Mondo), or (c) all its parents must be mapped, and at least 1
    of those parent's mappings must be one of `skos:exactMatch` or `skos:NarrowMatch`."""
    obsolete_mondo_parent_ids = []
    qualified_parent_mondo_ids = []
    all_parents_mapped = True
    no_parents: bool = not t.direct_owned_parent_curies
    for parent_curie in t.direct_owned_parent_curies:
        if parent_curie not in sssom_object_ids:
            all_parents_mapped = False
        if parent_curie in sssom_object_ids:
            parent: Dict = sssom_df[sssom_df['object_id'] == parent_curie].to_dict('records')[0]
            parent_mondo_id, parent_mondo_label = parent['subject_id'], parent['subject_label']
            if parent_mondo_label.startswith('obsolete'):
                obsolete_mondo_parent_ids.append(parent_mondo_id)
            elif parent['predicate_id'] in ['skos:exactMatch', 'skos:narrowMatch']:
                qualified_parent_mondo_ids.append(parent_mondo_id)

    no_valid_mondo_parents: bool = len(t.direct_owned_parent_curies) == len(obsolete_mondo_parent_ids)
    return (all_parents_mapped and qualified_parent_mondo_ids) or no_parents or no_valid_mondo_parents


def slurp(
    ontology_path: str, onto_config_path: str, onto_exclusions_path: str, mondo_mappings_path: str, max_id: int,
    mondo_terms_path: str, slurp_dir_path: str, outpath: str, min_id: int = 0, use_cache=False,
    parent_conditions_on=False
) -> pd.DataFrame:
    """Run slurp pipeline for given ontology
    todo: Speed: tried on an older computer and it was indeed too slow. Has to do w/ term class / utils, probably.
    """
    # Read inputs
    ontology: ProntoImplementation = _load_ontology(ontology_path, use_cache)
    with open(onto_config_path, 'r') as stream:
        onto_config = yaml.safe_load(stream)
        owned_prefix_map: Dict[PREFIX, URI] = onto_config['base_prefix_map']
    sssom_df: pd.DataFrame = pd.read_csv(mondo_mappings_path, comment='#', sep='\t')
    excluded_terms: Set[CURIE] = get_excluded_terms(onto_exclusions_path)

    # Get next_mondo_id
    next_mondo_id = min_id
    slurp_files = [x for x in os.listdir(slurp_dir_path) if x.endswith('.tsv')]
    for f in slurp_files:
        slurp_df = pd.read_csv(os.path.join(slurp_dir_path, f), sep='\t')
        slurp_ids = [int(x.split(':')[1]) for x in list(slurp_df['mondo_id'])[1:]]
        next_mondo_id = max(next_mondo_id, max(slurp_ids) + 1) if slurp_ids else next_mondo_id

    # Get map of native IDs to existing slurp mondo IDs
    slurp_id_map: Dict[str, str] = {}
    if os.path.exists(outpath):
        this_slurp_df = pd.read_csv(outpath, sep='\t')
        for i, row in this_slurp_df[1:].iterrows():  # skip first row because it's a `robot` template sub-header
            slurp_id_map[row['xref']] = row['mondo_id']

    # mondo_term_ids: If I remember correctly, rationale is to avoid edge case where mondo IDs exist above min_id
    # todo: I think `mondo_term_ids` is now redundant with `slurp_id_map` usage and can probably now be deleted
    mondo_term_ids: Set[int] = get_mondo_term_ids(mondo_terms_path, slurp_id_map)

    # Intermediates
    owned_terms: List[Term] = _get_all_owned_terms(
        ontology=ontology, owned_prefix_map=owned_prefix_map, ontology_path=ontology_path, cache_dir_path=CACHE_DIR,
        onto_config_path=onto_config_path, use_cache=use_cache)
    sssom_object_ids: Set[Union[URI, CURIE]] = set(sssom_df['object_id'])  # Usually CURIE, but spec allows URI
    unmapped_terms: List[Term] = [x for x in owned_terms if x.curie not in sssom_object_ids]
    slurp_candidates = [x for x in unmapped_terms if x.curie not in excluded_terms]  # remove exclusions

    # Determine slurpable / migratable terms
    # To be migratable, the term (i) must not already be mapped, (ii) must not be excluded (e.g. not in
    # `reports/%_term_exclusions.txt`), and (iii) must not be deprecated / obsolete. Then, if `parent_conditions_on`,
    # we will also (iv, optional) `_check_parent_conditions()`.
    terms_to_slurp: List[Dict[str, str]] = []
    for t in slurp_candidates:
        if parent_conditions_on and not _check_parent_conditions(t, sssom_object_ids, sssom_df):
            continue
        if t.curie in slurp_id_map:
            mondo_id = slurp_id_map[t.curie]
        else:
            next_mondo_id, mondo_term_ids = _get_next_available_mondo_id(next_mondo_id, max_id, mondo_term_ids)
            mondo_id = 'MONDO:' + str(next_mondo_id).zfill(7)  # leading 0-padding
        mondo_label = t.label.lower() if t.label else ''
        terms_to_slurp.append({
            'mondo_id': mondo_id, 'mondo_label': mondo_label, 'xref': t.curie, 'xref_source': 'MONDO:equivalentTo',
            'original_label': t.label if t.label else '', 'definition': t.definition if t.definition else '',
            'parents': '|'.join([p for p in t.direct_owned_parent_curies])})

    # Sort, add robot row, save and return
    result = pd.DataFrame(terms_to_slurp)
    if len(result) > 0:
        result = result.sort_values(
            ['mondo_id', 'mondo_label', 'xref', 'xref_source', 'original_label', 'definition', 'parents'])
    result = pd.concat([pd.DataFrame([ROBOT_TEMPLATE_HEADER]), result])
    result.to_csv(outpath, sep='\t', index=False)
    return result


def slurp_docs():
    """Update documentation with info about slurp / migrate"""
    # Read sources
    # todo: what's best way to gather ontology names? There's a way in the makefile. Is this not right to do here?
    paths: List[str] = glob(PATH_GLOB_PATTERN)

    # Create pages & build stats
    stats_rows: List[Dict] = []
    for path in paths:
        ontology_name = os.path.basename(path).replace(FILENAME_GLOB_PATTERN[1:], '')
        ontology_page_relpath = f'./migrate_{ontology_name.lower()}.md'
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
            'Tot': f"{len(df) - 1:,}",  # -1 because robot template subheader
        })

    # Stats: save
    stats_df = pd.DataFrame(stats_rows).sort_values(['Tot'], ascending=False)
    instantiated_str: str = Template(JINJA_MAIN_PAGE).render(stats_markdown_table=stats_df.to_markdown(index=False))
    with open(OUT_PATH, 'w') as f:
        f.write(instantiated_str)


# todo: add way to not read from cache, but write to cache
def cli():
    """Command line interface."""
    parser = ArgumentParser(prog='Migrate', description='Integrate new terms from other ontologies into Mondo.')
    # slurp_() args
    parser.add_argument(
        '-o', '--ontology-path',
        help='Required. Path to ontology file, e.g. an `.owl` file.')
    parser.add_argument(
        '-c', '--onto-config-path',
        help='Required. Path to a config `.yml` for the ontology which contains a `base_prefix_map` which contains a '
             'list of prefixes owned by the ontology. Used to filter out terms.')
    parser.add_argument(
        '-e', '--onto-exclusions-path',
        help='Required. Path to a text file, e.g with naming pattern `<ontology>_term_exclusions.txt` which contains a '
             'list of  terms that are exclueded from inclusion into Mondo. Should be a plain file of line break '
             'delimited terms; only 1 column with no column header.')
    parser.add_argument(
        '-s', '--mondo-mappings-path',
        help='Required. Path to file containing all known Mondo mappings, in SSSOM format.')
    parser.add_argument(
        '-m', '--min-id',
        help='The Mondo ID from which we want to begin to possibly allow for assignment of new Mondo IDs for any'
             ' unslurped terms. Only necessary if no slurp/%.tsv\'s exist. Otherwise, will be ignored, and the min-id '
             'will be determined based on the highest ID assigned in the slurp/%.tsv\'s.')
    parser.add_argument(
        '-M', '--max-id',
        help='Required. The max Mondo ID we should ever assign for any unslurped terms.')
    parser.add_argument(
        '-t', '--mondo-terms-path',
        help='Required. Path to a file that contains a list of all Mondo terms.')
    parser.add_argument(
        '-l', '--slurp-dir-path',
        help='Required. Path to `slurp/` dir where other slurp files are checked so that any assigned Mondo IDs are not'
             ' re-used')
    parser.add_argument(
        '-O', '--outpath',
        help='Required. Path to save the output slurp `.tsv` file, containing list of new terms to integrate to Mondo.')
    parser.add_argument(
        '-C', '--use-cache', action='store_true', default=False,
        help='Use cached ontology and owned_terms objects?')
    parser.add_argument(
        '-p', '--parent-conditions-on', action='store_true', default=False,
        help='If this flag is not present, the end result is that the terms in `slurp/%.tsv` will be exactly the same '
             'as `reports/%_unmapped_terms.tsv`, which is the same as the list of terms in '
             '`reports/%_mapping_status.tsv` where `is_mapped`, `is_deprecated`, and `is_obsolete` are `False`. If this'
             ' flag is present, then for a term to be migratable it must either (a) have no parents, or (b) have no '
             'valid parents in Mondo (i.e. all of its parent terms are marked obsolete in Mondo), or (c) all its '
             'parents must be mapped, and at least 1 of those parent\'s mappings must be one of `skos:exactMatch` or '
             '`skos:NarrowMatch`.')
    # slurp_docs() args
    parser.add_argument(
        '-d', '--docs', action='store_true',
        help='Generates documentation based on any existing "slurp" / "migrate" tables.')
    d: Dict = vars(parser.parse_args())
    # Reformatting
    # todo: Paths: Convert to absolute paths, as I've done before? Or expect always be run from src/ontology and ok?
    d['min_id'] = int(d['min_id']) if d['min_id'] else None
    d['max_id'] = int(d['max_id']) if d['max_id'] else None
    docs = d.pop('docs')
    if docs and any([d[x] for x in d]):
        raise RuntimeError('If --docs, don\'t provide any other arguments.')
    return slurp_docs() if docs else slurp(**d)


if __name__ == '__main__':
    cli()
