""" Test versioning functionality
"""
import unittest
from Products.CMFCore.utils import getToolByName
from eea.versions.controlpanel.schema import PortalType
from eea.versions.interfaces import IVersionControl
from eea.versions.tests.base import INTEGRATIONAL_TESTING


class TestVersioningTool(unittest.TestCase):
    """ TestVersioning TestCase class
    """
    layer = INTEGRATIONAL_TESTING

    def setUp(self):
        """ Test Setup
        """
        self.portal = self.layer['portal']
        self.fid = self.portal.invokeFactory("Folder", 'f1')
        self.folder = self.portal[self.fid]

    def test_version_prefixed_title_rename(self):
        """ Test the version id of a new object changes to match
            new prefix
        """
        pvtool = getToolByName(self.portal, 'portal_eea_versions')
        vobjs = PortalType(id='LNK')
        vobjs.title = 'LNK'
        vobjs.search_type = 'Link'
        pvtool[vobjs.getId()] = vobjs
        link_id = self.folder.invokeFactory("Link", 'l1')
        link = self.folder[link_id]
        assert IVersionControl(link).versionId == 'LNK-1'
        vobjs.title = 'LINK'
        link2_id = self.folder.invokeFactory("Link", 'l2')
        link2 = self.folder[link2_id]
        # after tool object title is modified new version id will
        # use the new title
        assert IVersionControl(link2).versionId == 'LINK-2'
        # previous versions keep their prefix and number
        assert IVersionControl(link).versionId == 'LNK-1'

    def test_version_prefixed_title_rename_with_migration(self):
        """ Test the version id of all versions changes to match
            new prefix after performing migration
        """
        pvtool = getToolByName(self.portal, 'portal_eea_versions')
        vobjs = PortalType(id='LNK')
        vobjs.title = 'LNK'
        vobjs.search_type = 'Link'
        pvtool[vobjs.getId()] = vobjs
        link_id = self.folder.invokeFactory("Link", 'l1')
        link = self.folder[link_id]
        assert IVersionControl(link).versionId == 'LNK-1'
        vobjs.title = 'LINK'
        link2_id = self.folder.invokeFactory("Link", 'l2')
        link2 = self.folder[link2_id]
        # after tool object title is modified new version id will
        # use the new title
        assert IVersionControl(link2).versionId == 'LINK-2'
        # previous versions keep their prefix and number
        assert IVersionControl(link).versionId == 'LNK-1'
        migration_view = link.restrictedTraverse('@@migrateVersions')
        migration_view(prefix='LINK')
        # assert that now all of the links use the new LINK prefix
        # after running the migration script
        assert IVersionControl(link).versionId == 'LINK-1'
        assert IVersionControl(link2).versionId == 'LINK-2'


