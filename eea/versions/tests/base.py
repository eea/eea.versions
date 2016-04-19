"""Base tests configuration
"""

from  plone.app.testing import FunctionalTesting
from  plone.app.testing import IntegrationTesting
from  plone.app.testing import PLONE_FIXTURE
from  plone.app.testing import PloneSandboxLayer
from  plone.app.testing import applyProfile
from plone.app.testing import TEST_USER_ID
from plone.app.testing import setRoles
from plone.testing import z2
from zope.configuration import xmlconfig
import eea.versions
import eea.versions.tests.sample


class EEAFixture(PloneSandboxLayer):
    """ Custom fixture
    """
    defaultBases = (PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        """ Setup Zope
        """

        xmlconfig.file('configure.zcml',
                       eea.versions,
                       context=configurationContext
                       )
        xmlconfig.file('configure.zcml',
                       eea.versions.tests.sample,
                       context=configurationContext
                       )

        z2.installProduct(app, 'eea.versions.tests.sample')

    def setUpPloneSite(self, portal):
        """ Setup Plone
        """
        applyProfile(portal, 'eea.versions:default')
        applyProfile(portal, 'eea.versions.tests.sample:default')
        setRoles(portal, TEST_USER_ID, ['Member', 'Manager'])

EEAFIXTURE = EEAFixture()
FUNCTIONAL_TESTING = FunctionalTesting(bases=(EEAFIXTURE,),
                                       name='eea.versions:Functional')

INTEGRATIONAL_TESTING = IntegrationTesting(bases=(EEAFIXTURE,),
                                           name='eea.versions:Integrational')
