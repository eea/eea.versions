""" EEA Versions views
"""
import logging

from Products.CMFEditions.utilities import maybeSaveVersion

from Products.Five import BrowserView
from Products.CMFCore.utils import getToolByName
import transaction


logger = logging.getLogger(__name__)


class UpdateCreationDate(BrowserView):
    """ Update CreationDate if it's smaller than the EffectiveDate
        in which case we set the CreationDate to the value of EffectiveDate
    """

    def __init__(self, context, request):
        super(UpdateCreationDate, self).__init__(context, request)
        self.context = context
        self.request = request

    def __call__(self):
        catalog = getToolByName(self.context, 'portal_catalog')
        res = catalog(show_inactive="True", language="All", sort_on="meta_type")
        count = 0
        objs_urls = []
        import pdb; pdb.set_trace()
        for brain in res:
            if brain.EffectiveDate != "None" and brain.effective < brain.created:
                count += 1
                obj = brain.getObject()
                obj_url = brain.getURL()
                previous_creation_date = obj.created()
                effective_date = obj.effective()
                obj.setCreationDate(effective_date)
                comment = "Fixed creation date > effective date, changed " \
                          "creation date from " \
                          "%s to %s." % (previous_creation_date, effective_date)
                maybeSaveVersion(obj, comment=comment, force=False)
                try:
                    obj.reindexObject(idxs=['created'])
                except Exception:
                    logger.error("%s --> couldn't be reindexed", obj_url)
                    continue
                logger.info('Fixed %s', obj_url)
                objs_urls.append(obj_url)

                if count % 100 == 0:
                    transaction.commit()
        return "FIXED THE FOLLOWING OBJECTS %s" % "\n".join(objs_urls)




