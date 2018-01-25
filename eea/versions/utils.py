""" EEA Versions utils
"""
import random
from Products.CMFCore.utils import getToolByName
from zope.dottedname.resolve import resolve
from Acquisition import aq_base


def object_provides(obj, iname):
    """ implement plone_interface_info as plone.app.async
        does not pass a request and calling restrictedTraverse
        will end up in error
    """
    iface = resolve(iname)
    return iface.providedBy(aq_base(obj))

def _random_id(context, size=10):
    """ Returns a random arbitrary sized string, usable as version id
    """
    try:
        catalog = getToolByName(context, "portal_catalog")
    except AttributeError:
        catalog = None  # can happen in tests
    chars = "ABCDEFGHIJKMNOPQRSTUVWXYZ0123456789"
    res = "".join(random.sample(chars, size))

    if not catalog:
        return res

    if not catalog.Indexes.get('getVersionId'):
        return res

    i = 0
    while True:
        if not catalog.searchResults(getVersionId=res):
            break
        res = "".join(random.sample(chars, size))
        if i > 100:  # what are the odds of that?
            break
        i += 1

    return res
