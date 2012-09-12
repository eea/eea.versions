"""main eea.versions module
"""

from Acquisition import aq_base
from DateTime import DateTime
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone import PloneMessageFactory as _
from Products.CMFPlone import utils
from Products.Five import BrowserView
from eea.versions.events import VersionCreatedEvent
from eea.versions.interfaces import ICreateVersionView
from eea.versions.interfaces import IGetVersions, IGetContextInterfaces
from eea.versions.interfaces import IVersionControl, IVersionEnhanced
from Persistence import PersistentMapping
from persistent.dict import PersistentDict
from zope.annotation.interfaces import IAnnotations
from zope.cachedescriptors.property import Lazy
from zope.component import adapts
from zope.component import queryMultiAdapter, getMultiAdapter
from zope.event import notify
from zope.interface import alsoProvides, directlyProvides, directlyProvidedBy
from zope.interface import implements, providedBy
import logging
import random

hasNewDiscussion = True
try:
    from plone.app.discussion.interfaces import IConversation
except ImportError:
    hasNewDiscussion = False

logger = logging.getLogger('eea.versions.versions')

VERSION_ID = 'versionId'

def _reindex(obj):
    """ Reindex document
    """
    ctool = getToolByName(obj, 'portal_catalog')
    ctool.reindexObject(obj)


def _get_random(context, size=0):
    """returns a random id, usable as version id
    """
    try:
        catalog = getToolByName(context, "portal_catalog")
    except AttributeError:
        catalog = None  #can happen in tests
    chars = "ABCDEFGHIJKMNOPQRSTUVWXYZ023456789"

    while True:
        res = ''
        for _k in range(size):
            res += random.choice(chars)
        if catalog and not catalog.searchResults(getVersionId=res):
            break
        if not catalog:
            break

    return res


class VersionControl(object):
    """ Version adapter

    ZZZ: creating an adapter instance of an object has the side-effect of making
    that object versioned. This is not very intuitive
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
            #_reindex(context)

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
        #ZZZ: to be implemented
        pass


class GetVersions(object):
    """ Get all versions
    """
    implements(IGetVersions)

    def __init__(self, context, request):
        """constructor"""
        self.context = context
        self.request = request
    
    #ZZZ: replace Lazy with @memoize from plone
    @Lazy
    def versions(self):
        """ Returns versions objects"""
        ver = IVersionControl(self.context)
        verId = ver.getVersionId()

        if not verId:
            return {}

        cat = getToolByName(self.context, 'portal_catalog')
        query = {'getVersionId' : verId}
        mtool = getToolByName(self.context, 'portal_membership')
        if mtool.isAnonymousUser():
            query['review_state'] = 'published'

        brains = cat(**query)
        objects = [b.getObject() for b in brains]

        # Some objects don't have EffectiveDate so we have to sort 
        # them using CreationDate
        sortedObjects = sorted(objects, 
                key=lambda o: o.effective_date or o.creation_date)

        versions = {}
        for index, ob in enumerate(sortedObjects):
            versions[index+1] = ob
        return versions

    def extract(self, version):
        """ Extract needed properties
        """
        wftool = getToolByName(version, 'portal_workflow')
        review_state = wftool.getInfoFor(version, 'review_state', '(Unknown)')

        # Get title of the workflow state
        getWorkflowStateTitle = queryMultiAdapter((self.context, self.request),
                name=u'getWorkflowStateTitle')
        if getWorkflowStateTitle:
            title_state = getWorkflowStateTitle(obj=version)
        else:
            title_state = 'Unknown'

        field = version.getField('lastUpload') #ZZZ: specific to dataservice
        if not field:
            value = version.getEffectiveDate()
            if not value:
                value = version.creation_date
        else:
            value = field.getAccessor(version)()

        if not isinstance(value, DateTime):
            value = None

        return {
            'title': version.title_or_id(),
            'url': version.absolute_url(),
            'date': value,
            'review_state': review_state,
            'title_state': title_state,
        }

    def version_number(self):
        """ Return the current version number
        """
        for k, v in self.versions.items():
            if v == self.context:
                return k
        return 0

    def newest(self):
        """ Return info on new versions
        """
        versions = self.versions.items()
        versions.sort(reverse=True)

        res = []
        found = False
        uid = self.context.UID()
        for _key, version in versions:
            if version.UID() == uid:
                found = True
                break
            res.append(self.extract(version))

        if not found:
            return []
        return res

    #ZZZ: add first_version method
    def latest_version(self):
        """Returns the latest version of an object"""

        if not self.versions:
            return self.context

        latest = sorted(self.versions.keys())[-1]
        return self.versions[latest]
    
    def isLatest(self):
        """ return true if this object is latest version
        """
        return self.context == self.latest_version()

    def oldest(self):
        """ Return old versions
        """
        versions = self.versions.items()
        versions.sort()

        res = []
        found = False
        uid = self.context.UID()
        for _key, version in versions:
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
        return self.versions

    def getLatestVersionUrl(self):
        """returns the url of the latest version"""
        return self.latest_version().absolute_url()


def get_versions_api(context):
    """returns version api class
    """
    #ZZZ: at this moment the code sits in views, which makes it 
    #awkward to reuse this API in python code and tests. There are 
    #the get_..._api() functions
    #Treat those views as API classes. This can and should be refactored
    return GetVersions(context, request=None)


def get_latest_version_link(context):
    """method
    """
    IVersionControl(context) #ctrl = 
    anno = IAnnotations(context)
    ver = anno.get(VERSION_ID)
    return ver[VERSION_ID]


class GetLatestVersionLink(object):
    """ Get latest version link
    """

    def __init__(self, context, request):
        """constructor"""
        self.context = context
        self.request = request

    def __call__(self):
        """view implementation"""
        return get_latest_version_link(self.context)


def get_version_id(context):
    """method
    """
    res = None
    try:
        ver = IVersionControl(context)
        res = ver.getVersionId()
    except (TypeError, ValueError): #ComponentLookupError, 
        res = None

    return res


class GetVersionId(object):
    """ Get version ID
    """

    def __init__(self, context, request):
        """constructor"""
        self.context = context
        self.request = request

    def __call__(self):
        """view implementation"""
        return get_version_id(self.context)


class GetWorkflowStateTitle(BrowserView):
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


def get_version_id_api(context):
    """returns versionid api"""
    return GetVersionId(context, request=None)


def isVersionEnhanced(context):
    """returns bool if context can be version enhanced"""
    #ZZZ: this doesn't guarantee that there are versions
    #a better name for this would be "is_versionenhanced"
    if IVersionEnhanced.providedBy(context):
        return True
    return False


class IsVersionEnhanced(object):
    """ Check if object is marked as version enhanced
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
    """Create a new version of an object"""

    #pu = getToolByName(context, 'plone_utils')
    obj_id = context.getId()
    parent = utils.parent(context)

    # Adapt version parent (if case)
    if not IVersionEnhanced.providedBy(context):
        alsoProvides(context, IVersionEnhanced)
    verparent = IVersionControl(context)
    verId = verparent.getVersionId()
    if not verId:
        verId = _get_random(context, 10)
        verparent.setVersionId(verId)
        _reindex(context)

    # Create version object
    clipb = parent.manage_copyObjects(ids=[obj_id])
    #tibi test
    #res = pasteObjects(parent, clipb)
    res = parent.manage_pasteObjects(clipb)

    new_id = res[0]['new_id']

    ver = getattr(parent, new_id)

    # Fixes the generated id: remove copy_of from ID
    #ZZZ: add -vX sufix to the ids
    vid = ver.getId()
    new_id = vid.replace('copy_of_', '')
    new_id = generateNewId(parent, new_id, ver.UID())
    parent.manage_renameObject(id=vid, new_id=new_id)
    ver = parent[new_id]

    # Set effective date today
    ver.setCreationDate(DateTime())
    ver.setEffectiveDate(None)
    ver.setExpirationDate(None)

    # Remove comments
    if hasNewDiscussion:
        conversation = IConversation(aq_base(ver))
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


def revoke_version(context):
    """Revokes the context from being a version
    """
    obj = context
    verparent = IVersionControl(obj)
    verparent.setVersionId('')
    directlyProvides(obj, directlyProvidedBy(obj)-IVersionEnhanced)


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


def generateNewId(context, gid, uid):
    """generate a new id based on existing id"""
    tmp = gid.split('-')[-1]
    try:
        int(tmp)
        gid = '-'.join(gid.split('-')[:-1])
    except ValueError, err:
        logger.info(err)

    if gid in context.objectIds():
        tmp_ob = getattr(context, gid)
        if tmp_ob.UID() != uid:
            idx = 1
            while idx <= 100:
                new_id = "%s-%d" % (gid, idx)
                new_ob = getattr(context, new_id, None)
                if new_ob:
                    if new_ob.UID() != uid:
                        idx += 1
                    else:
                        gid = new_id
                        break
                else:
                    gid = new_id
                    break
    return gid


def versionIdHandler(obj, event):
    """ Set a versionId as annotation without setting the
        version marker interface just to have a perma link
        to last version
    """
    if not isVersionEnhanced(obj):
        verId = _get_random(obj, 10)
        anno = IAnnotations(obj)
        ver = anno.get(VERSION_ID)
        #ZZZ: tests fails with ver = None when adding an EEAFigure,
        #      remove "if ver:" after fix
        if ver:
            if not ver.values()[0]:
                ver[VERSION_ID] = verId
                _reindex(obj)


class GetContextInterfaces(object):
    """Utility view that returns a list of FQ dotted interface names"""
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


#old code that explored if it's possible to speed up versioning by 
#not triggering events when objects are copied
#unfortunately it caused problems because of those missing events
#living here, maybe this code is needed in the future


#from App.Dialogs import MessageDialog
#from OFS import Moniker
#from OFS.CopySupport import CopyError, _cb_decode, eInvalid, eNotFound
#from OFS.CopySupport import eNotSupported
#from ZODB.POSException import ConflictError
#from cgi import escape
#import sys
#def pasteObjects(context, cp):
    #"""a paste implementation which avoids throwing too many events
    #"""
    #try:
        #op, mdatas = _cb_decode(cp)
    #except Exception:
        #raise CopyError, eInvalid

    #oblist = []
    #app = context.getPhysicalRoot()
    #for mdata in mdatas:
        #m = Moniker.loadMoniker(mdata)
        #try:
            #ob = m.bind(app)
        #except ConflictError:
            #raise
        #except:
            #raise CopyError, eNotFound
        #context._verifyObjectPaste(ob, validate_src=op+1)
        #oblist.append(ob)

    #result = []
    #for ob in oblist:
        #orig_id = ob.getId()
        #if not ob.cb_isCopyable():
            #raise CopyError, eNotSupported % escape(orig_id)

        #try:
            #ob._notifyOfCopyTo(context, op=0)
        #except ConflictError:
            #raise
        #except Exception:
            #raise CopyError, MessageDialog(
                #title="Copy Error",
                #message=sys.exc_info()[1],
                #action='manage_main')

        #cid = context._get_id(orig_id)
        #result.append({'id': orig_id, 'new_id': cid})

        ##orig_ob = ob
        #ob = ob._getCopy(context)
        #ob._setId(cid)
        ##notify(ObjectCopiedEvent(ob, orig_ob))

        #context._setObject(cid, ob)
        #ob = context._getOb(cid)
        #ob.wl_clearLocks()

        #ob._postCopy(context, op=0)

        ##OFS.subscribers.compatibilityCall('manage_afterClone', ob, ob)

        ##notify(ObjectClonedEvent(ob))

        ##if REQUEST is not None:
            ##return self.manage_main(self, REQUEST, update_menu=1,
                                    ##cb_dataValid=1)
    #return result

