"""main eea.versions module
"""

from Acquisition import aq_base
from DateTime import DateTime
from Persistence import PersistentMapping
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone import PloneMessageFactory as _
from Products.CMFPlone import utils
from Products.Five.browser import BrowserView
from eea.versions.events import VersionCreatedEvent
from eea.versions.interfaces import ICreateVersionView
from eea.versions.interfaces import IGetVersions, IGetContextInterfaces
from eea.versions.interfaces import IVersionControl, IVersionEnhanced
from plone.memoize.instance import memoize
from zope.annotation.interfaces import IAnnotations
from zope.component import adapts
from zope.component import queryMultiAdapter, getMultiAdapter
from zope.event import notify
from zope.interface import alsoProvides, implements, providedBy
import logging
import random


hasNewDiscussion = True
try:
    from plone.app.discussion.interfaces import IConversation
except ImportError:
    hasNewDiscussion = False

logger = logging.getLogger('eea.versions.versions')

VERSION_ID = 'versionId'


class VersionControl(object):
    """ Version adapter """

    implements(IVersionControl)
    adapts(IVersionEnhanced)

    def __init__(self, context):
        """ Initialize adapter. """
        self.context = context
        self.annot = IAnnotations(context)

    def getVersionId(self):
        """ Get version id. """
        return self.annot.get(VERSION_ID)

    def setVersionId(self, value):
        """ Set version id. """
        self.annot[VERSION_ID] = value

    versionId = property(getVersionId, setVersionId)

    def can_version(self):
        """ can new versions be created? """
        return True #adapt, subclass and override if needed


class CanCreateNewVersion():
    """ @@can_create_new_version view
    """

    def __call__(self):
        if not IVersionEnhanced.providedBy(self.context):
            return False
        return IVersionControl(self.context).can_version()


class GetVersions(object):
    """ Get all versions

    The versions are always reordered "on the fly" based on their
    effectiveDate or creationDate. This may create unexpected behaviour!
    """
    implements(IGetVersions)

    versionId = None

    def __init__(self, context):    #, request
        """constructor"""
        self.context = context
        #self.request = request

        self.versionId = IVersionControl(self.context).versionId


        failsafe = lambda obj: "Unknown"
        self.state_title_getter = queryMultiAdapter(
                                        (self.context, self.context.REQUEST),
                                 name=u'getWorkflowStateTitle') or failsafe

    @memoize
    def versions(self):
        """return a list of sorted version objects
        """
        # Avoid making a catalog call if versionId is empty

        if not self.versionId:
            return [self.context]

        if not isinstance(self.versionId, basestring):
            return [self.context]   # this is an old, unmigrated storage

        cat = getToolByName(self.context, 'portal_catalog')
        query = {'getVersionId' : self.versionId}
        mtool = getToolByName(self.context, 'portal_membership')
        if mtool.isAnonymousUser():
            query['review_state'] = 'published'

        brains = cat(**query)
        objects = [b.getObject() for b in brains]

        # Some objects don't have EffectiveDate so we have to sort
        # them using CreationDate. This has the side effect that
        # in certain conditions the list of versions is reordered
        # For the anonymous users this is never a problem because
        # they only see published (and with effective_date) objects

        # Store versions as ordered list, with the oldest item first
        _versions = sorted(objects,
                key=lambda o: o.effective_date or o.creation_date)

        #during creation self.context has not been indexed
        if not self.context.UID() in [o.UID() for o in _versions]:
            _versions.append(self.context)

        return _versions

    @memoize
    def wftool(self):
        """Memoized portal_workflow
        """
        return getToolByName(self.context, 'portal_workflow')

    @memoize
    def enumerate_versions(self): #rename from versions
        """ Returns a mapping of version_number:object"""

        return dict(enumerate(self.versions(), start=1))

    def version_number(self):
        """ Return the current version number
        """
        return self.versions().index(self.context) + 1

    def later_versions(self):
        """ Return a list of newer versions, newest object first
        """
        res = []
        uid = self.context.UID()
        for version in reversed(self.versions()):
            if version.UID() == uid:
                break
            res.append(self._obj_info(version))

        return res

    def earlier_versions(self):
        """ Return a list of older versions, oldest object first
        """
        res = []
        uid = self.context.UID()
        for version in self.versions():
            if version.UID() == uid:
                break
            res.append(self._obj_info(version))

        res.reverse()   #is this needed?
        return res

    def latest_version(self):
        """Returns the latest version of an object
        """
        return self.versions()[-1]

    def first_version(self):
        """ Returns the first version of an object """
        return self.versions()[0]

    def isLatest(self):
        """ return true if this object is latest version
        """
        return (self.context.UID() == self.versions()[-1].UID())

    def __call__(self):
        return self.enumerate_versions()

    def _obj_info(self, obj):
        """ Extract needed properties for a given persistent object
        """
        state_id = self.wftool().getInfoFor(obj, 'review_state', '(Unknown)')
        state = self.state_title_getter(obj)

        date = None
        field = obj.getField('lastUpload') #Note: specific to dataservice
        if field:
            date = field.getAccessor(obj)()
        else:
            date = obj.getEffectiveDate() or obj.creation_date
        if not isinstance(date, DateTime):
            date = None

        return {
            'title'        : obj.title_or_id(),
            'url'          : obj.absolute_url(),
            'date'         : date,
            'review_state' : state_id,
            'title_state'  : state,
        }

    def getLatestVersionUrl(self):
        """returns the url of the latest version @@getLatestVersionUrl view
        """

        return self.latest_version().absolute_url()


class GetVersionsView(BrowserView, GetVersions):
    """ The @@getVersions view
    """

    def __init__(self, context, request):
        BrowserView.__init__(self, context, request)
        GetVersions.__init__(self, context)


class GetWorkflowStateTitle(BrowserView):   #what is this used for?
    """ Returns the title of the workflow state of the given object
    """

    def __call__(self, obj=None):
        title_state = 'Unknown'
        if obj:
            wftool = getToolByName(self.context, 'portal_workflow')
            review_state = wftool.getInfoFor(obj, 'review_state', '(Unknown)')

            try:
                title_state = wftool.getWorkflowsFor(obj)[0].\
                        states[review_state].title
            except Exception, err:
                logger.info(err)

        return title_state


def isVersionEnhanced(context):
    """ Returns bool if context implements IVersionEnhanced """

    return bool(IVersionEnhanced.providedBy(context))


class IsVersionEnhanced(object):
    """ Check if object is implements IVersionEnhanced
    """

    def __init__(self, context, request):

        self.context = context
        self.request = request

    def __call__(self):
        return isVersionEnhanced(self.context)


class CreateVersion(object):
    """ This view, when called, will create a new version of an object
    """
    implements(ICreateVersionView)

    # usable by ajax view to decide if it should load this view instead
    # of just executing it. The use case is to have a @@createVersion
    # view with a template that allows the user to make some choice
    has_custom_behaviour = False

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self):
        ver = self.create()
        return self.request.RESPONSE.redirect(ver.absolute_url())

    def create(self):
        """create a version
        """
        return create_version(self.context)


class CreateVersionAjax(object):
    """ Used by javascript to create a new version in a background thread
    """

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self):
        # We use the view instead of calling create_version to allow for
        # packages to override how versions are created.
        # If view.has_custom_template is True, it means that the view wants
        # the user to make a decision. We treat this case in javascript

        view = getMultiAdapter((self.context, self.request),
                                name="createVersion")
        if getattr(view, 'has_custom_behaviour', False):
            return "SEEURL: %s/@@createVersion" % self.context.absolute_url()
        else:
            view.create()
            return "OK"


def create_version(context, reindex=True):
    """Create a new version of an object

    This is done by copy&pasting the object, then assigning, as
    versionId, the one from the original object.

    Additionally, we rename the object using a number based scheme and
    then clean it up to avoid various problems.
    """
    logger.info("Started creating version of %s", context.absolute_url())

    obj_id = context.getId()
    parent = utils.parent(context)

    # Adapt version parent (if case)
    if not IVersionEnhanced.providedBy(context):
        alsoProvides(context, IVersionEnhanced)

    #_ = IVersionControl(context).getVersionId()

    # Create version object
    clipb = parent.manage_copyObjects(ids=[obj_id])
    res = parent.manage_pasteObjects(clipb)

    new_id = res[0]['new_id']

    ver = getattr(parent, new_id)

    # Fixes the generated id: remove copy_of from ID
    #ZZZ: add -vX sufix to the ids
    vid = ver.getId()
    new_id = vid.replace('copy_of_', '')
    new_id = generateNewId(parent, new_id)
    parent.manage_renameObject(id=vid, new_id=new_id)
    ver = parent[new_id]

    # Set effective date today
    ver.setCreationDate(DateTime())
    ver.setEffectiveDate(None)
    ver.setExpirationDate(None)

    # Remove comments
    if hasNewDiscussion:
        conversation = IConversation(ver)
        while conversation.keys():
            conversation.__delitem__(conversation.keys()[0])
    else:
        if hasattr(aq_base(ver), 'talkback'):
            tb = ver.talkback
            if tb is not None:
                for obj in tb.objectValues():
                    obj.__of__(tb).unindexObject()
                tb._container = PersistentMapping()

    notify(VersionCreatedEvent(ver, context))

    if reindex:
        ver.reindexObject()
        #some catalogued values of the context may depend on versions
        _reindex(context)

    logger.info("Created version at %s", ver.absolute_url())

    return ver


def assign_version(context, new_version):
    """Assign a specific version id to an object"""

    # Verify if there are more objects under this version
    cat = getToolByName(context, 'portal_catalog')
    brains = cat.searchResults({'getversionid' : new_version,
                                'show_inactive': True})
    if brains and not IVersionEnhanced.providedBy(context):
        alsoProvides(context, IVersionEnhanced)
    if len(brains) == 1:
        target_ob = brains[0].getObject()
        if not IVersionEnhanced.providedBy(target_ob):
            alsoProvides(target_ob, IVersionEnhanced)

    # Set new version ID
    verparent = IVersionControl(context)
    verparent.setVersionId(new_version)
    context.reindexObject()


class AssignVersion(object):
    """ Assign new version ID
    """

    def __call__(self):
        pu = getToolByName(self.context, 'plone_utils')
        new_version = self.request.form.get('new-version', '').strip()
        nextURL = self.request.form.get('nextURL', self.context.absolute_url())

        if new_version:
            assign_version(self.context, new_version)
            message = _(u'Version ID changed.')
        else:
            message = _(u'Please specify a valid Version ID.')

        pu.addPortalMessage(message, 'structure')
        return self.request.RESPONSE.redirect(nextURL)


def revoke_version(context):    #this should not exist ???
    """Assigns a new random id to context, make it split from it version group
    """
    IVersionControl(context).setVersionId(_random_id(context))

#   obj = context
#   verparent = IVersionControl(obj)
#   verparent.setVersionId('')
#   directlyProvides(obj, directlyProvidedBy(obj)-IVersionEnhanced)


class RevokeVersion(object):
    """ Revoke the context as being a version
    """

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self):
        revoke_version(self.context)
        pu = getToolByName(self.context, 'plone_utils')
        message = _(u'Version revoked.')
        pu.addPortalMessage(message, 'structure')

        return self.request.RESPONSE.redirect(self.context.absolute_url())


def assign_new_version_id(obj, event):
    """Assigns a version id to newly created objects
    """
    versionId = IAnnotations(obj).get(VERSION_ID)
    if not versionId:
        IAnnotations(obj)[VERSION_ID] = _random_id(obj)


class GetContextInterfaces(object):
    """Utility view that returns a list of FQ dotted interface names

    ZZZ: should remove, replace with

    is_video python:context.restrictedTraverse('@@plone_interfaces_info').\
             item_interfaces.provides('eea.mediacentre.interfaces.IVideo');
    """
    implements(IGetContextInterfaces)

    def __call__(self):
        ifaces = providedBy(self.context)
        return ['.'.join((iface.__module__, iface.__name__))
                        for iface in ifaces]

    def has_any_of(self, iface_names):
        """Check if object implements any of given interfaces"""
        ifaces = providedBy(self.context)
        ifaces = set(['.'.join((iface.__module__, iface.__name__))
                        for iface in ifaces])
        return bool(ifaces.intersection(iface_names))


def generateNewId(location, gid):
    """generate a new id in a series, based on existing id"""

    if "-" in gid:  #remove a possible sufix -number from the id
        if gid.split('-')[-1].isdigit():
            gid = '-'.join(gid.split('-')[:-1])

    context_ids = location.objectIds()
    new_id      = gid
    i           = 1
    while True:     #now we try to generate a unique id
        if new_id not in context_ids:
            break
        new_id = "%s-%s" % (gid, i)
        i += 1

    return new_id


def _random_id(context, size=10):
    """returns a random arbitrary sized string, usable as version id
    """
    try:
        catalog = getToolByName(context, "portal_catalog")
    except AttributeError:
        catalog = None  #can happen in tests
    chars = "ABCDEFGHIJKMNOPQRSTUVWXYZ0123456789"
    res = "".join(random.sample(chars, size))

    #while True
    for x in range(0, 100000):
        if not catalog:
            break
        if not catalog.Indexes.get('getVersionId'):
            break
        if not catalog.searchResults(getVersionId=res):
            break
        res = "".join(random.sample(chars, size))

    return res


def _reindex(obj, catalog_tool=None):
    """ Reindex document
    """
    if not catalog_tool:
        catalog_tool = getToolByName(obj, 'portal_catalog')
    catalog_tool.reindexObject(obj)
