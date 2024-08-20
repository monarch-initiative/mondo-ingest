"""Slurp migration pipeline

Basically, we:
1. Look at all unmapped terms T
2. If all of parents of T are mapped, designate for slurping (we only slurp if parents are already slurped, iteratively)
3. Extract basic information about T and export as ROBOT template

Resources
- https://incatools.github.io/ontology-access-kit/
- https://incatools.github.io/ontology-access-kit/intro/tutorial02.html
"""
import os
from argparse import ArgumentParser
from glob import glob
from pathlib import Path
from typing import Dict, List, Set, Union

import pandas as pd
from jinja2 import Template
from oaklib.implementations import ProntoImplementation
from oaklib.types import CURIE, URI

from ordo_subsets import get_formatted_subsets_df
from utils import CACHE_DIR, DOCS_DIR, METADATA_DIR, PREFIX, PROJECT_DIR, Term, get_all_owned_terms, \
    _get_next_available_mondo_id, \
    get_mondo_term_ids, _load_ontology, SLURP_DIR, get_owned_prefix_map, TEMP_DIR

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
    'mondo_id': 'ID',
    'mondo_label': 'LABEL',
    'xref': 'A oboInOwl:hasDbXref',
    'xref_source': '>A oboInOwl:source SPLIT=|',
    'original_label': '',
    'definition': 'A IAO:0000115',
    'parents': 'SC %'
}

def _valid_parent_conditions(
    parents: List[CURIE], mapped: Set[CURIE], excluded: Set[CURIE], obsolete: Set[CURIE]
) -> bool:
    """This is an optional, stricter check on slurp candidacy / order.

    For a term to be immediately migratable, it must either (a) have no parents, or (b) all of its parents must be
    mapped, obsolete, or excluded"""
    return not parents or all([(x in mapped) or (x in excluded) or (x in obsolete) for x in parents])


def slurp(
    ontology_path: str, onto_config_path: str, mondo_mappings_path: str, mapping_status_path: str,
    mondo_terms_path: str, slurp_dir_path: str, outpath: str, max_id: int, min_id: int = 0,
    parent_conditions_off=False, use_cache=False
) -> pd.DataFrame:
    """Run slurp pipeline for given ontology
    todo: Speed: tried on an older computer and it was indeed too slow. Has to do w/ term class / utils, probably.
    """
    # Read inputs
    ontology: ProntoImplementation = _load_ontology(ontology_path, use_cache)
    owned_prefix_map: Dict[PREFIX, URI] = get_owned_prefix_map(onto_config_path)
    sssom_df: pd.DataFrame = pd.read_csv(mondo_mappings_path, comment='#', sep='\t')
    mapping_status_df: pd.DataFrame = pd.read_csv(mapping_status_path, sep='\t')

    # Related to assignment of new identifiers
    # - Get next_mondo_id
    next_mondo_id = min_id
    slurp_files = [x for x in os.listdir(slurp_dir_path) if x.endswith('.tsv')]
    for f in slurp_files:
        slurp_df = pd.read_csv(os.path.join(slurp_dir_path, f), sep='\t')
        slurp_ids = [int(x.split(':')[1]) for x in list(slurp_df['mondo_id'])[1:]]
        next_mondo_id = max(next_mondo_id, max(slurp_ids) + 1) if slurp_ids else next_mondo_id
    # - Get map of native IDs to existing slurp mondo IDs
    slurp_id_map: Dict[str, str] = {}
    if os.path.exists(outpath):
        this_slurp_df = pd.read_csv(outpath, sep='\t')
        for i, row in this_slurp_df[1:].iterrows():  # skip first row because it's a `robot` template sub-header
            slurp_id_map[row['xref']] = row['mondo_id']
    # - mondo_term_ids: If I remember correctly, rationale is to avoid edge case where mondo IDs exist above min_id
    # todo: `mondo_term_ids` might now redundant with `slurp_id_map` usage. if so, can delete
    mondo_term_ids: Set[int] = get_mondo_term_ids(mondo_terms_path, slurp_id_map)

    # Intermediates
    excluded: Set[CURIE] = set(mapping_status_df[mapping_status_df['is_excluded'] == True]['subject_id'])
    mapped: Set[CURIE] = set(mapping_status_df[mapping_status_df['is_mapped'] == True]['subject_id'])
    obsolete: Set[CURIE] = set(mapping_status_df[mapping_status_df['is_deprecated'] == True]['subject_id'])
    owned_terms: List[Term] = get_all_owned_terms(  # todo can simplify. see comment on function
        ontology, owned_prefix_map, ontology_path, cache_dir_path=CACHE_DIR,
        ontology_name=os.path.basename(onto_config_path).replace(".yml", "").replace(".yaml", ""), use_cache=use_cache)
    slurp_candidates: List[Term] = \
        [t for t in owned_terms if all([t.curie not in y for y in [excluded, mapped, obsolete]])]
    match_types: Dict = {}
    mondo_id_map: Dict = {}
    for row in sssom_df.itertuples():
        # noinspection PyUnresolvedReferences
        match_types[row.object_id] = row.predicate_id
        # noinspection PyUnresolvedReferences
        mondo_id_map[row.object_id] = row.subject_id

    # Determine slurpable / migratable terms
    # To be migratable, the term (i) must not already be mapped, (ii) must not be excluded (e.g. not in
    # `reports/%_term_exclusions.txt`), and (iii) must not be deprecated / obsolete. Then, unless
    # `parent_conditions_off`, will also (iv) check parent conditions. For information about parent conditions, see the
    # help text for `--parent-conditions-off`.
    terms_to_slurp: List[Dict[str, str]] = []
    slurp_candidates = [t for t in slurp_candidates if _valid_parent_conditions(
        t.direct_owned_parent_curies, mapped, excluded, obsolete)] if not parent_conditions_off else slurp_candidates
    for t in slurp_candidates:
        if t.curie in slurp_id_map:
            mondo_id = slurp_id_map[t.curie]
        else:
            next_mondo_id, mondo_term_ids = _get_next_available_mondo_id(next_mondo_id, max_id, mondo_term_ids)
            mondo_id = 'MONDO:' + str(next_mondo_id).zfill(7)  # leading 0-padding
        mondo_label = t.label.lower() if t.label else ''
        qualified_parents = [p for p in t.direct_owned_parent_curies
                             if p in match_types and match_types[p] in ['skos:exactMatch', 'skos:narrowMatch']]
        qualified_mondo_parents = [mondo_id_map[p] for p in qualified_parents if p in mondo_id_map]
        terms_to_slurp.append({
            'mondo_id': mondo_id, 'mondo_label': mondo_label, 'xref': t.curie, 'xref_source': 'MONDO:equivalentTo',
            'original_label': t.label if t.label else '', 'definition': t.definition if t.definition else '',
            # if not in match_types, this should mean term is excluded or obsolete
            'parents': '|'.join(qualified_mondo_parents)})

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
        # todo: duplicated code fragment w/ deprecated_in_mondo_docs()
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


# todo: ideally, these would also be passed in through the makefile, but that requires refactor of CLI to a more
#  complex one, like Click, to allow for sub-commands.
def slurp_ordo_mods(
    slurp_path: Union[str, Path] = os.path.join(SLURP_DIR, 'ordo.tsv'),
    subsets_path: Union[str, Path] = os.path.join(TEMP_DIR, 'ordo-subsets.tsv'),
    onto_config_path: Union[str, Path] = os.path.join(METADATA_DIR, 'ordo.yml'),
):
    """Adds rare_disease_subset column to the ORDO migration TSV."""
    # Read inputs
    df: pd.DataFrame = pd.read_csv(slurp_path, sep='\t')
    df_subsets: pd.DataFrame = get_formatted_subsets_df(subsets_path, onto_config_path)
    df_subsets = df_subsets[['ordo_id', 'subset_ordo_class_label']]\
        .rename(columns={'ordo_id': 'xref', 'subset_ordo_class_label': 'subset'})

    # Edge case: re-running
    if 'subset' in df.columns:
        del df['subset']

    # JOIN
    df = pd.merge(df, df_subsets, how='left', on='xref')
    df.to_csv(slurp_path, sep='\t', index=False)


# TODO: remove cache? probably not needed after mapping status
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
        '-S', '--mapping-status-path',
        help='Required. A TSV with a list of all terms and columns: subject_id, subject_label, is_mapped, is_excluded, '
             'is_deprecated.')
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
        '-p', '--parent-conditions-off', action='store_true', default=False,
        help='If this flag is present, the end result is that the terms in `slurp/%.tsv` will be exactly the same '
             'as `reports/%_unmapped_terms.tsv`, which is the same as the list of terms in '
             '`reports/%_mapping_status.tsv` where `is_mapped`, `is_deprecated`, and `is_obsolete` are `False`. If this'
             ' flag is not present, then for a term to be migratable it must either (a) have no parents, or (b) have '
             'no valid parents in Mondo (i.e. all of its parent terms are marked obsolete in Mondo), or (c) all its '
             'parents must be mapped, and at least 1 of those parent\'s mappings must be one of `skos:exactMatch` or '
             '`skos:NarrowMatch`.')
    # slurp_docs() args
    parser.add_argument(
        '-d', '--docs', action='store_true',
        help='Generates documentation based on any existing "slurp" / "migrate" tables.')
    # slurp_ordo_mods() args
    parser.add_argument(
        '-r', '--ordo-mods', action='store_true', help='Adds rare_disease_subset column to the ORDO migration TSV.')
    d: Dict = vars(parser.parse_args())
    # Reformatting
    # todo: Paths: Convert to absolute paths, as I've done before? Or expect always be run from src/ontology and ok?
    d['min_id'] = int(d['min_id']) if d['min_id'] else None
    d['max_id'] = int(d['max_id']) if d['max_id'] else None
    # Route & run
    run_docs, run_ordo = d.pop('docs'), d.pop('ordo_mods')
    if run_docs:
        if any([d[x] for x in d]) or run_ordo:
            raise RuntimeError('If running --docs, don\'t provide any other arguments.')
        return slurp_docs()
    elif run_ordo:
        if any([d[x] for x in d]) or run_docs:
            raise RuntimeError('If running --ordo-mods, don\'t provide any other arguments.')
        return slurp_ordo_mods()
    slurp(**d)


if __name__ == '__main__':
    cli()
