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


def slurp(
    ontology_path: str, onto_config_path: str, onto_exclusions_path: str, mondo_mappings_path: str, max_id: int,
    mondo_terms_path: str, slurp_dir_path: str, outpath: str, min_id: int = 0, use_cache=False
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
        next_mondo_id = max(next_mondo_id, max(slurp_ids) + 1)

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
    owned_term_curies: List[CURIE] = [x.curie for x in owned_terms]
    sssom_object_ids: Set[Union[URI, CURIE]] = set(sssom_df['object_id'])  # Usually CURIE, but spec allows URI
    unmapped_terms: List[Term] = [x for x in owned_terms if x.curie not in sssom_object_ids]
    slurp_candidates = [x for x in unmapped_terms if x.curie not in excluded_terms]  # remove exclusions

    # Temp: ORDO troubleshooting
    ontology_name = os.path.basename(ontology_path).replace('.owl', '')
    mapping_status_path = os.path.join('reports', f'{ontology_name}_mapping_status.tsv')
    mapping_status_df = pd.read_csv(mapping_status_path, sep='\t')
    mapping_status_df['possible_slurp_candidate'] = False
    mapping_status_dict: Dict[str, Dict] = {x['subject_id']: x for x in mapping_status_df.to_dict('records')}

    # Determine slurpable terms
    # Migratable term: A term owned by the given ontology but unmapped in Mondo, which has either no parents, or if it
    # has parents, all of its parents have already been mapped in Mondo.
    terms_to_slurp: List[Dict[str, str]] = []
    for t in slurp_candidates:
        # TODO: is this wrong? it looks like in my logic if any parent term is qualified, the term is slurpable. below says 1+ OK, but above comments ays all need to be mapped
        #  - i should only have one comment. the one above or below, and make sure it makes sense
        #  - and add a note about the fact that obsolete parents don't count
        # TODO: also wrong? did I already filter by exact or narrow match?
        #  - it looks like in reality, all of the SSSOM predicates in the file are exactMatch. But I should program this logic in anyway
        # If all T.parents mapped, and 1+ is an exact or narrow match and non obsolete, designate T for slurping
        # (i.e. only slurp if parents are already slurped)
        qualified_parent_mondo_ids = []
        parent_obsolete_statuses = []
        parent_mapping_predicates = []
        parent_labels = []
        no_parents: bool = not t.direct_owned_parent_curies
        all_parents_mapped = True
        for parent_curie in t.direct_owned_parent_curies:
            # Conversely, if any of T.parents is unmapped, T is not to be slurped
            if parent_curie in sssom_object_ids:
                parent: Dict = sssom_df[sssom_df['object_id'] == parent_curie].to_dict('records')[0]
                parent_mondo_id, parent_mondo_label = parent['subject_id'], parent['subject_label']
                # Temp
                parent_mapping_predicates.append(parent['predicate_id'])
                parent_labels.append(parent_mondo_label)
                if not parent_mondo_label.startswith('obsolete'):
                    # Temp
                    parent_obsolete_statuses.append(False)
                    qualified_parent_mondo_ids.append(parent_mondo_id)
                # Temp
                else:
                    parent_obsolete_statuses.append(True)
            # Temp
            else:
                parent_mapping_predicates.append('unmapped')
                parent_labels.append('unknown')

            # todo: is this supposed to break the outer loop or the inner loop? i think maybe replacing the `break` with `all_parents_mapped` is better
            if parent_curie not in sssom_object_ids and parent_curie in owned_term_curies:
                # TODO Impt!: If this break clause is indeed correct, and indeed we need all parents need to be mapped, then this line below needs to be added to the general slurp
                #  because it will prevent the slurp of a term that has a parent that is not mapped
                all_parents_mapped = False
                # todo: break should probabl be kept for general slurp; but commenting it out here so that i can collect info about all parents
                #  - or maybe i just want to use the `all_parents_mapped` var instead of breaking
                # break

        if all_parents_mapped and (qualified_parent_mondo_ids or no_parents):
            if t.curie in slurp_id_map:
                mondo_id = slurp_id_map[t.curie]
            else:
                next_mondo_id, mondo_term_ids = _get_next_available_mondo_id(next_mondo_id, max_id, mondo_term_ids)
                mondo_id = 'MONDO:' + str(next_mondo_id).zfill(7)  # leading 0-padding
            mondo_label = t.label.lower() if t.label else ''
            terms_to_slurp.append({
                'mondo_id': mondo_id, 'mondo_label': mondo_label, 'xref': t.curie, 'xref_source': 'MONDO:equivalentTo',
                'original_label': t.label if t.label else '', 'definition': t.definition if t.definition else '',
                'parents': '|'.join(qualified_parent_mondo_ids)})
        # Temp: ORDO troubleshooting
        mapping_status_dict[t.curie]['possible_slurp_candidate'] = True  # unmapped, not excluded, not deprecated
        mapping_status_dict[t.curie]['parents'] = '|'.join(t.direct_owned_parent_curies)
        mapping_status_dict[t.curie]['parent_labels'] = '|'.join(parent_labels)
        mapping_status_dict[t.curie]['qualified_parent_mondo_ids'] = '|'.join(qualified_parent_mondo_ids)
        mapping_status_dict[t.curie]['parent_mapping_predicates'] = '|'.join(parent_mapping_predicates)
        mapping_status_dict[t.curie]['parent_obsolete'] = '|'.join([str(x) for x in parent_obsolete_statuses])
        mapping_status_dict[t.curie]['all_parents_mapped'] = all_parents_mapped
        if qualified_parent_mondo_ids or no_parents:
            mapping_status_dict[t.curie]['actual_slurp_candidate'] = True  # 1+ qualified parents or no parents
        else:
            mapping_status_dict[t.curie]['actual_slurp_candidate'] = False

    # Temp: ORDO troubleshooting
    mapping_status_path2 = mapping_status_path.replace('.tsv', '-with_slurp_info.tsv')
    mapping_status_df2 = pd.DataFrame(mapping_status_dict.values())
    mapping_status_df2 = mapping_status_df2.sort_values(
        ['actual_slurp_candidate', 'possible_slurp_candidate', 'is_mapped', 'is_excluded', 'is_deprecated', 'subject_id'],
        ascending=[False, False, True, True, True, True])
    mapping_status_df2.to_csv(mapping_status_path2, sep='\t', index=False)

    # todo: if running this, will have mondo_id KeyError. i know what to do and will fix that in separate PR
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
