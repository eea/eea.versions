""" eea.versions viewlets
"""
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from eea.versions.versions import get_version_prefix
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

    def get_version_object(self, version):
        """ Retrieve portal_version object if found
        """
        vtool = self.context.portal_eea_versions
        res = vtool.get(version.split('-')[0])
        if not res:
            return get_version_prefix(self.context)
        return res

    def available(self):
        """ Available
        """
        version_id = self.version_id()
        if not version_id:
            return ''
        if '-' not in version_id:
            return ''
        version_obj = self.get_version_object(version_id)
        return version_obj.show_version_id if version_obj else ''
