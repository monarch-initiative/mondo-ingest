"""Convert SSSOM to ROBOT template."""
from argparse import ArgumentParser
from pathlib import Path
from typing import Dict, Union

import pandas as pd
from sssom import MappingSetDataFrame
from sssom.parsers import parse_sssom_table

ROBOT_ROW = {
    'subject_id': 'ID',
    'subject_label': '',
    'object_id': 'A oboInOwl:hasDbXref',
    'object_label': '',
    'equivalence': '>A oboInOwl:source',
    'ORCID': '>A oboInOwl:source SPLIT=|',
}


def sssom_to_robot_template(inpath: Union[str, Path], outpath: Union[str, Path]):
    """Convert SSSOM to ROBOT template."""
    msdf: MappingSetDataFrame = parse_sssom_table(inpath)
    df: pd.DataFrame = msdf.df

    # Filter
    df = df[df['predicate_id'] == 'skos:exactMatch']

    # Conversion
    df = df[['subject_id', 'subject_label', 'object_id', 'object_label']].sort_values(['subject_id', 'object_id'])
    df['equivalence'] = 'MONDO:equivalentTo'
    df['ORCID'] = '|'.join(msdf.metadata['creator_id'])
    df = pd.concat([pd.DataFrame([ROBOT_ROW]), df])

    # Write
    df.to_csv(outpath, sep='\t', index=False)


def cli():
    """Command line interface"""
    parser = ArgumentParser(
        prog='sssom-to-robot-template',
        description='Convert SSSOM to ROBOT template.')
    parser.add_argument(
        '-i', '--inpath', required=True, help='Path to input SSSOM TSV.')
    parser.add_argument(
        '-o', '--outpath', required=True, help='Path to output ROBOT template TSV.')
    d: Dict = vars(parser.parse_args())
    sssom_to_robot_template(**d)


if __name__ == '__main__':
    cli()