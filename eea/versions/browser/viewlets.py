""" eea.versions viewlets
"""
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from plone.app.layout.viewlets.common import ViewletBase
from zope.component import getMultiAdapter
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


class VersionIdViewlet(ViewletBase):
    """ A custom viewlet registered below the title for showing
        the version id if version id contain dashes as that means
        that the version id isn't random and we should show it
        as a global version id
    """

    index = ViewPageTemplateFile('templates/versioning_id.pt')

    def version_id(self):
        return IGetVersions(self.context).versionId

    def available(self):
        """ Available
        """
        version = self.version_id()
        if not version:
            return ''
        return '-' in version
