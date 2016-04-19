""" Test versioning functionality
"""
from eea.versions.versions import create_version
from eea.versions.tests.base import INTEGRATIONAL_TESTING
import unittest


class TestVersioning(unittest.TestCase):
    """ TestVersioning TestCase class
    """
    layer = INTEGRATIONAL_TESTING

    def setUp(self):
        """ Test Setup
        """
        portal = self.layer['portal']
        self.fid = portal.invokeFactory("Folder", 'f1')
        folder = portal[self.fid]
        docid = folder.invokeFactory("Document", 'd1')
        self.doc = folder[docid]

    def test_version_obj(self):
        """ Test the versioning of the object
        """
        new_version = create_version(self.doc)
        assert new_version != self.doc


