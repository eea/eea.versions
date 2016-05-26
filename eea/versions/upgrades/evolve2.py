""" evolve script
"""

import logging

import transaction
from eea.versions.interfaces import IVersionEnhanced, IGetVersions
from eea.versions.versions import VERSION_ID
from eea.versions.utils import _random_id
from zope.annotation.interfaces import IAnnotations

logger = logging.getLogger('eea.versions.migration')


def migrate_versionId_storage(obj):
    """Migrate storage of versionId
    """

    raw_versionId = obj.__annotations__['versionId']['versionId']
    logger.info('versionID: %s', raw_versionId)
    versionId = raw_versionId.strip()

    #doesn't have a good versionId (could be empty string),
    if not versionId and IVersionEnhanced.providedBy(obj):
        obj.__annotations__['versionId'] = _random_id(obj)
    else:
        obj.__annotations__['versionId'] = versionId

    msg = "Migrated versionId storage (old version) for %s (%s)" % \
            (obj.absolute_url(), versionId)

    logger.info(msg)


def evolve(context):
    """ Migrate versionIds for objects that don't have them set
    """
    cat = context.portal_catalog
    brains = cat.searchResults(missing=True, Language="all")

    i = 0
    for brain in brains:
        obj = brain.getObject()
        if not IVersionEnhanced.providedBy(obj):
            continue

        # first, check the brain's versionId
        brain_version = brain.getVersionId
        if isinstance(brain_version, basestring) and brain_version:
            # everything fine
            continue

        if brain.portal_type == "Discussion Item":
            continue    # skipping Discussion Items, they can't be reindexed

        versionId = IGetVersions(obj).versionId
        if isinstance(brain_version, basestring) and not brain_version.strip():
            # an empty string, assigning new versionId
            IAnnotations(obj)[VERSION_ID] = _random_id(obj)
            #obj.reindexObject()
            msg = "Migrated versionId storage (empty string) for %s (%s)" % \
                    (obj.absolute_url(), versionId)
            logger.info(msg)
            if (i % 500) == 0:
                transaction.commit()
            i += 1
            continue

        if isinstance(versionId, basestring) and not versionId.strip():
            # an empty string, assigning new versionId
            IAnnotations(obj)[VERSION_ID] = _random_id(obj)
            #obj.reindexObject()
            msg = "Migrated versionId storage (empty string) for %s (%s)" % \
                    (obj.absolute_url(), versionId)
            logger.info(msg)
            if (i % 500) == 0:
                transaction.commit()
            i += 1
            continue

        if not brain.getVersionId:
            IAnnotations(obj)[VERSION_ID] = _random_id(obj)
            #obj.reindexObject()
            msg = "Migrated versionId storage (empty storage) for %s (%s)" % \
                    (obj.absolute_url(), versionId)
            logger.info(msg)
            if (i % 500) == 0:
                transaction.commit()
            i += 1
            continue

        migrate_versionId_storage(obj)  #this is an old storage:
