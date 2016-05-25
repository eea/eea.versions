""" plugins to modify @@rdf output
"""
from zope.component import adapts
from zope.interface import implements
from eea.rdfmarshaller.interfaces import ISurfResourceModifier
from .interfaces import IVersionEnhanced, IGetVersions


class ProductIdModifier(object):
    """ Adds information about product ID
    """

    implements(ISurfResourceModifier)
    adapts(IVersionEnhanced)

    def __init__(self, context):
        self.context = context

    def run(self, resource, *args, **kwds):
        """ change the rdf output
        """
        versionId = IGetVersions(self.context).versionId
        if not versionId:
            versionId = self.context.UID()
        resource.schema_productID = versionId

        resource.save()
