""" Test versioning functionality
"""
from eea.versions.versions import create_version
from eea.versions.tests.base import EEAFixture


class TestVersioning(EEAFixture):
    """ TestArchive TestCase class
    """

    def afterSetUp(self):
        """ After Setup
        """
        self.setRoles(('Manager', ))
        portal = self.portal
        fid = portal.invokeFactory("Folder", 'f1')
        self.folder = portal[fid]
        docid = self.folder.invokeFactory("Document", 'd1')
        self.doc = self.folder[docid]

    def test_version_obj(self):
        """ Test the versioning of the object
        """
        new_version = create_version(self.doc)
        assert new_version != self.doc


# def test_suite():
#     """ Test Suite
#     """
#     from unittest import TestSuite, makeSuite
#     suite = TestSuite()
#     suite.addTest(makeSuite(TestVersioning), name="test_versioning")
#     return suite
