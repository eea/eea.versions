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

    def getVersionId(self):
        """returns version id """

    def setVersionId(self, value):
        """sets version id """

    def can_create_new_version(self):
        """ Returns True if new versions are allowed """


class IGetVersions(Interface):
    """ Get container versions """

    versionId = Attribute(u"""The version ID string of the context""")

    def versions(self):
        """Returns all objects that are in the version group

        The objects are sorted based on their effective date,
        falling back on creation date if object is not published.

        Anonymous users will only get published objects.
        """

    def enumerate_versions(self):
        """Returns a mapping of version_number:object

        Number 1 is the oldest object.
        """

    def version_number(self):
        """Returns the number of the version.

        First version gets number 1, and so on.
        """

    def later_versions(self):
        """Returns a list of objects that are created/published
        later then the current object.
        """

    def earlier_versions(self):
        """Returns a list of objects that are created/published
        earlier then the current object.
        """

    def latest_version(self):
        """Returns the last created (or published) object in this version
        group
        """

    def first_version(self):
        """Returns the oldest created/published object in this version group
        """

    def isLatest(self):
        """Returns True if current object is the last object in version group,
        otherwise returns False
        """

    def getLatestVersionUrl(self):
        """Returns the absolute url of the last object in version group
        """

    def __call__(self):
        """ Same as enumerate_versions()
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
