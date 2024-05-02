"""Creates a ROBOT template to update mondo terms with the correct ORDO subset annotation."""
from argparse import ArgumentParser

import pandas as pd

from utils import remove_angle_brackets


SUBSET_MAP = {
    'Orphanet:557493': 'http://purl.obolibrary.org/obo/mondo#ordo_disease',  # disorder
    'Orphanet:557492': 'http://purl.obolibrary.org/obo/mondo#ordo_group_of_disorders',  # group of disorders
    'Orphanet:557494': 'http://purl.obolibrary.org/obo/mondo#ordo_clinical_subtype',  # subtype of a disorder
}
ROBOT_TEMPLATE_HEADER = {
    'mondo_id': 'ID',
    'ordo_id': 'A oboInOwl:hasDbXref',
    'subset': 'A oboInOwl:inSubset',
}


def create_ordo_subsets_robot_template(
    class_subsets_tsv_path: str, mondo_mappings_path: str, outpath: str,
):
    """Creates a ROBOT template to update mondo terms with the correct ORDO subset annotation."""
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
        df[fld] = df[fld].map(lambda x: x.replace('http://www.orpha.net/ORDO/Orphanet_', 'Orphanet:'))

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


def cli():
    """Command line interface."""
    parser = ArgumentParser('Creates a ROBOT template to update mondo terms with the correct ORDO subset annotation.')
    parser.add_argument(
        '-c', '--class-subsets-tsv-path', required=True,
        help='Path to TSV containing results of a SPARQL query to get all ORDO subsets, by class.')
    parser.add_argument(
        '-m', '--mondo-mappings-path', required=True,
        help='Path to TSV containing all known Mondo mappings, in SSSOM format.')
    parser.add_argument('-o', '--outpath', required=True, help='Path to save ROBOT template TSV.')
    create_ordo_subsets_robot_template(**vars(parser.parse_args()))


if __name__ == '__main__':
    cli()
