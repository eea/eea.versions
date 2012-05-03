""" Doc tests
"""
from Products.PloneTestCase.PloneTestCase import PloneTestCase
from Testing.ZopeTestCase import FunctionalDocFileSuite as Suite
from eea.versions.tests.base import VersionsFunctionalTestCase
from Zope2.App.zcml import load_config
import doctest
import timeit
import unittest
import random

OPTIONFLAGS = (doctest.REPORT_ONLY_FIRST_FAILURE |
               doctest.ELLIPSIS |
               doctest.NORMALIZE_WHITESPACE)


class OptimizationTest(PloneTestCase):
    """ Optimization test case"""

    def _make_tree(self, container):
        """create a tree of content"""
        make_id = lambda: "o" + str(random.randint(0, 10000000000))

        toplevel = container[container.invokeFactory("Folder", make_id())]
        #print "Created top level"

        #add 5 folders to the top level container
        for iid in (make_id() for i in range(5)):
            branch = toplevel[toplevel.invokeFactory("Folder", iid)]
            #print "Created branch"

            #add another 3 folders inside, each with 5 docs
            for iid in (make_id() for i in range(3)):
                twig = branch[branch.invokeFactory("Folder", iid)]
                #print "Created twig"

                for iid in (make_id() for i in range(5)):
                    leaf = twig[twig.invokeFactory("Sample Data", iid)]
                    #print "Created sample data"
                    form = {
                      'title': 'Dataset'+iid,
                      'description': 'Organisation description',
                      'somedata':'Some Data',
                    }
                    leaf.processForm(values=form, data=1, metadata=1)
                    #print "Edited sample data"

        return toplevel

    def make_versions(self):
        """make a tree and version of it"""
        self.tree.unrestrictedTraverse("@@createVersion")()
        #print "Finished versioning"

    def test_indexing(self):
        """ test"""
        self.loginAsPortalOwner()

        print "Start tree creation"
        self.tree = self._make_tree(self.portal)
        print "Finished created tree"
        
        timer = timeit.Timer(self.make_versions)

        #default indexing
        print "Starting creation of objects with regular indexing"
        self.portal.portal_catalog.manage_catalogClear()
        v1 = timer.repeat(5, number=10)

        #collective.indexing based
        self.portal.portal_catalog.manage_catalogClear()
        import collective.indexing
        load_config('configure.zcml', collective.indexing)
        collective.indexing.initialize(None)
        timer = timeit.Timer(self.make_versions)
        print "Starting creation of objects with collective indexing"
        v2 = timer.repeat(5, number=10)

        print "Without collective.indexing: ", sum(v1)
        print "With collective.indexing: ", sum(v2)

        assert(sum(v1) > sum(v2))


def test_suite():
    """ Suite
    """
    return unittest.TestSuite((
            Suite('docs/versions.txt',
                  optionflags=OPTIONFLAGS,
                  package='eea.versions',
                  test_class=VersionsFunctionalTestCase) ,
              #unittest.makeSuite(OptimizationTest),
              ))
