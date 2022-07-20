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
from oaklib.resource import OntologyResource
from oaklib.implementations.sqldb.sql_implementation import SqlImplementation
from oaklib.utilities.lexical.lexical_indexer import (
    create_lexical_index,
    lexical_index_to_sssom,
    load_mapping_rules,
    save_lexical_index
)
from sssom.writers import write_table
import sys
from pathlib import Path
import yaml
import click

SRC = Path(__file__).resolve().parents[1]
ONTOLOGY_DIR = SRC / "ontology"
OUT_INDEX_DB = ONTOLOGY_DIR / "tmp/merged.db.lexical.yaml"

input_argument = click.argument("input", required=True, type=click.Path())
output_option = click.option(
    "-o",
    "--output",
    help="Path for output file.",
    type=click.File(mode="w"),
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
    with open(config, "r") as f:
        sssom_yaml = yaml.safe_load(f)

    resource = OntologyResource(slug=f"sqlite:///{Path(input).absolute()}")
    oi = SqlImplementation(resource=resource)
    lexical_index = create_lexical_index(oi)
    save_lexical_index(lexical_index, OUT_INDEX_DB)
    msdf = lexical_index_to_sssom(oi, lexical_index)
    if rules:
        msdf = lexical_index_to_sssom(oi, lexical_index, ruleset=load_mapping_rules(rules))
    else:
        msdf = lexical_index_to_sssom(oi, lexical_index)
    
    msdf.prefix_map = sssom_yaml['curie_map']
    msdf.metadata = sssom_yaml['global_metadata']

    # target_location = 
    with open(SRC / output, "w", encoding="utf8") as f:
        write_table(msdf, f)



if __name__ == '__main__':
    main()
