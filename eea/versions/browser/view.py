""" EEA Versions views
"""
import logging

from AccessControl import Unauthorized
from DateTime.DateTime import DateTime
from plone.app.uuid.utils import uuidToObject
from plone.memoize import view
from Products.CMFCore.WorkflowCore import WorkflowException
from Products.CMFEditions.utilities import maybeSaveVersion
from Products.Five import BrowserView
from Products.CMFCore.utils import getToolByName
from zope.component import getMultiAdapter
import transaction


class UpdateCreationDate(BrowserView):
    """ Update CreationDate if it's smaller than the EffectiveDate
        in which case we set the CreationDate to the value of EffectiveDate
    """

    def __init__(self, context, request):
        super(UpdateCreationDate, self).__init__(context, request)
        self.context = context
        self.request = request

    def __call__(self):
        logger = logging.getLogger()
        log_name = __name__ + '.' + self.__name__
        logger.info('STARTING %s browser view', log_name)
        catalog = getToolByName(self.context, 'portal_catalog', None)
        mt = getToolByName(self.context, 'portal_membership', None)
        rt = getToolByName(self.context, "portal_repository", None)
        wf = getToolByName(self.context, "portal_workflow", None)
        res = catalog(show_inactive="True", language="All",
                      sort_on="meta_type")
        count = 0
        objs_urls = []
        wf_error_objs = []
        wf_error_objs_count = 0
        reindex_error_objs = []
        reindex_error_objs_count = 0
        actor = mt.getAuthenticatedMember().id
        for brain in res:
            if brain.EffectiveDate != "None" and \
                            brain.effective < brain.created:
                obj = brain.getObject()
                obj_url = brain.getURL()
                try:
                    review_state = wf.getInfoFor(obj, 'review_state', 'None')
                except WorkflowException:
                    wf_error_objs_count += 1
                    wf_error_objs.append(obj_url)
                    continue
                previous_creation_date = obj.created()
                effective_date = obj.effective()
                obj.setCreationDate(effective_date)
                comment = "Fixed creation date < effective date (issue 21326" \
                          "). Changed creation date from %s to --> %s." % (
                              previous_creation_date,
                              effective_date)
                if not rt.isVersionable(obj):
                    objs_urls.append(brain.getURL(1))
                    history = obj.workflow_history # persistent mapping
                    for name, wf_entries in list(history.items()):
                        wf_entries = list(wf_entries)
                        wf_entries.append({'action': 'Edited',
                                           'review_state': review_state,
                                           'comments': comment,
                                           'actor': actor,
                                           'time': DateTime()})
                        history[name] = tuple(wf_entries)
                else:
                    maybeSaveVersion(obj, comment=comment, force=False)
                try:
                    obj.reindexObject(idxs=['created'])
                except Exception:
                    reindex_error_objs.append(obj_url)
                    reindex_error_objs_count += 1
                    logger.error("%s --> couldn't be reindexed", obj_url)
                    continue
                count += 1
                logger.info('Fixed %s', obj_url)
                objs_urls.append(obj_url)

                if count % 100 == 0:
                    transaction.commit()
        logger.info('ENDING %s browser view', log_name)
        message = \
            "REINDEX ERROR FOR %d objects \n %s \n" \
            "REVIEW STATE ERROR FOR %d objects \n %s \n" \
            "FIXED THE FOLLOWING OBJECTS %d %s" % (
            reindex_error_objs_count, "\n".join(reindex_error_objs),
            wf_error_objs_count, "\n".join(wf_error_objs),
            count, "\n".join(objs_urls))
        return message


class ReportVersionsHelperView(BrowserView):
    """ Helper view that return previous versions for reports
    """

    @property
    def is_report(self):
        return self.context.portal_type == 'Report'

    @view.memoize
    def report_versions(self):
        report_view = self.context.restrictedTraverse('@@report_view')
        versions = report_view.does_replace()

        res = []
        for ver in versions:
            obj = ver.getObject()
            state = getMultiAdapter((obj, self.request), name='plone_context_state')

            res.append({
                'url': obj.absolute_url(),
                'date': obj.effective(),
                'title': obj.Title(),
                'review_state': state.workflow_state(),
            })

        return res

    def patched_toLocalizedTime(self, date, obj):
        toLocalizedTime = self.context.restrictedTraverse('@@plone').toLocalizedTime
        try:
            formatted_date = toLocalizedTime(date)
        except ValueError:
            logger = logging.getLogger('eea.versions.patched_toLocalizedTime')
            logger.error('Date error for object: %s' % obj['url'])
            if date.year() < 1900:
                formatted_date = toLocalizedTime(0)
        return formatted_date


class GetDataForRedirect(object):
    """ Get objects to redirect
    """

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self, query=None):
        if query is None:
            query = {}
        cat = getToolByName(self.context, 'portal_catalog')
        res = cat(**query)
        if not res:
            # If no results published try searching for objects
            # in published_eionet state
            query['review_state'] = ['published', 'published_eionet']
            res = cat.unrestrictedSearchResults(**query)
        return res


class DsResolveUid(BrowserView):
    """
    """
    subpath = None

    def publishTraverse(self, request, name):
        self.uuid = name
        traverse_subpath = self.request['TraversalRequestNameStack']
        if traverse_subpath:
            traverse_subpath = list(traverse_subpath)
            traverse_subpath.reverse()
            self.subpath = traverse_subpath
            self.request['TraversalRequestNameStack'] = []
        return self

    def __call__(self):
        context = self.context
        request = context.REQUEST
        response = request.RESPONSE
        traverse_subpath = self.subpath
        uuid = self.uuid
        redirect = True

        if not uuid:
            try:
                uuid = traverse_subpath.pop(0)
            except:
                raise Unauthorized(context)

        try:
            reference_tool = getToolByName(context, 'reference_catalog')
            obj = reference_tool.lookupObject(uuid)
        except:
            obj = uuidToObject(uuid)

        if not obj:
            hook = getattr(context, 'kupu_resolveuid_hook', None)
            if hook:
                obj = hook(uuid)

            if not obj:
                self.redirectBasedOnVersionUID(context, uuid, redirect)
                self.redirectBasedOnShortId(context, redirect)
                self.redirectNotFound(redirect, response)
        else:
            self.redirectBasedOnObjectUID(obj, redirect, traverse_subpath)

    def url_with_view(self, obj, url):
        pprops = getToolByName(self.context, 'portal_properties')
        if pprops:
            sprops = pprops.site_properties
            if obj.portal_type in getattr(sprops, 'plone.typesUseViewActionInListings'):
                url += '/view'
        return url

    def redirectBasedOnVersionUID(self, context, uuid, redirect):
        """ Version UID based redirect
        """
        portal = context.restrictedTraverse('plone_portal_state').portal()
        permalink_folder = portal.get('eea_permalink_objects')
        response = context.REQUEST.RESPONSE
        if permalink_folder:
            value = permalink_folder.get(uuid)
            if value:
                uuid = value.versionId
            else:
                data_dict = context.restrictedTraverse('dataVersions')()
                value = data_dict.get(uuid)
                if value:
                    uuid = value
        query = {'getVersionId': uuid,
                 'show_inactive': True,
                 'sort_on': 'effective'}

        resView = context.restrictedTraverse('@@getDataForRedirect')
        res = resView(query)
        if len(res) > 0:
            target_obj = res[-1]
            target = target_obj.getURL()
            target = self.url_with_view(target_obj, target)
            if not redirect:
                # return find url
                return target
            return response.redirect(target, lock=1)

    def redirectBasedOnShortId(self, context, redirect):
        """ Short ID based redirect
        """
        if context.getId() == 'figures':
            ptype = 'EEAFigure'
        elif context.getId() == 'data':
            ptype = 'Data'
        else:
            ptype = None

        if ptype:
            query = {'portal_type': ptype,
                     'show_inactive': True,
                     'getShortId': request.get('id', None)}
            resView = context.restrictedTraverse('@@getDataForRedirect')
            res = resView(query)
            if len(res) > 0:
                target = context.absolute_url() + '/' + res[0].getId
                if not redirect:
                    return target
                return response.redirect(target, lock=1)

    def redirectNotFound(self, redirect, response):
        """ Redirect not found
        """
        if not redirect:
            return None

        return response.notFoundError(
            'The link you followed appears to be broken!')

    def redirectBasedOnObjectUID(self, obj, redirect, traverse_subpath):
        """ Object UID based redirect
        """
        request = self.context.REQUEST
        response = request.RESPONSE

        if traverse_subpath:
            traverse_subpath.insert(0, obj.absolute_url())
            target = '/'.join(traverse_subpath)
        else:
            target = obj.absolute_url()
        if request.QUERY_STRING:
            target += '?' + request.QUERY_STRING
        target = self.url_with_view(obj, target)

        if not redirect:
            return target
        return response.redirect(target, status=301)