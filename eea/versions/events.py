from eea.versions.interfaces import IVersionCreatedEvent 
from zope.app.event.objectevent import ObjectEvent
from zope.interface import implements


class VersionCreatedEvent(ObjectEvent):
    """An event object triggered when new versions of an object are being created"""

    implements(IVersionCreatedEvent)

    def __init__(self, object, original):
        self.object = object
        self.original = original
