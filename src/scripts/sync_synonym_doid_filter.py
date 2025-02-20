"""DO filtration: For now we are filtering out all DOID terms that are not either: (a) created from rdfs:label, or (b) substantiated by another source."""
import logging
import os
import re
import sys
from argparse import ArgumentParser
from pathlib import Path
from typing import Union, List, Tuple, Set, Dict, Any, Callable

import curies
import pandas as pd
import yaml
from oaklib import get_adapter
from oaklib.implementations import SqlImplementation
from oaklib.types import CURIE, PRED_CURIE, URI

# TODO: extract all the DO terms
# TODO: remove non exact
# TODO: allow label
# TODO: allow if backed up by another -added source
def sync_synonyms_do_filter(
    added_path: Union[Path, str], updated_path: Union[Path, str], outpath: Union[Path, str],
):
    """Filter DO terms

    Filter all DO terms from that are not either: (a) created from rdfs:label, or (b) substantiated by another source.
    """
    pass


def cli():
    """Command line interface."""
    parser = ArgumentParser(
        prog='sync-synonyms-do-filtration',
        description='Filter all DO terms from that are not either: (a) created from rdfs:label, or (b) substantiated '
            'by another source.')
    parser.add_argument(
        '-a', '--added-path', required=True,
        help='Incoming -added synonyms to be checked against to determine if the potential new DO synonym is newly '
             'substantiated by another source.')
    parser.add_argument(
        '-u', '--updated-path', required=True,
        help='Incoming -updated synonyms to be checked against to determine if the potential new DO synonym is newly '
             'substantiated by another source.')
    parser.add_argument(
        '-o', '--outpath', required=True, help='Output path for filtered DO -added synonyms.')
    sync_synonyms_do_filter(**vars(parser.parse_args()))


if __name__ == '__main__':
    cli()
