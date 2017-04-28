""" eea.versions viewlets
"""
from plone.app.layout.viewlets.common import ViewletBase
from plone.memoize import view
from zope.component import getMultiAdapter
from eea.versions.utils import object_provides
from eea.versions.interfaces import IGetVersions


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


class CanonicalURL(ViewletBase):
    """ Override to set canonical url for archived objects
    """

    @view.memoize
    def render(self):
        """ render canonical url
        """
        archive = 'eea.workflow.interfaces.IObjectArchived'
        archived = object_provides(self.context, archive)
        canonical_url = self.context.absolute_url()
        if archived:
            vobj = IGetVersions(self.context)
            versions = vobj.versions()
            for obj in versions[::-1]:
                archived = object_provides(obj, archive)
                if not archived:
                    canonical_url = obj.absolute_url()
                    break
        else:
            context_state = getMultiAdapter(
                (self.context, self.request), name=u'plone_context_state')
            canonical_url = context_state.canonical_object_url()
        return u'    <link rel="canonical" href="%s" />' % canonical_url
