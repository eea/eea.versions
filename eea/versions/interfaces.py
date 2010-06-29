from zope.interface import Interface, Attribute


class IVersionEnhanced(Interface):
    """ Objects which have versions.  """


class IVersionControl(Interface):
    """ Objects which have versions.  """

    versionId = Attribute("Version ID")

    def getVersionNumber():
        """ Return version number. """


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
