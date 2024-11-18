"""Tests for sync_subclassof.py"""
import os
import sys
import unittest
from pathlib import Path

TEST_DIR = Path(os.path.abspath(os.path.dirname(__file__)))
TEST_INPUT_DIR = TEST_DIR / 'input'
TEST_OUTPUT_DIR = TEST_DIR / 'output'
PROJECT_ROOT = TEST_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))
TEST_ONTOLOGY = TEST_INPUT_DIR / 'merged.owl'


class TestSyncSubclassf(unittest.TestCase):
    """TODO"""

    def setUpClass(self):
        """Set up"""
        # TODO: convert to semsql if file not already present
        #  - and add the .db file to the gitignore, maybe
        # TODO: run pipeline
        pass

    def test_integration(self, use_cache=False):
        """TODO"""
        print()


# Special debugging: To debug in PyCharm and have it stop at point of error, change TestSyncSubclassf(unittest.TestCase)
#  to TestSyncSubclassf, and uncomment below.
# if __name__ == '__main__':
#     tester = TestSyncSubclassf()
#     tester.test_integration()
