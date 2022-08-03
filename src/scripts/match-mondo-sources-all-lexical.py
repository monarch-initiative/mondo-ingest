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
from typing import List, TextIO
from oaklib.resource import OntologyResource
from oaklib.implementations.sqldb.sql_implementation import SqlImplementation
from oaklib.utilities.lexical.lexical_indexer import (
    create_lexical_index,
    lexical_index_to_sssom,
    load_mapping_rules,
    save_lexical_index
)
import pandas as pd

import sys
from pathlib import Path
import click
import yaml

from sssom.constants import SUBJECT_ID, OBJECT_ID
from sssom.util import KEY_FEATURES, get_prefix_from_curie, MappingSetDataFrame
from sssom.parsers import parse_sssom_table
from sssom.writers import write_table
from sssom.io import get_metadata_and_prefix_map, run_sql_query

SRC = Path(__file__).resolve().parents[1]
ONTOLOGY_DIR = SRC / "ontology"
OUT_INDEX_DB = ONTOLOGY_DIR / "tmp/merged.db.lexical.yaml"
TEMP_DIR = ONTOLOGY_DIR / "tmp"
SSSOM_MAP_FILE = TEMP_DIR / "mondo.sssom.tsv"
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

    meta = get_metadata_and_prefix_map(config)
    with open(config, "r") as f:
        yml = yaml.safe_load(f)

    # Get mondo.sssom.tsv
    mapping_msdf = parse_sssom_table(SSSOM_MAP_FILE)

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
    # TODO: replace line below by msdf.remove_mappings(mapping_msdf) once imported from SSSOM.
    msdf.df = (
            pd.merge(
                msdf.df,
                mapping_msdf.df,
                on=KEY_FEATURES,
                how="outer",
                suffixes=("", "_2"),
                indicator=True,
            )
            .query("_merge == 'left_only'")
            .drop("_merge", axis=1)
            .reset_index(drop=True)
        )
    msdf.df = msdf.df[msdf.df.columns.drop(list(msdf.df.filter(regex=r"_2")))]
    msdf.clean_prefix_map()

    with open(str(SRC / Path(output)), "w", encoding="utf8") as f:
        write_table(msdf, f)

    objects = msdf.df[OBJECT_ID].drop_duplicates()
    prefixes = objects.str.split(":").str.get(0).drop_duplicates()
    prefix_args = tuple([x+":%" for _, x in prefixes.iteritems() if x != "MONDO"])
    kwargs = {"subject_id": ("MONDO:%",), "object_id": prefix_args}
    with open(str(SRC / Path(output.replace("lexical", "lexical-2"))), "w") as f:
        filter_file(
            input=str(SRC / Path(output)),
            output=f,
            **kwargs
            )

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

def filter_file(input: str, output: TextIO, **kwargs) -> MappingSetDataFrame:
    """Filter a dataframe by dynamically generating queries based on user input.

    e.g. sssom filter --subject_id x:% --subject_id y:% --object_id y:% --object_id z:% tests/data/basic.tsv

    yields the query:

    "SELECT * FROM df WHERE (subject_id LIKE 'x:%'  OR subject_id LIKE 'y:%')
     AND (object_id LIKE 'y:%'  OR object_id LIKE 'z:%') " and displays the output.

    :param input: DataFrame to be queried over.
    :param output: Output location.
    :param **kwargs: Filter options provided by user which generate queries (e.g.: --subject_id x:%).
    :raises ValueError: If parameter provided is invalid.
    :return: Filtered MappingSetDataFrame object.
    """
    params = {k: v for k, v in kwargs.items() if v}
    query = "SELECT * FROM df WHERE ("
    multiple_params = True if len(params) > 1 else False

    # Check if all params are legit
    input_df: pd.DataFrame = parse_sssom_table(input).df
    if not input_df.empty and len(input_df.columns) > 0:
        column_list = list(input_df.columns)
    else:
        raise ValueError(f"{input} is either not a SSSOM TSV file or an empty one.")
    legit_params = all(p in column_list for p in params)
    if not legit_params:
        invalids = [p for p in params if p not in column_list]
        raise ValueError(f"The params are invalid: {invalids}")

    for idx, (k, v) in enumerate(params.items(), start=1):
        query += k + " LIKE '" + v[0] + "' "
        if len(v) > 1:
            for exp in v[1:]:
                query += " OR "
                query += k + " LIKE '" + exp + "') "
        else:
            query += ") "
        if multiple_params and idx != len(params):
            query += " AND ("
    return run_sql_query(query=query, inputs=[input], output=output)

if __name__ == '__main__':
    main()
