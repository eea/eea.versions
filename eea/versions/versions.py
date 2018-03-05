""" Main eea.versions module
"""
# pylint:disable=R0101
import logging
import sys
import warnings
from Acquisition import aq_base, aq_inner, aq_parent
from Persistence import PersistentMapping
from zope.interface import alsoProvides, implements, providedBy
from zope.annotation.interfaces import IAnnotations
from zope.component import adapts
from zope.component import queryAdapter, queryMultiAdapter, getMultiAdapter
from zope.component.hooks import getSite
from zope.event import notify
import transaction
from DateTime.DateTime import DateTime, time
from OFS.CopySupport import _cb_encode, _cb_decode, CopyError, eInvalid, \
    eNoData, eNotFound, eNotSupported, loadMoniker, ConflictError, \
    escape, MessageDialog, ObjectCopiedEvent, compatibilityCall, \
    ObjectClonedEvent, sanity_check, ObjectWillBeMovedEvent, \
    ObjectMovedEvent, notifyContainerModified, cookie_path
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone import PloneMessageFactory as _
from Products.CMFPlone import utils
from Products.Five.browser import BrowserView
from eea.versions.controlpanel.utils import new_version_id
from eea.versions.events import VersionCreatedEvent
from eea.versions.interfaces import ICreateVersionView
from eea.versions.interfaces import IGetVersions, IGetContextInterfaces
from eea.versions.interfaces import IVersionControl, IVersionEnhanced
from plone.memoize.instance import memoize

try:
    from plone.app.discussion.interfaces import IConversation
    hasNewDiscussion = True
except ImportError:
    hasNewDiscussion = False

try:
    from eea.dataservice.content.Permalink import zmi_addPermalinkMapping
    hasDataservice = True
except ImportError:
    hasDataservice = False

logger = logging.getLogger('eea.versions.versions')

VERSION_ID = 'versionId'


class VersionControl(object):
    """ Version adapter
    """

    implements(IVersionControl)
    adapts(IVersionEnhanced)

    def __init__(self, context):
        """ Initialize adapter
        """
        self.context = context
        self.annot = IAnnotations(context)

    def getVersionId(self):
        """ Get version id
        """
        return self.annot.get(VERSION_ID)

    def setVersionId(self, value):
        """ Set version id
        """
        self.annot[VERSION_ID] = value

    versionId = property(getVersionId, setVersionId)

    def can_version(self):
        """ Can new versions be created?
        """
        return True  # adapt, subclass and override if needed


class CanCreateNewVersion(object):
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

    def __init__(self, context):
        """ Constructor
        """
        request = getattr(context, 'REQUEST', None)
        state = getMultiAdapter((context, request), name='plone_context_state')
        # fix for folders with a default view set, when creating a
        # version, we need the folder, not the page
        self.context = context
        if state.is_default_page():
            parent = aq_parent(context)
            if IVersionEnhanced.providedBy(parent):
                self.context = parent

        self.versionId = IVersionControl(self.context).versionId

        failsafe = lambda obj: "Unknown"
        self.state_title_getter = queryMultiAdapter((self.context, request),
                                    name=u'getWorkflowStateTitle') or failsafe

    @memoize
    def versions(self):
        """ Return a list of sorted version objects
        """
        # Avoid making a catalog call if versionId is empty
        if not self.versionId:
            return [self.context]

        if not isinstance(self.versionId, basestring):
            return [self.context]  # this is an old, unmigrated storage
        cat = getToolByName(self.context, 'portal_catalog', None)
        if not cat:
            return []
        query = {'getVersionId': self.versionId}

        mtool = getToolByName(self.context, 'portal_membership')
        if mtool.isAnonymousUser():
            query['review_state'] = 'published'
            brains = cat.unrestrictedSearchResults(**query)
        else:
            brains = cat(**query)
        objects = []
        for b in brains:
            try:
                obj = b.getObject()
            except Exception as err:
                # Because of the unrestricted search done above, this
                # might happen, and we don't need a crash. Also do not
                # crash if the object is missing/not re-indexed yet.
                logger.warn(err)
                continue
            else:
                objects.append(obj)


        # Some objects don't have EffectiveDate so we have to sort
        # them using CreationDate. This has the side effect that
        # in certain conditions the list of versions is reordered
        # For the anonymous users this is never a problem because
        # they only see published (and with effective_date) objects

        # during creation self.context has not been indexed
        if not self.context.UID() in [o.UID() for o in objects if o]:
            objects.append(self.context)

        # Store versions as ordered list, with the oldest item first
        # #20827 check if creation_date isn't bigger than the effective
        # date of the object as there are situation where the effective_date
        # is smaller such as for object without an workflow like FigureFile
        _versions = sorted(objects,
                           key=lambda ob: ob.effective_date if ob.effective_date
                           else ob.creation_date)

        return _versions

    @memoize
    def wftool(self):
        """ Memoized portal_workflow
        """
        return getToolByName(self.context, 'portal_workflow')

    @memoize
    def enumerate_versions(self):  # rename from versions
        """ Returns a mapping of version_number:object
        """

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

        res.reverse()  # is this needed?
        return res

    def latest_version(self):
        """ Returns the latest version of an object
        """
        return self.versions()[-1]

    def first_version(self):
        """ Returns the first version of an object
        """
        return self.versions()[0]

    def isLatest(self):
        """ Return true if this object is latest version
        """
        return self.context.UID() == self.versions()[-1].UID()

    def __call__(self):
        return self.enumerate_versions()

    def _obj_info(self, obj):
        """ Extract needed properties for a given persistent object
        """
        state_id = self.wftool().getInfoFor(obj, 'review_state', '(Unknown)')
        state = self.state_title_getter(obj)

        field = obj.getField('lastUpload')  # Note: specific to dataservice
        if field:
            date = field.getAccessor(obj)()
        else:
            date = obj.getEffectiveDate() or obj.creation_date
        if not isinstance(date, DateTime):
            date = None

        return {
            'title': obj.title_or_id(),
            'url': obj.absolute_url(),
            'date': date,
            'review_state': state_id,
            'title_state': state,
        }

    def getLatestVersionUrl(self):
        """ Returns the url of the latest version @@getLatestVersionUrl view
        """

        return self.latest_version().absolute_url()

    def getCurrentLanguage(self):
        """ Return the language of the context
        """
        context = self.context
        portal_state = context.unrestrictedTraverse("@@plone_portal_state")
        lang = aq_inner(context).Language() or portal_state.default_language()

        if lang == 'en':
            return ''
        return '/' + lang


class GetVersionsView(BrowserView, GetVersions):
    """ The @@getVersions view
    """

    def __init__(self, context, request):
        BrowserView.__init__(self, context, request)
        GetVersions.__init__(self, context)


def migrate_version(brains, vobj, count, **kwargs):
    """ migrate_versions given brains and prefix
    """
    increment = True
    no_versions = []
    prefix = str(vobj.title)
    parent = None
    datasets = kwargs.get('datasets')
    if datasets:
        site = getSite()
        parent = site.get('eea_permalink_objects')
        if not parent:
            parent_id = site.invokeFactory('Folder', 'eea_permalink_objects')
            parent = site[parent_id]

    for brain in brains:
        obj = brain.getObject()
        if not obj:
            continue
        adapter = queryAdapter(obj, IGetVersions)
        if not adapter:
            no_versions.append(obj.absolute_url())
            continue

        versions = adapter.versions()
        latest_version = versions[-1]
        for obj in versions:
            verparent = IVersionControl(obj)
            verparent_id = verparent.versionId
            if prefix not in verparent_id:
                version_id = "{0}-{1}".format(prefix, count)
                orig_id = version_id
                if vobj.prefix_with_language:
                    version_id = version_id + '-' + obj.getLanguage()
                if getattr(obj, 'getTranslations', None):
                    translations = obj.getTranslations()
                    if len(translations) > 1:
                        canonical = obj.getCanonical()
                        if vobj.prefix_with_language:
                            version_id = orig_id + '-' + canonical.getLanguage()
                        IVersionControl(canonical).setVersionId(version_id)
                        canonical.reindexObject(idxs=['getVersionId'])
                        for trans_tuple in translations.items():
                            translation = trans_tuple[1][0]
                            if translation != canonical:
                                version_id = orig_id + '-' + trans_tuple[0]
                                IVersionControl(translation).setVersionId(
                                    version_id)
                                translation.reindexObject(idxs=['getVersionId'])
                    else:
                        if datasets and obj is latest_version:
                            vid = IGetVersions(obj).versionId
                            zmi_addPermalinkMapping(parent, vid, version_id)
                        verparent.setVersionId(version_id)
                        obj.reindexObject(idxs=['getVersionId'])
                else:
                    verparent.setVersionId(version_id)
                    obj.reindexObject(idxs=['getVersionId'])
                increment = True
                logger.info('%s ==> %s --> %s',
                    obj.absolute_url(1), verparent_id, version_id)
            else:
                increment = False
        if increment:
            count += 1
            if count % 50 == 0:
                transaction.commit()
    logger.info("MIGRATION DONE")
    return count


class MigrateVersions(BrowserView):
    """ MigrateVersions
    """
    def __init__(self, context, request):
        super(MigrateVersions, self).__init__(context, request)
        self.request = request
        self.context = context

    def migrate_versions(self, **kwargs):
        """ migrate_versions given brains and prefix
        """
        context = self.context
        kwargs = kwargs or self.request.form
        cat = self.context.portal_catalog
        count = 1
        prefix = kwargs.get('prefix')
        logger.info('PREFIX IS %s', prefix)
        if prefix:
            prefix = prefix.split(',')

        query = {
            "Language": "all",
            "show_inactive": True,
            "sort_on": "created",
        }

        result = []
        vtool = getToolByName(context, 'portal_eea_versions', None)
        ptool = getToolByName(context, 'portal_properties')
        stool = ptool.site_properties
        datasets_types = stool.get('dataset_types') or \
                         ['Assessment', 'Data', 'EEAFigure',
                          'Specification', 'Indicator FactSheet']
        if vtool:
            for obj in vtool.values():
                if prefix and obj.title not in prefix:
                    continue
                prefix = obj.title
                search_type = obj.search_type
                search_iface = obj.search_interface
                if search_type:
                    query['portal_type'] = search_type
                    if query.get('object_provides'):
                        del query['object_provides']
                if search_iface:
                    query['object_provides'] = search_iface
                    if query.get('portal_type'):
                        del query['portal_type']

                datasets = False
                if query.get('portal_type', []) in datasets_types:
                    datasets = True
                brains = cat(**query)
                last_number = migrate_version(brains, obj, count,
                                              datasets=datasets)
                obj.last_assigned_version_number = last_number
                result.append(last_number)
            return result
        return "portal_eea_versions tool is not found, no migration will" \
               " be performed"

    def __call__(self, **kwargs):
        """ Ex call migrateVersions?prefix=FIS
            migrateVersions?prefix=FIS,IMG
            if we want to manually run it later with specific values
            bypassing therefore the other objects that are added
        """
        return self.migrate_versions(**kwargs)


class GetWorkflowStateTitle(BrowserView):
    """ Returns the title of the workflow state of the given object
        used on versions viewlet letting you know that there is
        a new version with the review state Title
    """

    def __call__(self, obj=None):
        title_state = 'Unknown'
        if obj:
            wftool = getToolByName(self.context, 'portal_workflow')
            review_state = wftool.getInfoFor(obj, 'review_state', title_state)
            if review_state == title_state:
                return title_state
            try:
                title_state = wftool.getWorkflowsFor(obj)[0]. \
                    states[review_state].title
            except Exception, err:
                logger.info(err)

        return title_state


def isVersionEnhanced(context):
    """ Returns bool if context implements IVersionEnhanced
    """

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
        """ Create a version
        """
        return create_version(self.context)


class AjaxVersion(object):
    """ Ajax Versioning progress
    """
    def __init__(self, context, request):
        self.context = context
        self.url = context.absolute_url()
        self.request = request
        self.annotations = self.context.__annotations__

    def get_logged_in_user(self):
        """
        :return: user id
        :rtype:  string
        """
        portal_membership = getToolByName(self.context, 'portal_membership',
                                          None)
        if not portal_membership:
            return "UNKNOWN"
        return portal_membership.getAuthenticatedMember().getId()

    def __call__(self):
        version_status = self.check_versioning_status()
        if version_status:
            return version_status
        if "startVersioning" in self.request:
            return self.set_versioning_status()
        return "NO VERSION IN PROGRESS"

    def check_versioning_status(self):
        """ Check if versioning is present and didn't take longer than 15
        minutes
        """
        in_progress = self.annotations.get('versioningInProgress')
        # 22047 check if it took less than 15 minutes since last check
        # if context still has the versioningInProgress annotation
        # otherwise request a new version creation
        # this is done to prevent situations were a new version was requested
        # and annotation was set but afterwards there was an error or the server
        # was restarted as such no removing of versioning status being produced
        if in_progress and (time() - in_progress) < 900.0:
            logger.info('VersioningInProgress in_progress at %s, now %s '
                        ', time since last run == %f',
                        in_progress, time(), time() - in_progress)
            return "IN PROGRESS"

    def set_versioning_status(self):
        """ Set time of versioning creation
        """
        now = DateTime()
        self.annotations["versioningInProgress"] = time()
        user = self.get_logged_in_user()
        logger.info("VersioningInProgress set for %s by %s at %s", self.url,
                    user, now)
        return "VERSIONING STARTED"

    def remove_versioning_status(self):
        """ Remove versioning status from object annotations
        """
        self.annotations["versioningInProgress"] = False
        logger.info("VersioningInProgress removed for %s", self.url)


class CreateVersionAjax(object):
    """ Used by javascript to create a new version in a background thread
    """
    def __init__(self, context, request):
        state = getMultiAdapter((context, request), name='plone_context_state')
        # fix for folders with a default view set, when creating a
        # version, we need the folder, not the page
        parent = state.canonical_object()
        if IVersionEnhanced.providedBy(parent):
            self.context = parent
        else:
            self.context = context
        self.url = self.context.absolute_url()
        self.request = request

    def __call__(self):
        view = getMultiAdapter((self.context, self.request),
                               name="createVersion")
        if getattr(view, 'has_custom_behaviour', False):
            return "SEEURL: %s/@@createVersion" % self.url
        else:
            try:
                view.create()
            finally:
                # remove the in progress status from annotation
                # on version creation or in case of an error
                view = getMultiAdapter((self.context, self.request),
                                       name="ajaxVersion")
                view.remove_versioning_status()
            return "OK"


def create_version(context, reindex=True):
    """ Create a new version of an object

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

    # _ = IVersionControl(context).getVersionId()

    # Create version object
    # 1. copy object
    clipb = parent.manage_copyObjects(ids=[obj_id])

    # 2. pregenerate new id for the copy
    new_id = generateNewId(parent, obj_id)
    # 3. alter the clipboard data and inject the desired new id
    clipb_decoded = _cb_decode(clipb)
    clipb = _cb_encode((clipb_decoded[0], clipb_decoded[1], [new_id]))
    # 4. call paste operation
    manage_pasteObjects_Version(parent, clipb)
    # 5. get the version object - no need for a rename anymore
    ver = parent[new_id]

    # #31440 apply related items from original object to the new version
    ver.setRelatedItems(context.getRelatedItems())

    # Set effective date today
    ver.setCreationDate(DateTime())
    ver.setEffectiveDate(None)
    ver.setExpirationDate(None)

    mtool = getToolByName(context, 'portal_membership')
    auth_user = mtool.getAuthenticatedMember()
    auth_username = auth_user.getUserName()
    auth_username_list = [auth_username]
    current_creators = ver.Creators()
    auth_username_list.extend(current_creators)
    username_list = []
    for name in auth_username_list:
        if name == auth_username and name in username_list:
            continue
        else:
            username_list.append(name)
    new_creators = tuple(username_list)
    ver.setCreators(new_creators)

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
        # some catalogued values of the context may depend on versions
        _reindex(context)

    logger.info("Created version at %s", ver.absolute_url())

    return ver


def assign_version(context, new_version):
    """ Assign a specific version id to an object
    """

    # Verify if there are more objects under this version
    cat = getToolByName(context, 'portal_catalog')
    brains = cat.searchResults({'getVersionId': new_version,
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
    context.reindexObject(idxs=['getVersionId'])


def assign_new_version_id(obj, event):
    """Assigns a version id to newly created objects
    """
    # 70786 avoid adding new versions to objects found in portal_factory
    # during creating and saving of object this event is called 8 times
    # and we only need to apply a version to the object when it is out of
    # portal_factory
    if 'portal_factory' in obj.absolute_url():
        return
    version_id = IAnnotations(obj).get(VERSION_ID)
    if not version_id:
        IAnnotations(obj)[VERSION_ID] = new_version_id(obj)


class AssignVersion(object):
    """ Assign new version ID
    """

    def __call__(self):
        pu = getToolByName(self.context, 'plone_utils')
        new_version = self.request.form.get('new-version', '').strip()
        nextURL = self.request.form.get('nextURL', self.context.absolute_url())
        # #87691 append /view for ptypes that need it in order to avoid file
        # download
        pprops = getToolByName(self.context, 'portal_properties')
        if pprops:
            sprops = pprops.site_properties
            if self.context.portal_type in sprops.typesUseViewActionInListings:
                if nextURL[-5:] != '/view':
                    nextURL += '/view'
        if new_version:
            assign_version(self.context, new_version)
            message = _(u'Version ID changed.')
        else:
            message = _(u'Please specify a valid Version ID.')

        pu.addPortalMessage(message, 'structure')
        return self.request.RESPONSE.redirect(nextURL)


def revoke_version(context):
    """ Assigns a new random id to context, make it split from it version group
    """
    IVersionControl(context).setVersionId(new_version_id(context))


class RevokeVersion(object):
    """ Revoke the context as being a version
    """

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self):
        revoke_version(self.context)
        self.context.reindexObject(idxs=['getVersionId'])
        pu = getToolByName(self.context, 'plone_utils')
        message = _(u'Version revoked.')
        pu.addPortalMessage(message, 'structure')

        # #87691 append /view for ptypes that need it in order to avoid file
        # download
        nextURL = self.context.absolute_url()
        pprops = getToolByName(self.context, 'portal_properties')
        if pprops:
            sprops = pprops.site_properties
            if self.context.portal_type in sprops.typesUseViewActionInListings:
                if nextURL[-5:] != '/view':
                    nextURL += '/view'

        return self.request.RESPONSE.redirect(nextURL)


class GetContextInterfaces(object):
    """ Utility view that returns a list of FQ dotted interface names

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
        """ Check if object implements any of given interfaces
        """
        ifaces = providedBy(self.context)
        ifaces = set(['.'.join((iface.__module__, iface.__name__))
                      for iface in ifaces])
        return bool(ifaces.intersection(iface_names))


def generateNewId(location, gid):
    """ Generate a new id in a series, based on existing id
    """

    if "-" in gid:  # remove a possible sufix -number from the id
        if gid.split('-')[-1].isdigit():
            gid = '-'.join(gid.split('-')[:-1])

    context_ids = location.objectIds()
    new_id = gid
    i = 1
    while True:  # now we try to generate a unique id
        if new_id not in context_ids:
            break
        new_id = "%s-%s" % (gid, i)
        i += 1

    return new_id


def _reindex(obj, catalog_tool=None):
    """ Reindex document
    """
    if not catalog_tool:
        catalog_tool = getToolByName(obj, 'portal_catalog')
    catalog_tool.reindexObject(obj)


def manage_pasteObjects_Version(self, cb_copy_data=None, REQUEST=None):
    """Paste previously copied objects into the current object.

    If calling manage_pasteObjects from python code, pass the result of a
    previous call to manage_cutObjects or manage_copyObjects as the first
    argument.

    Also sends IObjectCopiedEvent and IObjectClonedEvent
    or IObjectWillBeMovedEvent and IObjectMovedEvent.
    """
    ### due to the ticket #14598: the need to also handle a cb_copy_data
    ### structure that contains the desired new id on a copy/paste operation.
    ### this feature will be used when creating a new version for an object.
    ### if there is no new id also incapsulated in the cb_copy_data then
    ### the copy/paste will work as default.
    ### also the cut/paste remains the same.
    if cb_copy_data is not None:
        cp = cb_copy_data
    elif REQUEST is not None and REQUEST.has_key('__cp'):
        cp = REQUEST['__cp']
    else:
        cp = None
    if cp is None:
        raise CopyError(eNoData)

    try:
        op, mdatas, newids = _cb_decode(cp)
    except Exception:
        try:
            op, mdatas = _cb_decode(cp)
            newids = []
        except Exception:
            raise CopyError(eInvalid)
    else:
        if len(mdatas) != len(newids):
            raise CopyError(eInvalid)

    oblist = []
    app = self.getPhysicalRoot()
    for mdata in mdatas:
        m = loadMoniker(mdata)
        try:
            ob = m.bind(app)
        except ConflictError:
            raise
        except:
            raise CopyError(eNotFound)
        self._verifyObjectPaste(ob, validate_src=op+1)
        oblist.append(ob)

    if len(newids) == 0:
        newids = ['']*len(oblist)

    result = []
    if op == 0:
        # Copy operation
        for ob, new_id in zip(oblist, newids):
            orig_id = ob.getId()
            if not ob.cb_isCopyable():
                raise CopyError(eNotSupported % escape(orig_id))

            try:
                ob._notifyOfCopyTo(self, op=0)
            except ConflictError:
                raise
            except:
                raise CopyError(MessageDialog(
                    title="Copy Error",
                    message=sys.exc_info()[1],
                    action='manage_main'))

            if new_id == '':
                new_id = self._get_id(orig_id)
            result.append({'id': orig_id, 'new_id': new_id})

            orig_ob = ob
            ob = ob._getCopy(self)
            ob._setId(new_id)
            notify(ObjectCopiedEvent(ob, orig_ob))

            self._setObject(new_id, ob)
            ob = self._getOb(new_id)
            ob.wl_clearLocks()

            ob._postCopy(self, op=0)

            compatibilityCall('manage_afterClone', ob, ob)

            notify(ObjectClonedEvent(ob))

        if REQUEST is not None:
            return self.manage_main(self, REQUEST, update_menu=1,
                                    cb_dataValid=1)

    elif op == 1:
        # Move operation
        for ob in oblist:
            orig_id = ob.getId()
            if not ob.cb_isMoveable():
                raise CopyError(eNotSupported % escape(orig_id))

            try:
                ob._notifyOfCopyTo(self, op=1)
            except ConflictError:
                raise
            except:
                raise CopyError(MessageDialog(
                    title="Move Error",
                    message=sys.exc_info()[1],
                    action='manage_main'))

            if not sanity_check(self, ob):
                raise CopyError(
                        "This object cannot be pasted into itself")

            orig_container = aq_parent(aq_inner(ob))
            if aq_base(orig_container) is aq_base(self):
                new_id = orig_id
            else:
                new_id = self._get_id(orig_id)
            result.append({'id': orig_id, 'new_id': new_id})

            notify(ObjectWillBeMovedEvent(ob, orig_container, orig_id,
                                          self, new_id))

            # try to make ownership explicit so that it gets carried
            # along to the new location if needed.
            ob.manage_changeOwnershipType(explicit=1)

            try:
                orig_container._delObject(orig_id, suppress_events=True)
            except TypeError:
                orig_container._delObject(orig_id)
                warnings.warn(
                    "%s._delObject without suppress_events is discouraged."
                    % orig_container.__class__.__name__,
                    DeprecationWarning)
            ob = aq_base(ob)
            ob._setId(new_id)

            try:
                self._setObject(new_id, ob, set_owner=0, suppress_events=True)
            except TypeError:
                self._setObject(new_id, ob, set_owner=0)
                warnings.warn(
                    "%s._setObject without suppress_events is discouraged."
                    % self.__class__.__name__, DeprecationWarning)
            ob = self._getOb(new_id)

            notify(ObjectMovedEvent(ob, orig_container, orig_id, self, new_id))
            notifyContainerModified(orig_container)
            if aq_base(orig_container) is not aq_base(self):
                notifyContainerModified(self)

            ob._postCopy(self, op=1)
            # try to make ownership implicit if possible
            ob.manage_changeOwnershipType(explicit=0)

        if REQUEST is not None:
            REQUEST['RESPONSE'].setCookie('__cp', 'deleted',
                                path='%s' % cookie_path(REQUEST),
                                expires='Wed, 31-Dec-97 23:59:59 GMT')
            REQUEST['__cp'] = None
            return self.manage_main(self, REQUEST, update_menu=1,
                                    cb_dataValid=0)

    return result
