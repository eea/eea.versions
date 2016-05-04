""" eea.versions viewlets
"""
from plone.app.layout.viewlets.common import ViewletBase
from zope.component import getMultiAdapter


class VersionStatusViewlet(ViewletBase):
    """ Viewlet to show status of versioning on any content type
    """

    def available(self):
        """ Method that enables the viewlet only if we are on a
            view template
        """
        plone = getMultiAdapter((self.context, self.request),
                                name=u'plone_context_state')
        return plone.is_view_template()
