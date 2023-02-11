"""An alternative way of creating a `reports/mirror_signature-ONTOLOGY.tsv` which uses OAK instead of `robot`.

The primary use case for this is NCIT, which has a huge memory requirement, and can error out sometimes because of this.

A "mirror signature" is a table with a single column '?term' which includes all of the class IRIs in an ontology.
"""
from argparse import ArgumentParser
from typing import Dict, List, Union

import curies
import pandas as pd
import yaml
from oaklib import get_implementation_from_shorthand
from oaklib.types import CURIE, URI
from sssom.util import is_curie


# TODO: there's already some duplicative code between this and `unmapped_tables.py`: reading config, list curies
def mirror_signature_via_oak(db_path: str, onto_config_path: str, outpath: str) -> pd.DataFrame:
    """Creates a `reports/mirror_signature-ONTOLOGY.tsv` which uses OAK instead of `robot`."""
    # Read source info
    with open(onto_config_path, 'r') as stream:
        onto_config = yaml.safe_load(stream)
        prefix_map: Dict[str, str] = onto_config['base_prefix_map']
        owned_prefixes: List[str] = list(prefix_map.keys())
        converter = curies.Converter.from_prefix_map(prefix_map)
        prefix_preplacement_map = {
            f'{alias}:': f'{preferred}:' for preferred, alias in onto_config['prefix_aliases'].items()} \
            if 'prefix_aliases' in onto_config else {}
    oi = get_implementation_from_shorthand(db_path)
    ids_sans_deprecated: List[Union[CURIE, URI]] = [x for x in oi.entities(filter_obsoletes=True)]

    # todo: excessive code since not sure if OAK sometimes returns IRIs or CURIES. can we simplify?

    # Get owned terms
    curies_owned: List[CURIE] = []
    for _id in ids_sans_deprecated:
        curie: CURIE = _id if is_curie(_id) else converter.compress(_id)
        for alias, preferred in prefix_preplacement_map.items():
            curie = curie.replace(alias, preferred) if curie else curie
        if curie and curie.split(':')[0] in owned_prefixes:
            curies_owned.append(curie)
    uris_owned: List[URI] = [converter.expand(curie) for curie in curies_owned]

    # Save
    df = pd.DataFrame({'?term': uris_owned})
    df.to_csv(outpath, sep='\t', index=False)

    return df


def cli():
    """Command line interface."""
    description = 'Creates a "mirror signature" is a table with a single column "?term" which includes all of the ' \
                  'class IRIs in an ontology.'
    parser = ArgumentParser(description=description)
    parser.add_argument('-o', '--outpath', required=True, help='Path to create a mirror_signature-%.tsv.')
    parser.add_argument('-d', '--db-path', required=True, help='Path to SemanticSQL sqlite ONTO_NAME.db.')
    parser.add_argument(
        '-c', '--onto-config-path', required=True,
        help='Path to a config `.yml` for the ontology which contains a `base_prefix_map` which contains a '
             'list of prefixes owned by the ontology. Used to filter out terms.')
    mirror_signature_via_oak(**vars(parser.parse_args()))


if __name__ == '__main__':
    cli()
