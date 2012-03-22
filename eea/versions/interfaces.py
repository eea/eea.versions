"""interfaces
"""

from zope.interface import Interface, Attribute
from zope.component.interfaces import IObjectEvent


class IVersionEnhanced(Interface):
    """ Objects which have versions.  """


class IVersionControl(Interface):
    """ Objects which have versions.  """

    versionId = Attribute("Version ID")

    def getVersionNumber():
        """ Return version number. """

    def getVersionId():
        """returns version id """

    def setVersionId(numbers):
        """sets version id """


class IGetVersions(Interface):
    """ Get container versions """

    def newest():
        """ Return newer versions
        """

    def oldest():
        """ Return oldest versions
        """

    def latest_version():
        """ Return the object that is the latest version """

    def version_number():
        """ Return the current version number """

    def __call__():
        """ Get all versions
        """

class IVersionCreatedEvent(IObjectEvent):
    """An event triggered after a new version of an object is created"""

    def __init__(obj, original):
        """Constructor

        object is the new, versioned, object
        original is the object that was versioned
        """


class IGetContextInterfaces(Interface):
    """A view that can return information about interfaces for context
    """

    def __call__():
        """ call"""

    def has_any_of(ifaces):
        """ Returns True if any specified interface is provided by context"""


class ICreateVersionView(Interface):
    """ A view that can create a new version
    """

    def __call__():
        """ Calls create() and redirects to new version """

    def create():
        """ This creates a new version """
