# Basic matching pipeline that takes in 

#Input:
# 1. MERGED_ONTOLOGY = tmp/merged.owl
# 2. SSSOM_CONFIG = metadata/mondo.sssom.config.yml
# 3. OUTPUT_SSSOM = mapping/mondo-sources-all-lexical.sssom.tsv

# I would try some basic things first:

# Use synonymiser
# Use oak.mapping() pipeline

import logging
from pathlib import Path
from typing import List
from oaklib.resource import OntologyResource
from oaklib.implementations.sqldb.sql_implementation import SqlImplementation
from oaklib.utilities.lexical.lexical_indexer import (
    create_lexical_index,
    lexical_index_to_sssom,
    load_mapping_rules,
    save_lexical_index
)
import pandas as pd
from sssom.writers import write_table
from sssom.io import get_metadata_and_prefix_map
import sys
from pathlib import Path
import click
import yaml
from sssom.constants import SUBJECT_ID, OBJECT_ID
from sssom.util import KEY_FEATURES, get_prefix_from_curie

SRC = Path(__file__).resolve().parents[1]
ONTOLOGY_DIR = SRC / "ontology"
OUT_INDEX_DB = ONTOLOGY_DIR / "tmp/merged.db.lexical.yaml"
# KEY_FEATURES = [SUBJECT_ID, OBJECT_ID]

input_argument = click.argument("input", required=True, type=click.Path())
output_option = click.option(
    "-o",
    "--output",
    help="Path for output file.",
    default=sys.stdout,
)

@click.group()
@click.option("-v", "--verbose", count=True)
@click.option("-q", "--quiet")

def main(verbose: int, quiet: bool):
    """Run the SSSOM CLI."""
    logger = logging.getLogger()
    if verbose >= 2:
        logger.setLevel(level=logging.DEBUG)
    elif verbose == 1:
        logger.setLevel(level=logging.INFO)
    else:
        logger.setLevel(level=logging.WARNING)
    if quiet:
        logger.setLevel(level=logging.ERROR)

@main.command()
@input_argument
@click.option(
    "-c",
    "--config",
    help="YAML file containing metadata.",
)
@click.option(
    "-r",
    "--rules",
    help="Ruleset for mapping.",
)
@output_option
def run(input:str, config: str, rules:str, output: str):
    # Implemented `meta` param in `lexical_index_to_sssom`
    # with open(config, "r") as f:
    #     sssom_yaml = yaml.safe_load(f)
    meta = get_metadata_and_prefix_map(config)
    with open(config, "r") as f:
        yml = yaml.safe_load(f)

    prefix_of_interest = yml['subject_prefixes']

    resource = OntologyResource(slug=f"sqlite:///{Path(input).absolute()}")
    oi = SqlImplementation(resource=resource)
    lexical_index = create_lexical_index(oi)
    save_lexical_index(lexical_index, OUT_INDEX_DB)

    if rules:
        msdf = lexical_index_to_sssom(oi, lexical_index, ruleset=load_mapping_rules(rules),meta=meta)
    else:
        msdf = lexical_index_to_sssom(oi, lexical_index,meta=meta)
    
    # msdf.prefix_map = sssom_yaml['curie_map']
    # msdf.metadata = sssom_yaml['global_metadata']
    msdf.df = filter_prefixes(df=msdf.df, filter_prefixes=prefix_of_interest, features=[SUBJECT_ID, OBJECT_ID])
    msdf.clean_prefix_map()
    import pdb; pdb.set_trace()

    with open(str(SRC / Path(output)), "w", encoding="utf8") as f:
        write_table(msdf, f)

# TODO: Replace the method below by sssom.utils.filter_prefixes.
def filter_prefixes(
    df: pd.DataFrame, filter_prefixes: List[str], features: list = KEY_FEATURES
) -> pd.DataFrame:
    """Filter any row where a CURIE in one of the key column uses one of the given prefixes.

    :param df: Pandas DataFrame
    :param filter_prefixes: List of prefixes
    :param features: List of dataframe column names dataframe to consider
    :return: Pandas Dataframe
    """
    filter_prefix_set = set(filter_prefixes)
    rows = []

    for _, row in df.iterrows():
        prefixes = {get_prefix_from_curie(curie) for curie in row[features]}
        # Confirm if all of the CURIEs in the list above appear in the filter_prefixes list.
        # If TRUE, append row.
        if all(prefix in filter_prefix_set for prefix in prefixes):
            rows.append(row)
    if rows:
        return pd.DataFrame(rows)
    else:
        return pd.DataFrame(columns=features)

if __name__ == '__main__':
    main()
