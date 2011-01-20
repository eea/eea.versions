from zope.interface import Interface, Attribute
from zope.app.event.interfaces import IObjectEvent


class IVersionEnhanced(Interface):
    """ Objects which have versions.  """


class IVersionControl(Interface):
    """ Objects which have versions.  """

    versionId = Attribute("Version ID")

    def getVersionNumber():
        """ Return version number. """

    def getVersionId():
        """ """

    def setVersionId(numbers):
        """ """


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

    def __init__(object, original):
        """Constructor

        object is the new, versioned, object
        original is the object that was versioned
        """
