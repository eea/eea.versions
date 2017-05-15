""" EEA Versions views
"""
import logging

from DateTime.DateTime import DateTime
from Products.CMFCore.WorkflowCore import WorkflowException
from Products.CMFEditions.utilities import maybeSaveVersion
from Products.Five import BrowserView
from Products.CMFCore.utils import getToolByName
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
                    for name, wf_entries in history.items():
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
