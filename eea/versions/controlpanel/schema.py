""" Custom zope schema
"""

from zope.interface import implements
from eea.versions.controlpanel.interfaces import IEEAVersionsPortalType
from OFS.Folder import Folder


class PortalType(Folder):
    """ Storage for custom portal types
    """
    implements(IEEAVersionsPortalType)
    meta_type = 'EEA Versions Portal Type'
    _properties = (
        {'id': 'title', 'type': 'string', 'mode': 'w'},
        {'id': 'search_interface', 'type': 'string', 'mode': 'w'},
        {'id': 'search_type', 'type': 'string', 'mode': 'w'},
        {'id': 'show_version_id', 'type': 'boolean', 'mode': 'w'},
        {'id': 'last_assigned_version_number', 'type': 'int', 'mode': 'w'}
    )

    title = ''
    search_interface = ''
    search_type = ''
    show_version_id = True
    last_assigned_version_number = 0

