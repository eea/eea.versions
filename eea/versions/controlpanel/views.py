""" Views
"""
from Products.Five import BrowserView
from zope.formlib.form import Fields, PageAddForm, PageEditForm, applyChanges

from eea.versions.controlpanel.interfaces import IEEAVersionsPortalType
from eea.versions.controlpanel.schema import PortalType


class EEAVersionsToolView(BrowserView):
    """ Browser view for eea versions tool
    """
    def add(self):
        """ Add new portal type
        """
        if not self.request:
            return None
        self.request.response.redirect('@@add')

    def delete(self, **kwargs):
        """ Delete portal types
        """
        ids = kwargs.get('ids', [])
        msg = self.context.manage_delObjects(ids)
        if not self.request:
            return msg
        self.request.response.redirect('@@view')

    def __call__(self, **kwargs):
        if self.request:
            kwargs.update(self.request)

        if kwargs.get('form.button.Add', None):
            return self.add()
        if kwargs.get('form.button.Delete', None):
            return self.delete(**kwargs)
        return self.index()


class AddPage(PageAddForm):
    """ Add page
    """
    form_fields = Fields(IEEAVersionsPortalType)

    def create(self, data):
        """ Create
        """
        ob = PortalType(id=data.get('title', 'ADDTitle'))
        applyChanges(ob, self.form_fields, data)
        return ob

    def add(self, obj):
        """ Add
        """
        name = obj.getId()
        self.context[name] = obj
        self._finished_add = True
        return obj

    def nextURL(self):
        """ Next
        """
        return "./@@view"


class EditPage(PageEditForm):
    """ Edit page
    """
    form_fields = Fields(IEEAVersionsPortalType)
