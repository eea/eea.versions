#from Globals import package_home
from Products.Five import fiveconfigure
from Products.Five import zcml
from Testing import ZopeTestCase as ztc
from zope.app.component.hooks import setSite

# Let Zope know about the two products we require above-and-beyond a basic
# Plone install (PloneTestCase takes care of these).

ztc.installProduct('Five')
ztc.installProduct('FiveSite')

# Import PloneTestCase - this registers more products with Zope as a side effect
from Products.PloneTestCase.PloneTestCase import PloneTestCase
from Products.PloneTestCase.PloneTestCase import FunctionalTestCase
from Products.PloneTestCase.PloneTestCase import setupPloneSite
from Products.PloneTestCase.layer import onsetup
import logging
logger = logging.getLogger('eea.version.tests.base')

@onsetup
def setup_test():
    """Set up the additional products required for the Dataservice Content.

    The @onsetup decorator causes the execution of this body to be deferred
    until the setup of the Plone site testing layer.
    """
    fiveconfigure.debug_mode = True
    import Products.Five
    zcml.load_config('meta.zcml', Products.Five)
    import Products.FiveSite
    zcml.load_config('configure.zcml', Products.FiveSite)
    # Load the ZCML configuration for the eea.versions package.
    # This includes the other products below as well.

    import eea.versions
    zcml.load_config('configure.zcml', eea.versions)
    import eea.versions.tests.sample
    zcml.load_config('configure.zcml', eea.versions.tests.sample)
    fiveconfigure.debug_mode = False

    # We need to tell the testing framework that these products
    # should be available. This can't happen until after we have loaded
    # the ZCML.

    try:
        ztc.installPackage('eea.versions')
        ztc.installPackage('eea.versions.tests.sample')
    except AttributeError, err:
        # Old ZopeTestCase
        logger.info(err)

# The order here is important: We first call the (deferred) function which
# installs the products we need for the Optilux package. Then, we let
# PloneTestCase set up this product on installation.

setup_test()

setupPloneSite(products=[],
        extension_profiles=('eea.versions:default',
            'eea.versions.tests.sample:default',
            ))


class DataserviceTestCase(PloneTestCase):
    """Base class for integration tests for the 'eea.versions' product.
    """

    def _setup(self):
        """ Setup test case
        """
        PloneTestCase._setup(self)
        # Set the local component registry
        setSite(self.portal)

        from Products.Five.pythonproducts import patch_ProductDispatcher__bobo_traverse__
        patch_ProductDispatcher__bobo_traverse__()

        #setup = getattr(self.portal, 'portal_setup', None)
        #profile = 'ThemeCentre:themecentre'
        #if not self.portal._installed_profiles.has_key(profile):
        #    setup.setImportContext('profile-%s' % (profile,))
        #    setup.runImportStep('catalog')
        #    self.portal._installed_profiles[profile] = 1
        #setup.runImportStep('eeacontenttypes_various')


class DataserviceFunctionalTestCase(FunctionalTestCase, DataserviceTestCase):
    """Base class for functional integration tests for the 'eea.versions' product.
    """
