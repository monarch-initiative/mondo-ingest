import os
import sys
from pathlib import Path


HERE = Path(os.path.abspath(os.path.dirname(__file__)))
PROJECT_ROOT = HERE.parent
sys.path.insert(0, str(PROJECT_ROOT))
SRC_DIR = PROJECT_ROOT / 'src'
ONTOLOGY_DIR = SRC_DIR / 'ontology'
TMP_DIR = ONTOLOGY_DIR / 'tmp'
