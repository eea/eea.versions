from DateTime import DateTime
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone import PloneMessageFactory as _
from Products.CMFPlone import utils
from eea.versions.interfaces import IGetVersions
from eea.versions.interfaces import IVersionControl, IVersionEnhanced
from persistent.dict import PersistentDict
from zope.app.annotation.interfaces import IAnnotations
from zope.component import adapts
from zope.component.exceptions import ComponentLookupError
from zope.interface import alsoProvides, directlyProvides, directlyProvidedBy
from zope.interface import implements
import random


VERSION_ID = 'versionId'


def _reindex(obj):
    """ Reindex document
    """
    ctool = getToolByName(obj, 'portal_catalog')
    ctool.reindexObject(obj)


def _get_random(size=0):
    chars = "ABCDEFGHIJKMNOPQRSTUVWXYZ023456789"
    res = ''
    for k in range(size):
        res += random.choice(chars)
    return res


class VersionControl(object):
    """ Version adapter
    """
    implements(IVersionControl)
    adapts(IVersionEnhanced)

    def __init__(self, context):
        """ Initialize adapter. """
        self.context = context
        annotations = IAnnotations(context)

        #Version ID
        ver = annotations.get(VERSION_ID)
        if ver is None:
            verData = {VERSION_ID: ''}
            annotations[VERSION_ID] = PersistentDict(verData)

    def getVersionId(self):
        """ Get version id. """
        anno = IAnnotations(self.context)
        ver = anno.get(VERSION_ID)
        return ver[VERSION_ID]

    def setVersionId(self, value):
        """ Set version id. """
        anno = IAnnotations(self.context)
        ver = anno.get(VERSION_ID)
        ver[VERSION_ID] = value

    versionId = property(getVersionId, setVersionId)

    def getVersionNumber(self):
        """ Return version number """
        #TODO: to be implemented
        pass


class GetVersions(object):
    """ Get all versions
    """
    implements(IGetVersions)

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.versions = {}

    def extract(self, version):
        """ Extract needed properties
        """
        field = version.getField('lastUpload')  #XXX: this is a specific to dataservice
        if not field:
            value = version.getEffectiveDate()
        else:
            value = field.getAccessor(version)()

        if not isinstance(value, DateTime):
            value = None

        return {
            'title': version.title_or_id(),
            'url': version.absolute_url(),
            'date': value
        }

    def version_number(self):
        """ Return the current version number
        """
        if not self.versions:
            self()
        for k,v in self.versions.items():
            if v == self.context:
                return k
        return 0

    def newest(self):
        """ Return new versions
        """
        if not self.versions:
            self()
        versions = self.versions.items()
        versions.sort(reverse=True)

        res = []
        found = False
        uid = self.context.UID()
        for key, version in versions:
            if version.UID() == uid:
                found = True
                break
            res.append(self.extract(version))

        if not found:
            return []
        return res

    def oldest(self):
        """ Return old versions
        """
        if not self.versions:
            self()
        versions = self.versions.items()
        versions.sort()

        res = []
        found = False
        uid = self.context.UID()
        for key, version in versions:
            self.extract(version)
            if version.UID() == uid:
                found = True
                break
            res.append(self.extract(version))

        if not found:
            return []

        res.reverse()
        return res

    def __call__(self):
        if self.versions:
            return self.versions

        ver = IVersionControl(self.context)
        verId = ver.getVersionId()

        if not verId:
            return self.versions

        cat = getToolByName(self.context, 'portal_catalog')
        brains = cat.searchResults({'getVersionId' : verId,
                                    'sort_on': 'effective'})

        for index, brain in enumerate(brains):
            self.versions[index+1] = brain.getObject()
        return self.versions


class GetLatestVersionLink(object):
    """ Get latest version link
    """

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self):
        ctrl = IVersionControl(self.context)

        anno = IAnnotations(self.context)
        ver = anno.get(VERSION_ID)
        return ver[VERSION_ID]


class GetVersionId(object):
    """ Get version ID
    """

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self):
        res = None
        try:
            ver = IVersionControl(self.context)
            res = ver.getVersionId()
        except (ComponentLookupError, TypeError, ValueError):
            res = None

        return res


class HasVersions(object):
    """ Check if object has versions
    """

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self):
        if IVersionEnhanced.providedBy(self.context):
            return True
        return False


class CreateVersion(object):
    """ This view, when called, will create a new version of an object
    """

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self):
        ver = create_version(self.context)
        return self.request.RESPONSE.redirect(ver.absolute_url())


def create_version(context):
    """Create a new version of an object"""

    pu = getToolByName(context, 'plone_utils')
    obj_uid = context.UID()
    obj_id = context.getId()
    obj_title = context.Title()
    obj_type = context.portal_type
    parent = utils.parent(context)

    # Adapt version parent (if case)
    if not IVersionEnhanced.providedBy(context):
        alsoProvides(context, IVersionEnhanced)
    verparent = IVersionControl(context)
    verId = verparent.getVersionId()
    if not verId:
        verId = _get_random(10)
        verparent.setVersionId(verId)
        _reindex(context)

    # Create version object
    cp = parent.manage_copyObjects(ids=[obj_id])
    res = parent.manage_pasteObjects(cp)
    new_id = res[0]['new_id']

    ver = getattr(parent, new_id)

    # Remove copy_of from ID
    id = ver.getId()
    new_id = id.replace('copy_of_', '')
    new_id = generateNewId(parent, new_id, ver.UID())
    parent.manage_renameObject(id=id, new_id=new_id)

    # Set effective date today
    ver.setEffectiveDate(DateTime())

    # Set new state
    ver.reindexObject()
    _reindex(context)  #some indexed values of the context may depend on versions

    return ver

class AssignVersion(object):
    """ Assign new version ID
    """

    def __call__(self):
        pu = getToolByName(self.context, 'plone_utils')
        new_version = self.request.get('new-version', '')

        if new_version:
            obj = self.context

            # Verify if there are more objects under this version
            cat = getToolByName(self.context, 'portal_catalog')
            brains = cat.searchResults({'getVersionId' : new_version,
                                        'show_inactive': True})
            if brains and not IVersionEnhanced.providedBy(obj):
                alsoProvides(obj, IVersionEnhanced)

            # Set new version ID
            verparent = IVersionControl(obj)
            verparent.setVersionId(new_version)

            obj.reindexObject()
            message = _(u'Version ID changed.')
        else:
            message = _(u'Please specify a valid Version ID.')

        pu.addPortalMessage(message, 'structure')
        return self.request.RESPONSE.redirect(self.context.absolute_url())

class RevokeVersion(object):
    """ Revoke the context as being a version
    """

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self):
        obj = self.context
        verparent = IVersionControl(obj)
        verparent.setVersionId('')
        directlyProvides(obj, directlyProvidedBy(obj)-IVersionEnhanced)

        pu = getToolByName(self.context, 'plone_utils')
        message = _(u'Version revoked.')
        pu.addPortalMessage(message, 'structure')

        return self.request.RESPONSE.redirect(self.context.absolute_url())

def generateNewId(context, id, uid):
    tmp = id.split('-')[-1]
    try:
        num = int(tmp)
        id = '-'.join(id.split('-')[:-1])
    except ValueError:
        pass

    if id in context.objectIds():
        tmp_ob = getattr(context, id)
        if tmp_ob.UID() != uid:
            idx = 1
            while idx <= 100:
                new_id = "%s-%d" % (id, idx)
                new_ob = getattr(context, new_id, None)
                if new_ob:
                    if new_ob.UID() != uid:
                        idx += 1
                    else:
                        id = new_id
                        break
                else:
                    id = new_id
                    break
    return id

