"""catalog utils
"""
from eea.versions.interfaces import IVersionControl
from eea.versions.interfaces import IVersionEnhanced
from plone.indexer.decorator import indexer

@indexer(IVersionEnhanced)
def getVersionIdForIndex(obj):
    """indexes versionid
    """
    try:
        ver = IVersionControl(obj)
        return ver.getVersionId()
    except (TypeError, ValueError): #ComponentLookupError,
        # The catalog expects AttributeErrors when a value can't be found
        raise AttributeError
