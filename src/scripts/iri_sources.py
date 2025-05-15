"""Get a list of version IRIs for sources"""
import os
from argparse import ArgumentParser
from pathlib import Path
from typing import Dict, List, Union

from oaklib import get_adapter
from oaklib.implementations import SqlImplementation

HERE = Path(os.path.abspath(os.path.dirname(__file__)))
SRC_DIR = HERE.parent
PROJECT_ROOT = SRC_DIR.parent
ONTO_DIR = PROJECT_ROOT / 'src' / 'ontology'



def iri_docs(rel_paths: List[str], outpath_txt: Union[Path, str], outpath_md: Union[Path, str]):
    """Get a list of version IRIs for sources"""
    version_curies: List[str] = []
    for rel_path in rel_paths:
        path = ONTO_DIR / rel_path
        adapter: SqlImplementation = get_adapter(path)
        for ont in adapter.ontologies():
            meta = adapter.ontology_metadata_map(ont)
            versions: List[str] = meta["owl:versionIRI"]
            version_curies += versions
    version_iris = [x.replace('obo:', 'http://purl.obolibrary.org/obo/', ) for x in version_curies]

    outpath_txt = ONTO_DIR / outpath_txt
    with open(outpath_txt, 'w') as f:
        for version_iri in version_iris:
            f.write(version_iri + '\n')
    outpath_md = ONTO_DIR / outpath_md
    with open(outpath_md, 'w') as f:
        f.write(
"""These are the versions of the ingested resources that are currently being ingested into Mondo.  
Note that the specific version listed here might be only partially integrated into Mondo (the integration is ongoing).

## Versions of ingested resources\n\n""")
        for version_iri in version_iris:
            f.write(f'- {version_iri}\n')


def cli():
    """Command line interface."""
    parser = ArgumentParser(prog='Source IRI docs', description='Get a list of version IRIs for sources')
    parser.add_argument(
        '-p', '--rel-paths', required=True, nargs='+', type=str, help='List of source DB paths, relative to src/ontology/.')
    parser.add_argument(
        '-o', '--outpath-txt', required=True, type=str, help='Outpath for text file, relative to src/ontology/.')
    parser.add_argument(
        '-O', '--outpath-md', required=True, type=str, help='Outpath for markdown file, relative to src/ontology/.')
    d: Dict = vars(parser.parse_args())
    return iri_docs(**d)


if __name__ == '__main__':
    cli()
