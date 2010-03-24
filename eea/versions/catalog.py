# -*- coding: utf-8 -*-

__author__ = """European Environment Agency (EEA)"""
__docformat__ = 'plaintext'

from zope.component.exceptions import ComponentLookupError
from Products.CMFPlone.CatalogTool import registerIndexableAttribute
from eea.versions.interfaces import IVersionControl


def getVersionIdForIndex(object, portal, **kwargs):
    try:
        ver = IVersionControl(object)
        return ver.getVersionId()
    except (ComponentLookupError, TypeError, ValueError):
        # The catalog expects AttributeErrors when a value can't be found
        raise AttributeError

# getVersionId index is made a callable
registerIndexableAttribute('getVersionId', getVersionIdForIndex)
