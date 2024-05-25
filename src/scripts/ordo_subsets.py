"""Creates a ROBOT template to update mondo terms with the correct ORDO subset annotation."""
from argparse import ArgumentParser
from pathlib import Path
from typing import Union

import curies
import pandas as pd

from utils import remove_angle_brackets, get_converter

SUBSET_MAP = {
    'Orphanet:557493': 'http://purl.obolibrary.org/obo/mondo#ordo_disorder',  # disorder
    'Orphanet:557492': 'http://purl.obolibrary.org/obo/mondo#ordo_group_of_disorders',  # group of disorders
    'Orphanet:557494': 'http://purl.obolibrary.org/obo/mondo#ordo_subtype_of_a_disorder',  # subtype of a disorder
}
ROBOT_TEMPLATE_HEADER = {
    'mondo_id': 'ID',
    'subset': 'A oboInOwl:inSubset',
    'ordo_id': '>A oboInOwl:source',
}


def create_ordo_subsets_robot_template(
    class_subsets_tsv_path: Union[str, Path], mondo_mappings_path: Union[str, Path], onto_config_path: Union[str, Path],
    outpath: Union[str, Path],
) -> pd.DataFrame:
    """Creates a ROBOT template to update mondo terms with the correct ORDO subset annotation."""
    conv = curies.Converter = get_converter(onto_config_path)
    
    # Read: mondo.sssom.tsv
    mondo_df = pd.read_csv(mondo_mappings_path, sep='\t', comment='#').rename(columns={
        'subject_id': 'mondo_id',
        'subject_label': 'mondo_label',
    })
    # - keep only exact matches
    mondo_df = mondo_df[mondo_df['predicate_id'] == 'skos:exactMatch']

    # Read: ORDO class subsets query results
    df = pd.read_csv(class_subsets_tsv_path, sep='\t').rename(columns={
        '?cls': 'ordo_id',
        '?lbl': 'ordo_label',
        '?grp': 'subset_ordo_class_id',
        '?grp_lbl': 'subset_ordo_class_label',
    }).sort_values(['ordo_id', 'ordo_label'])
    # - remove duplicate rows where labels are a specific language variation, e.g. @en
    #   this alternative works as of 2024/05/02, but is potentially trepidacious:
    # df2 = df.drop_duplicates(subset=['ordo_id'], keep='last')
    df['label_has_lang_variation'] = df['ordo_label'].map(lambda label: '@' in label)
    df = df[~df['label_has_lang_variation']]
    del df['label_has_lang_variation']  # this gets dropped later, but w/e

    # Preprocess
    for fld in ['ordo_id', 'subset_ordo_class_id']:
        # - Strip annoying angle brackets from URIs
        df[fld] = df[fld].map(remove_angle_brackets)
        # - Compress class IDs
        df[fld] = df[fld].map(lambda x: conv.compress(x))

    # Map to mondo subset IDs
    df['subset'] = df['subset_ordo_class_id'].map(SUBSET_MAP)

    # JOIN to get Mondo IDs
    df = df.merge(mondo_df, how='inner', left_on='ordo_id', right_on='object_id')

    # Column order, column filtering, and sorting
    df = df[['mondo_id', 'ordo_id', 'subset', 'mondo_label', 'ordo_label']]\
        .sort_values(['mondo_id', 'ordo_id'])

    # Save & return
    df_out = pd.concat([pd.DataFrame([ROBOT_TEMPLATE_HEADER]), df])
    df_out.to_csv(outpath, sep='\t', index=False)
    return df


def cli():
    """Command line interface."""
    parser = ArgumentParser('Creates a ROBOT template to update mondo terms with the correct ORDO subset annotation.')
    parser.add_argument(
        '-C', '--class-subsets-tsv-path', required=True,
        help='Path to TSV containing results of a SPARQL query to get all ORDO subsets, by class.')
    parser.add_argument(
        '-m', '--mondo-mappings-path', required=True,
        help='Path to TSV containing all known Mondo mappings, in SSSOM format.')
    parser.add_argument(
        '-c', '--onto-config-path', required=True,
        help='Path to a config `.yml` for the ontology which contains a `base_prefix_map` which contains a '
             'list of prefixes owned by the ontology. Used to filter out terms.')
    parser.add_argument('-o', '--outpath', required=True, help='Path to save ROBOT template TSV.')
    create_ordo_subsets_robot_template(**vars(parser.parse_args()))


if __name__ == '__main__':
    cli()
