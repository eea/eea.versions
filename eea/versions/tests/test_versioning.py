""" Test versioning functionality
"""
from Products.CMFCore.utils import getToolByName
from eea.versions.controlpanel.schema import PortalType
from eea.versions.interfaces import IVersionControl
from eea.versions.versions import create_version, revoke_version
from eea.versions.tests.base import INTEGRATIONAL_TESTING
import unittest


class TestVersioning(unittest.TestCase):
    """ TestVersioning TestCase class
    """
    layer = INTEGRATIONAL_TESTING

    def setUp(self):
        """ Test Setup
        """
        self.portal = self.layer['portal']
        self.fid = self.portal.invokeFactory("Folder", 'f1')
        self.folder = self.portal[self.fid]
        docid = self.folder.invokeFactory("Document", 'd1')
        self.doc = self.folder[docid]

    def test_version_obj(self):
        """ Test the versioning of the object
        """
        new_version = create_version(self.doc)
        assert new_version != self.doc

    def test_version_random_id(self):
        """ Test the random version id of the object is 10 chars
        """
        new_version = create_version(self.doc)
        assert len(IVersionControl(new_version).versionId) == 10

    def test_version_prefixed_first_id(self):
        """ Test the version id of a first object contains prefix-1 chars
        """
        pvtool = getToolByName(self.portal, 'portal_eea_versions')
        vobjs = PortalType(id='LNK')
        vobjs.title = 'LNK'
        vobjs.search_type = 'Link'
        pvtool[vobjs.getId()] = vobjs
        link_id = self.folder.invokeFactory("Link", 'l1')
        link = self.folder[link_id]
        assert IVersionControl(link).versionId == 'LNK-1'

    def test_version_prefixed_first_version_id(self):
        """ Test the version id of a version contains the same version id
            as the object it derived from
        """
        pvtool = getToolByName(self.portal, 'portal_eea_versions')
        vobjs = PortalType(id='LNK')
        vobjs.title = 'LNK'
        vobjs.search_type = 'Link'
        pvtool[vobjs.getId()] = vobjs
        link_id = self.folder.invokeFactory("Link", 'l1')
        link = self.folder[link_id]
        link_version = create_version(link)
        assert IVersionControl(link_version).versionId == \
               IVersionControl(link).versionId

    def test_version_prefixed_second_id(self):
        """ Test the version id of a second object contains prefix-2 chars
        """
        pvtool = getToolByName(self.portal, 'portal_eea_versions')
        vobjs = PortalType(id='LNK')
        vobjs.title = 'LNK'
        vobjs.search_type = 'Link'
        pvtool[vobjs.getId()] = vobjs
        link_id = self.folder.invokeFactory("Link", 'l1')
        link = self.folder[link_id]
        link2_id = self.folder.invokeFactory("Link", 'l2')
        link2 = self.folder[link2_id]
        assert IVersionControl(link).versionId != \
               IVersionControl(link2).versionId

    def test_version_prefixed_revoked(self):
        """ Test the version id set to prefix-2 chars after version revoke
        """
        pvtool = getToolByName(self.portal, 'portal_eea_versions')
        vobjs = PortalType(id='LNK')
        vobjs.title = 'LNK'
        vobjs.search_type = 'Link'
        pvtool[vobjs.getId()] = vobjs
        link_id = self.folder.invokeFactory("Link", 'l1')
        link = self.folder[link_id]
        revoke_version(link)
        assert IVersionControl(link).versionId == 'LNK-2'

    def test_version_revoked(self):
        """ Test revoke on a version which will assign a new random value
        """
        current_id = IVersionControl(self.doc).versionId
        revoke_version(self.doc)
        assert current_id != IVersionControl(self.doc).versionId

