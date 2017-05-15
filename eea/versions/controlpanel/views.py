""" Views
"""
from Products.Five import BrowserView
from Products.statusmessages.interfaces import IStatusMessage
from eea.versions.controlpanel.interfaces import IEEAVersionsPortalType
from eea.versions.controlpanel.schema import PortalType
from eea.versions.config import EEAMessageFactory as _
from z3c.form import form, field
from z3c.form import button
from z3c.form.interfaces import DISPLAY_MODE


def input_is_valid(self, data):
    """ Flag input as invalid if both search_type and searc_interface is set
    """
    if data.get('search_type') and data.get('search_interface'):
        self.status = _("Cannot add both Portal type and "
                        "Provided Interface")
        self.formErrorsMessage = self.status
        return False
    return True


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

    def migrate(self, **kwargs):
        """ Migrate button
        """
        ids = kwargs.get('ids', [])
        if not ids:
            IStatusMessage(self.context.REQUEST).addStatusMessage(
                _("You need to select a custom portal type for migration"),
                type="error")
        for vid in ids:
            context = self.context
            version_tool = context
            vobj = version_tool.get(vid)
            vtitle = vobj.title
            migration_view = context.restrictedTraverse('@@migrateVersions')
            migration_view(prefix=vtitle)

        IStatusMessage(self.context.REQUEST).addStatusMessage(
            _("Migration for %s completed" % ",".join(ids)),
            type="info")
        self.request.response.redirect('@@view')

    def __call__(self, **kwargs):
        if self.request:
            kwargs.update(self.request)

        if kwargs.get('form.button.Add', None):
            return self.add()
        if kwargs.get('form.button.Delete', None):
            return self.delete(**kwargs)
        if kwargs.get('form.button.Migrate', None):
            return self.migrate(**kwargs)
        return self.index()


class AddPage(form.AddForm):
    """ Add page
    """
    fields = field.Fields(IEEAVersionsPortalType)
    fields['last_assigned_version_number'].mode = DISPLAY_MODE

    def create(self, data):
        """ Create
        """
        valid_input = input_is_valid(self, data)
        if not valid_input:
            return
        ob = PortalType(id=data.get('title', 'ADDTitle'))
        form.applyChanges(self, ob, data)
        return ob

    def add(self, obj):
        """ Add
        """
        if not obj:
            return
        name = obj.getId()
        self.context[name] = obj
        self._finished_add = True
        return obj

    def nextURL(self):
        """ Next
        """
        return "./@@view"


class EditPage(form.EditForm):
    """ Edit page
    """
    fields = field.Fields(IEEAVersionsPortalType)
    fields['last_assigned_version_number'].mode = DISPLAY_MODE

    def nextURL(self):
        """ Next
        """
        return "../@@view"

    @button.buttonAndHandler(_(u"label_apply", default=u"Apply"),
                             name='apply')
    def handleApply(self, action):
        """ Apply button
        """
        data = self.extractData()[0]
        valid_input = input_is_valid(self, data)
        if not valid_input:
            return
        reset_triggered = self.reset_version_number(data)
        if reset_triggered:
            return self.request.response.redirect(self.nextURL())
        super(EditPage, self).handleApply(self, action)
        self.request.response.redirect(self.nextURL())

    def reset_version_number(self, data):
        """ reset version number if title is different
        """
        title = data.get('title')
        if title and self.context.title == title:
            return False
        current_id = self.context.id
        tool = self.context.aq_parent
        # 72521 Folderish content type fails when calling manage_renameObject
        # with operation is not supported and a simple change of id
        # will keep the object with the previous id as such we need to recreate
        # it and then delete the previous object
        self.context._setId(title)
        tool._setObject(str(title), self.context)
        tool._delObject(current_id)
        data['last_assigned_version_number'] = 0
        changes = self.applyChanges(data)
        if changes:
            self.status = self.successMessage
        else:
            self.status = self.noChangesMessage
        return True

    @button.buttonAndHandler(_(u"label_cancel", default=u"Cancel"),
                             name='cancel_add')
    def handleCancel(self, action):
        """ Cancel button
        """
        self.request.response.redirect(self.nextURL())
        return ''
