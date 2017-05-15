"""Debug views and upgrade utilities
"""

from StringIO import StringIO
from BTrees.IIBTree import IISet, difference
from Products.Five import BrowserView
from Products.ZCatalog.Lazy import LazyMap
from eea.versions.interfaces import IVersionEnhanced
from eea.versions.versions import VERSION_ID
from zope.annotation.interfaces import IAnnotations
from zope.interface import alsoProvides


class GetMissingValuesForIndex(BrowserView):
    """We use this to see if there are any objects that have
    an assigned versionId but don't have that value stored in the
    catalog. This was due to the way the code worked up to
    v4.7: whenever a versionId was checked on an object, one
    was assigned, but a catalog reindex was not performed.

    Code based on http://stackoverflow.com/questions/11216472/
    how-can-i-look-for-objects-with-missing-value-or-none-as-key
    """

    def missing_entries_for_index(self, catalog, index_name):
        """ Return the difference between catalog and index ids
        """
        index = catalog._catalog.getIndex(index_name)
        referenced = IISet(index.referencedObjects())
        return (
            difference(IISet(catalog._catalog.paths), referenced),
            len(catalog) - len(referenced)
        )

    def not_indexed_results(self, catalog, index_name):
        """ call this for not indexed results
        """
        rs, length = self.missing_entries_for_index(catalog, index_name)
        return LazyMap(catalog._catalog.__getitem__, rs.keys(), length)

    def get_real_versionid(self, brain):
        """get version id recorded in annotation
        """
        try:
            obj = brain.getObject()
        except AttributeError:  #some objects have entries in the catalog
                                #but they have been deleted from ZMI
                                #so the catalog is out of date
            return False
        annot = IAnnotations(obj)
        versionid = annot.get(VERSION_ID, "")

        if hasattr(versionid, 'keys'):
            return bool(versionid.get('versionId'))
        elif versionid:
            return bool(versionid.strip())

    def __call__(self):
        catalog = self.context.portal_catalog
        index = self.request.form.get('index')
        portal_type = self.request.form.get('portal_type')
        fix = self.request.form.get("fix")

        results = self.not_indexed_results(catalog, index)

        out = StringIO()
        results = [z for z in results if
                (z.portal_type == portal_type) and self.get_real_versionid(z)]

        print >> out, "Got %s results" % len(results)
        for brain in results:
            print >> out, brain.portal_type, brain.getURL()
            if fix:
                obj = brain.getObject()
                if not IVersionEnhanced.providedBy(obj):
                    alsoProvides(obj, IVersionEnhanced)
                obj.reindexObject()

        if fix:
            print >> out, "Fixed, try calling again this page "\
                          "to see if different"

        out.seek(0)

        return out.read()
