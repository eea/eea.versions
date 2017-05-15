""" EEAVersions Tool
"""
from zope.component import queryMultiAdapter
from zope.interface import implements
from OFS.Folder import Folder
from Products.CMFCore.utils import getToolByName
from BTrees.IIBTree import IIBucket

from eea.versions.controlpanel.interfaces import IEEAVersionsTool
from eea.versions.controlpanel.interfaces import IEEAVersionsCatalog


class EEAVersionsTool(Folder):
    """ A local utility storing all eea versions global settings """
    implements(IEEAVersionsTool)

    id = 'portal_eea_versions'
    title = 'Manages eea versions global settings'
    meta_type = 'EEA Versions Tool'

    def apply_index(self, index, value):
        """ Custom catalog apply_index method
        """
        ctool = getToolByName(self, 'portal_catalog')
        catalog = queryMultiAdapter((self, ctool), IEEAVersionsCatalog)
        if not catalog:
            return IIBucket(), (index.getId(),)
        return catalog.apply_index(index, value)

    def search(self, **query):
        """
        Use this method to search over catalog using defined
        eea versions portal types.
        """
        ctool = getToolByName(self, 'portal_catalog')
        catalog = queryMultiAdapter((self, ctool), IEEAVersionsCatalog)
        if not catalog:
            return ctool(**query)
        return catalog(**query)
