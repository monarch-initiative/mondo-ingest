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


SRC = Path(__file__).resolve().parents[1]
ONTOLOGY_DIR = SRC / "ontology"
OUT_INDEX_DB = ONTOLOGY_DIR / "tmp/merged.db.lexical.yaml"

def run(input:str, config_file: str, rules:str, output: str):
    with open(config_file, "r") as f:
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
    input = None
    config_file = None
    output = None
    rules = None
    # TODO: there must be a better way to parse arguments.
    for arg in sys.argv:
        if arg.endswith('.db'):
            input = arg
        elif arg.endswith('_rules.yaml') or arg.endswith('_rules.yml'):
            rules = arg
        elif arg.endswith('.yaml') or arg.endswith('.yml'):
            config_file = arg
        elif arg.endswith('.tsv'):
            output = arg
        else:
            logging.info(f"{arg} has no further use from here on.")
    
    run(input=input, config_file=config_file, rules=rules, output=output)
