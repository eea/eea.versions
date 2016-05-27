""" ControlPanel utils
"""
from Products.CMFCore.utils import getToolByName
from eea.versions.utils import object_provides
from eea.versions.utils import _random_id


def get_version_prefix(obj):
    """
    :param obj: object to check if we have a defined prefix
    :type obj: EEAVersionsPortalType
    :return: Prefix object to be used for versioning
    :rtype: object
    """
    # note that this will find first result as such best to
    # avoid adding the same portal_type for different objects
    version_tool = getToolByName(obj, "portal_eea_versions", None)
    if not version_tool:
        return None
    ptype = obj.portal_type
    definitions = version_tool.objectItems()
    for item in definitions:
        definition = item[1]
        search_type = definition.search_type
        if ptype and ptype == search_type:
            return definition
        search_interface = definition.search_interface
        if search_interface and object_provides(obj, search_interface):
            return definition
    return None


def get_version_prefix_number(obj):
    """
    :param obj: EEAVersionsPortalType
    :type obj: EEAVersionsPortalType
    :return: Last version number used for given EEAVersionsPortalType object
    :rtype: int
    """
    return obj.last_assigned_version_number


def increment_version_prefix_number(obj):
    """
    :param obj: EEAVersionsPortalType
    :type obj: EEAVersionsPortalType
    :return: Incremented last version number used for param type
    :rtype: int
    """
    obj.last_assigned_version_number += 1
    return obj.last_assigned_version_number


def decrement_version_prefix_number(obj):
    """
    :param obj: EEAVersionsPortalType
    :type obj: EEAVersionsPortalType
    :return: Decrement last version number used for param type
    :rtype: int
    """
    obj.last_assigned_version_number -= 1
    return obj.last_assigned_version_number


def new_version_id(obj):
    """
    :param obj: context object
    :type obj: object
    :return: new version id containing either random or incremented prefix value
    :rtype: str
    """
    version_prefix = get_version_prefix(obj)
    if version_prefix:
        pvalue = increment_version_prefix_number(version_prefix)
        ptitle = version_prefix.title
        cvid = '{0}-{1}'.format(ptitle, pvalue)
        if version_prefix.prefix_with_language:
            cvid = cvid + '-' + obj.getLanguage()
        return cvid
    else:
        return _random_id(obj)
