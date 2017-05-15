""" Doc tests
"""

import doctest
import unittest
from eea.versions.tests.base import FUNCTIONAL_TESTING
from plone.testing import layered

OPTIONFLAGS = (doctest.REPORT_ONLY_FIRST_FAILURE |
               doctest.ELLIPSIS |
               doctest.NORMALIZE_WHITESPACE)


def test_suite():
    """ Suite
    """
    suite = unittest.TestSuite()
    suite.addTests([
        layered(
            doctest.DocFileSuite(
                'docs/versions.txt',
                optionflags=OPTIONFLAGS,
                package='eea.versions'),
            layer=FUNCTIONAL_TESTING),
    ])
    return suite
