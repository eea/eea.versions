"""Base tests configuration
"""
from Products.Five import fiveconfigure
from Products.Five import zcml
from Testing import ZopeTestCase as ztc


# Import PloneTestCase - this registers more products with Zope as a side effect
from Products.PloneTestCase.PloneTestCase import PloneTestCase
from Products.PloneTestCase.PloneTestCase import FunctionalTestCase
from Products.PloneTestCase.PloneTestCase import setupPloneSite
from Products.PloneTestCase.layer import onsetup

import eea.versions
import eea.versions.tests.sample

import logging
logger = logging.getLogger('eea.version.tests.base')

@onsetup
def setup_test():
    """Set up the additional products required for the Dataservice Content.

    The @onsetup decorator causes the execution of this body to be deferred
    until the setup of the Plone site testing layer.
    """
    # Load the ZCML configuration for the eea.versions package.
    # This includes the other products below as well.

    fiveconfigure.debug_mode = True
    zcml.load_config('configure.zcml', eea.versions)
    zcml.load_config('configure.zcml', eea.versions.tests.sample)
    fiveconfigure.debug_mode = False

    ztc.installPackage('eea.versions')
    ztc.installPackage('eea.versions.tests.sample')

setup_test()

setupPloneSite(
        products=[],
        extension_profiles=('eea.versions:default',
                            'eea.versions.tests.sample:default',
            ))


class VersionsTestCase(PloneTestCase):
    """Base class for integration tests for the 'eea.versions' product.
    """

class VersionsFunctionalTestCase(FunctionalTestCase, VersionsTestCase):
    """Base class for functional integration tests for 'eea.versions' product.
    """
