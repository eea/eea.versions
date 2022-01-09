""" Interfaces
"""
from zope.interface import Interface
from zope import schema
from eea.versions.config import EEAMessageFactory as _


class IEEAVersionsPortalType(Interface):
    """ EEAVersions settings
    """
    title = schema.TextLine(
        title=_('Title'),
        description=_('Prefix title used for construction of version id'),
        required=True
    )

    search_interface = schema.Choice(
        title=_('Provided interface'),
        description=_('Interface to search for'),
        vocabulary="eea.versions.vocabularies.ObjectProvides",
        required=False
    )

    search_type = schema.Choice(
        title=_('Portal type'),
        description=_('Portal type to search for'),
        vocabulary="plone.app.vocabularies.ReallyUserFriendlyTypes",
        required=False
    )

    show_version_id = schema.Bool(
        title=_('Display in document byline'),
        description=_('Boolean if global id is visible in byline'),
        default=True
    )

    prefix_with_language = schema.Bool(
        title=_('Append language prefix to version id'),
        description=_('Boolean if language prefix is added to versionId'),
        default=False
    )

    last_assigned_version_number = schema.Int(
        title=_('Last version number'),
        description=_('Set automatically and incremented when a new version'
                      ' is assigned'),
        default=0,
        required=False
    )


class IEEAVersionsTool(Interface):
    """ IEEAVersionsTool """

class IEEAVersionsCatalog(Interface):
    """ IEEAVersionsCatalog """
