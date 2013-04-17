"""interfaces
"""

from zope.interface import Interface, Attribute
from zope.component.interfaces import IObjectEvent


class IVersionEnhanced(Interface):
    """ Objects which have versions.  
    
    These objects have an annotation with key 'versionId'
    This annotation is a PersistentMapping and has a key 
    'versionId' where it stores a string which is the 
    'versionId' group to which this belongs.

    Any arbitrary object can be made an IVersionEnhanced object, 
    through the @@asignVersion action which alsoProvides that
    interface on the object.
    """


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
        !!not clear
        """

    def oldest():
        """ Return oldest versions
        !!not clear
        """

    def latest_version():
        #!!not clear - what state?
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
