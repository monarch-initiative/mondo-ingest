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
    'equivalence': '>A oboInOwl:source',
    'author_id': '>A oboInOwl:source SPLIT=|',
    'mapping_provider': '>A oboInOwl:source',
    'object_label': '',
}
PRED_MAP = {
    'skos:relatedMatch': 'MONDO:relatedTo',
    'skos:exactMatch': 'MONDO:equivalentTo',
    'skos:broadMatch': 'MONDO:mondoIsNarrowerThanSource',
}


def sssom_to_robot_template(inpath: Union[str, Path], outpath: Union[str, Path]):
    """Convert SSSOM to ROBOT template."""
    msdf: MappingSetDataFrame = parse_sssom_table(inpath)
    df: pd.DataFrame = msdf.df

    # Conversion
    df['equivalence'] = df['predicate_id'].map(lambda pred: PRED_MAP.get(pred, ''))
    df = df[['subject_id', 'subject_label', 'object_id', 'equivalence', 'object_label']]\
        .sort_values(['subject_id', 'object_id'])
    df['author_id'] = '|'.join(msdf.metadata['creator_id'])
    df['mapping_provider'] = msdf.metadata['mapping_provider']
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