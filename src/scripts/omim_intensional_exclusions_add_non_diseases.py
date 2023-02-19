"""Add non-diseases to OMIM intensional exclusions.

Resources
- GitHub issue: https://github.com/monarch-initiative/mondo-ingest/issues/110
- GitHub PR: https://github.com/monarch-initiative/mondo-ingest/pull/203
"""
from argparse import ArgumentParser

import pandas as pd


def omim_intensional_exclusions_add_non_diseases(
    intensional_exclusions_path: str, non_disease_exclusions_path: str
) -> pd.DataFrame:
    """Add non-diseases to OMIM intensional exclusions."""
    # Read sources
    ex_df = pd.read_csv(intensional_exclusions_path, sep='\t').fillna('')
    nd_ex_df = pd.read_csv(non_disease_exclusions_path, sep='\t').fillna('')
    # Transform
    df = pd.concat([ex_df, nd_ex_df]).drop_duplicates(subset=['term_id', 'exclusion_reason'], keep='first')\
        .reset_index(drop=True).sort_values(['exclusion_reason', 'term_id'])
    # Save & return
    df.to_csv(intensional_exclusions_path, index=False, sep='\t')
    return df


def cli():
    """Command line interface"""
    parser = ArgumentParser(description='Add non-diseases to OMIM intensional exclusions.')
    parser.add_argument(
        '-x', '--intensional-exclusions-path', required=True,
        help='Path to intensional exclusions TSV. This is an input parameter, as well as the path where the output will'
             ' be saved to / overwritten.')
    parser.add_argument(
        '-d', '--non-disease-exclusions-path', required=True,
        help='Path to TSV containing non-disease terms, in the format of an exclusions TSV.')
    omim_intensional_exclusions_add_non_diseases(**vars(parser.parse_args()))


if __name__ == '__main__':
    cli()
