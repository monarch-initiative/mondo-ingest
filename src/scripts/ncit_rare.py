"""Creates a ROBOT template to update Mondo terms with the NCIt rare disease subset annotation."""
from argparse import ArgumentParser
from pathlib import Path
from typing import Union

import curies
import pandas as pd

from utils import remove_angle_brackets, get_converter

NCIT_RARE_SUBSET = 'http://purl.obolibrary.org/obo/mondo#ncit_rare'
ROBOT_TEMPLATE_HEADER = {
    'mondo_id': 'ID',
    'subset': 'A oboInOwl:inSubset',
    'ncit_id': '>A oboInOwl:source',
}


def get_formatted_ncit_rare_df(ncit_rare_tsv_path: Union[str, Path], onto_config_path: Union[str, Path]):
    """Read & reformat NCIt rare disease query results"""
    conv: curies.Converter = get_converter(onto_config_path)
    # Read
    df = pd.read_csv(ncit_rare_tsv_path, sep='\t').rename(columns={
        '?cls': 'ncit_id',
        '?lbl': 'ncit_label',
    }).sort_values(['ncit_id', 'ncit_label'])
    # - remove duplicate rows where labels are a specific language variation, e.g. @en
    df['label_has_lang_variation'] = df['ncit_label'].map(lambda label: '@' in str(label))
    df = df[~df['label_has_lang_variation']]
    del df['label_has_lang_variation']

    # Preprocess
    # - Strip annoying angle brackets from URIs
    df['ncit_id'] = df['ncit_id'].map(remove_angle_brackets)
    # - Compress class IDs
    df['ncit_id'] = df['ncit_id'].map(lambda x: conv.compress(x))

    # All terms get the same subset
    df['subset'] = NCIT_RARE_SUBSET
    return df


def create_ncit_rare_robot_template(
    ncit_rare_tsv_path: Union[str, Path], mondo_mappings_path: Union[str, Path], onto_config_path: Union[str, Path],
    outpath: Union[str, Path],
) -> pd.DataFrame:
    """Creates a ROBOT template to update Mondo terms with the NCIt rare disease subset annotation."""
    # Get mondo.sssom.tsv
    mondo_df = pd.read_csv(mondo_mappings_path, sep='\t', comment='#').rename(columns={
        'subject_id': 'mondo_id',
        'subject_label': 'mondo_label',
    })
    # - keep only exact matches
    mondo_df = mondo_df[mondo_df['predicate_id'] == 'skos:exactMatch']

    # Get NCIt rare disease TSV
    df: pd.DataFrame = get_formatted_ncit_rare_df(ncit_rare_tsv_path, onto_config_path)

    # JOIN to get Mondo IDs
    df = df.merge(mondo_df, how='inner', left_on='ncit_id', right_on='object_id')

    # Column order, column filtering, and sorting
    df = df[['mondo_id', 'ncit_id', 'subset', 'mondo_label', 'ncit_label']]\
        .sort_values(['mondo_id', 'ncit_id'])

    # Save & return
    df_out = pd.concat([pd.DataFrame([ROBOT_TEMPLATE_HEADER]), df])
    df_out.to_csv(outpath, sep='\t', index=False)
    return df


def cli():
    """Command line interface."""
    parser = ArgumentParser('Creates a ROBOT template to update Mondo terms with the NCIt rare disease subset annotation.')
    parser.add_argument(
        '-n', '--ncit-rare-tsv-path', required=True,
        help='Path to TSV containing results of a SPARQL query to get all NCIt rare disease descendants.')
    parser.add_argument(
        '-m', '--mondo-mappings-path', required=True,
        help='Path to TSV containing all known Mondo mappings, in SSSOM format.')
    parser.add_argument(
        '-c', '--onto-config-path', required=True,
        help='Path to a config `.yml` for the ontology which contains a `base_prefix_map` which contains a '
             'list of prefixes owned by the ontology. Used to filter out terms.')
    parser.add_argument('-o', '--outpath', required=True, help='Path to save ROBOT template TSV.')
    create_ncit_rare_robot_template(**vars(parser.parse_args()))


if __name__ == '__main__':
    cli()
