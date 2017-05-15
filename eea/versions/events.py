"""Event handlers
"""
from zope.interface import implements
from zope.annotation import IAnnotations
from zope.component.interfaces import ObjectEvent
from eea.versions.controlpanel.utils import decrement_version_prefix_number
from eea.versions.controlpanel.utils import get_version_prefix
from eea.versions.interfaces import IVersionCreatedEvent

VERSION_ID = 'versionId'


class VersionCreatedEvent(ObjectEvent):
    """An event object triggered when new versions of an object are created"""

    implements(IVersionCreatedEvent)

    def __init__(self, obj, original):
        self.object = obj
        self.original = original


def assign_new_version_id_for_translation(obj, event):
    """Assigns a version id to newly created translations
    """
    version_prefix = get_version_prefix(obj)
    if version_prefix:
        target = event.target
        canonical = obj.getCanonical()
        if canonical is target:
            return
        decrement_version_prefix_number(version_prefix)
        cvid = IAnnotations(canonical).get(VERSION_ID)
        if version_prefix.prefix_with_language:
            cvid = '-'.join(cvid.split('-')[:-1])
        translation_vid = cvid + '-' + target.getLanguage()
        IAnnotations(target)[VERSION_ID] = translation_vid
