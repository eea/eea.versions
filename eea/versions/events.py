"""Event handlers
"""

from eea.versions.interfaces import IVersionCreatedEvent 
from zope.component.interfaces import ObjectEvent
from zope.interface import implements


class VersionCreatedEvent(ObjectEvent):
    """An event object triggered when new versions of an object are created"""

    implements(IVersionCreatedEvent)

    def __init__(self, obj, original):
        self.object = obj
        self.original = original
