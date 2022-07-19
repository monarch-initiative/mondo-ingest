# Basic matching pipeline that takes in 

#Input:
# 1. MERGED_ONTOLOGY = tmp/merged.owl
# 2. SSSOM_CONFIG = metadata/mondo.sssom.config.yml
# 3. OUTPUT_SSSOM = mapping/mondo-sources-all-lexical.sssom.tsv

# I would try some basic things first:

# Use synonymiser
# Use oak.mapping() pipeline

import logging
from oaklib.cli import lexmatch
import sys

def run(input:str, lexical_index: str, output: str):
    # args = [input,lexical_index,output]
    # msdf = lexmatch(*args)
    import pdb; pdb.set_trace()



if __name__ == '__main__':
    input = None
    lexical_index = None
    output = None

    for arg in sys.argv:
        if arg.endswith('.owl'):
            input = arg
        elif arg.endswith('.yaml') or arg.endswith('.yml'):
            lexical_index = arg
        elif arg.endswith('.tsv'):
            output = arg
        else:
            logging.info(f"{arg} has no further use from here on.")
    
    run(input=input, lexical_index=lexical_index, output=output)
