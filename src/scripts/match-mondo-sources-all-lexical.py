# Basic matching pipeline that takes in

# Input:
# 1. MERGED_ONTOLOGY = tmp/merged.owl
# 2. SSSOM_CONFIG = metadata/mondo.sssom.config.yml
# 3. OUTPUT_SSSOM = mapping/mondo-sources-all-lexical.sssom.tsv

# I would try some basic things first:

# Use synonymiser
# Use oak.mapping() pipeline

import logging
from pathlib import Path
from oaklib.resource import OntologyResource
from oaklib.implementations.sqldb.sql_implementation import SqlImplementation
from oaklib.utilities.lexical.lexical_indexer import (
    create_lexical_index,
    lexical_index_to_sssom,
    load_mapping_rules,
    save_lexical_index,
)
import sys
import click
import yaml
import pandas as pd

from sssom.constants import SUBJECT_ID, OBJECT_ID, PREDICATE_MODIFIER
from sssom.util import get_prefix_from_curie
from sssom.parsers import parse_sssom_table
from sssom.writers import write_table
from sssom.io import get_metadata_and_prefix_map

SRC = Path(__file__).resolve().parents[1]
ONTOLOGY_DIR = SRC / "ontology"
OUT_INDEX_DB = ONTOLOGY_DIR / "tmp/merged.db.lexical.yaml"
TEMP_DIR = ONTOLOGY_DIR / "tmp"
SSSOM_MAP_FILE = TEMP_DIR / "mondo.sssom.tsv"
# KEY_FEATURES = [SUBJECT_ID, OBJECT_ID]
MAPPINGS_DIR = SRC / "mappings"

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
@click.option(
    "--rejects",
    help="SSSOM TSV file containing rejected mappings that need to be filtered out.",
)
@output_option
def run(input: str, config: str, rules: str, rejects: str, output: str):
    # Implemented `meta` param in `lexical_index_to_sssom`

    #meta = get_metadata_and_prefix_map(config)
    meta = None
    with open(config, "r") as f:
        yml = yaml.safe_load(f)

    # Get mondo.sssom.tsv
    mapping_msdf = parse_sssom_table(SSSOM_MAP_FILE)
    reject_df = pd.read_csv(
        rejects, sep="\t", index_col=None
    )
    mapping_msdf.df = pd.concat([mapping_msdf.df, reject_df])[mapping_msdf.df.columns].drop_duplicates()
    # mapping_msdf.df = (
    #     pd.merge(
    #         mapping_msdf.df,
    #         reject_df,
    #         on=list(mapping_msdf.df.columns),
    #         how="outer",
    #         indicator=True,
    #     )
    #     .query("_merge != 'both'")
    #     .drop("_merge", axis=1)
    #     .reset_index(drop=True)
    # )

    prefixes_of_interest = yml["subject_prefixes"]

    resource = OntologyResource(slug=f"sqlite:///{Path(input).absolute()}")
    oi = SqlImplementation(resource=resource)
    ruleset = load_mapping_rules(rules)
    # syn_rules = [x.synonymizer for x in ruleset.rules if x.synonymizer]
    lexical_index = create_lexical_index(oi=oi, mapping_rule_collection=ruleset)
    save_lexical_index(lexical_index, OUT_INDEX_DB)

    if rules:
        msdf = lexical_index_to_sssom(oi, lexical_index, ruleset=ruleset, meta=meta)
    else:
        msdf = lexical_index_to_sssom(oi, lexical_index, meta=meta)

    # msdf.prefix_map = sssom_yaml['curie_map']
    # msdf.metadata = sssom_yaml['global_metadata']
    # todo: if the need for IRI to CURIE conversion rearises, use the curies .compress() instead of bioregistry
    # ! The block below converts IRI into CURIE using bioregistry.
    # msdf.df[SUBJECT_ID] = msdf.df[SUBJECT_ID].apply(
    #     lambda x: iri_to_curie(x) if x.startswith("<http") else x
    # )
    # msdf.df[OBJECT_ID] = msdf.df[OBJECT_ID].apply(
    #     lambda x: iri_to_curie(x) if x.startswith("<http") else x
    # )

    msdf.remove_mappings(mapping_msdf)

    # Select matches with prefixes defined in the configuration
    prefix_set = set(prefixes_of_interest)
    msdf.df = msdf.df[
        msdf.df[SUBJECT_ID].apply(get_prefix_from_curie).isin(prefix_set) &
        msdf.df[OBJECT_ID].apply(get_prefix_from_curie).isin(prefix_set)
    ].reset_index(drop=True)
    msdf.clean_prefix_map()
    with Path(output).open("w") as f:
        write_table(msdf, f)

    # Select MONDO->NOT MONDO matches
    msdf.df = msdf.df[
        msdf.df[SUBJECT_ID].str.startswith("MONDO:") &
        ~msdf.df[OBJECT_ID].str.startswith("MONDO:")
    ].reset_index(drop=True)
    with Path(output.replace("lexical", "lexical-2")).open("w") as f:
        write_table(msdf, f)

if __name__ == "__main__":
    main()
