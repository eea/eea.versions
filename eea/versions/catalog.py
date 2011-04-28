# -*- coding: utf-8 -*-

__author__ = """European Environment Agency (EEA)"""
__docformat__ = 'plaintext'

from eea.versions.interfaces import IVersionControl
from eea.versions.interfaces import IVersionEnhanced
from plone.indexer.decorator import indexer

@indexer(IVersionEnhanced)
def getVersionIdForIndex(obj):
    try:
        ver = IVersionControl(obj)
        return ver.getVersionId()
    except (TypeError, ValueError): #ComponentLookupError, 
        # The catalog expects AttributeErrors when a value can't be found
        raise AttributeError

