""" Browser interfaces
"""
from zope.interface import Interface
from plone.theme.interfaces import IDefaultPloneLayer


class IEEAVersionsPublic(Interface, IDefaultPloneLayer):
    """Versions layer
    """
