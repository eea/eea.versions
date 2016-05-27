""" Custom zope schema
"""

from zope.interface import implements
from OFS.Folder import Folder
from eea.versions.controlpanel.interfaces import IEEAVersionsPortalType


class PortalType(Folder):
    """ Storage for custom portal types
    """
    implements(IEEAVersionsPortalType)
    meta_type = 'EEA Versions Portal Type'
    _properties = (
        {'id': 'title', 'type': 'string', 'mode': 'w'},
        {'id': 'search_interface', 'type': 'string', 'mode': 'w'},
        {'id': 'search_type', 'type': 'string', 'mode': 'w'},
        {'id': 'prefix_with_language', 'type': 'string', 'mode': 'w'},
        {'id': 'show_version_id', 'type': 'boolean', 'mode': 'w'},
        {'id': 'last_assigned_version_number', 'type': 'int', 'mode': 'w'}
    )

    title = ''
    search_interface = ''
    search_type = ''
    show_version_id = True
    prefix_with_language = False
    last_assigned_version_number = 0
