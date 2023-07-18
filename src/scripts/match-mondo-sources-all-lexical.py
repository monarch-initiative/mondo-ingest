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
from sssom.util import filter_prefixes, is_curie, is_iri
from sssom.parsers import parse_sssom_table
from sssom.writers import write_table
from sssom.io import get_metadata_and_prefix_map, filter_file
from bioregistry import curie_from_iri

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

    meta = get_metadata_and_prefix_map(config)
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

    prefix_of_interest = yml["subject_prefixes"]

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
    # ! The block below converts IRI into CURIE using bioregistry.
    # msdf.df[SUBJECT_ID] = msdf.df[SUBJECT_ID].apply(
    #     lambda x: iri_to_curie(x) if x.startswith("<http") else x
    # )
    # msdf.df[OBJECT_ID] = msdf.df[OBJECT_ID].apply(
    #     lambda x: iri_to_curie(x) if x.startswith("<http") else x
    # )
    msdf.remove_mappings(mapping_msdf)

    with open(str(Path(output)), "w", encoding="utf8") as f:
        write_table(msdf, f)

    objects = msdf.df[OBJECT_ID].drop_duplicates()
    prefixes = objects.str.split(":").str.get(0).drop_duplicates()
    prefix_args = tuple([x + ":%" for _, x in prefixes.items() if x != "MONDO"])
    kwargs = {"subject_id": ("MONDO:%",), "object_id": prefix_args}
    with open(str(Path(output.replace("lexical", "lexical-2"))), "w") as f:
        filter_file(input=str(Path(output)), output=f, **kwargs)


def iri_to_curie(item):
    """If item is an IRI, return CURIE form.

    :param item: IRI or CURIE
    :return: CURIE
    """
    if item.startswith("<"):
        item = item.strip("<").strip(">")

    if is_iri(item):
        item = curie_from_iri(item) if curie_from_iri(item) else item
    else:
        if not is_curie(item):
            logging.warning(f"{item} is neither s CURIE nor an IRI.")

    # if item.startswith("obo:orphanet.ordo_"):
    #     item = item.replace("obo:orphanet.ordo_", "Orphanet:")
    # elif item.startswith("obo:OMIM"):
    #     item = item.replace("obo:OMIM_", "OMIM:")

    return item


if __name__ == "__main__":
    main()
