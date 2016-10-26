""" plugins to modify @@rdf output
"""
from eea.versions.interfaces import IGetVersions

class ProductIdModifier(object):
    """ Adds information about product ID
    """
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
