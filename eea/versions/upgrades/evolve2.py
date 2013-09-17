from eea.versions.interfaces import IVersionEnhanced, IGetVersions
from eea.versions.versions import _random_id, VERSION_ID
from zope.annotation.interfaces import IAnnotations
from zope.interface import alsoProvides
import logging
import transaction

logger = logging.getLogger('eea.versions.migration')


def migrate_versionId_storage(obj):
    """Migrate storage of versionId
    """

    old_storage = obj.__annotations__.get('versionId')

    versionId = obj.__annotations__['versionId']['versionId'].strip()

    #doesn't have a good versionId (could be empty string),
    if not versionId and IVersionEnhanced.providedBy(obj):
        obj.__annotations__['versionId'] = _random_id(obj)
    else:
        obj.__annotations__['versionId'] = versionId

    msg = "Migrated versionId storage (old version) for %s (%s)" % \
            (obj.absolute_url(), versionId)

    logger.info(msg)


def evolve(context):
    cat = context.portal_catalog
    brains = cat.searchResults(missing=True, Language="all")

    for brain in brains:
        obj = brain.getObject()

        # first, check the brain's versionId
        brain_version = brain.getVersionId
        if isinstance(brain_version, basestring) and brain_version:
            # everything fine
            continue

        if brain_version.portal_type == "Discussion Item":
            continue    # skipping Discussion Items, they can't be reindexed

        if isinstance(brain_version, basestring) and not brain_version.strip():
            # an empty string, assigning new versionId
            IAnnotations(obj)[VERSION_ID] = _random_id(obj)
            obj.reindexObject(idxs=['getVersionId'])
            msg = "Migrated versionId storage (empty string) for %s (%s)" % \
                    (obj.absolute_url(), versionId)
            logger.info(msg)
            transaction.savepoint()
            continue

        versionId = IGetVersions(obj).versionId
        if isinstance(versionId, basestring) and not versionId.strip():
            # an empty string, assigning new versionId
            IAnnotations(obj)[VERSION_ID] = _random_id(obj)
            obj.reindexObject(idxs=['getVersionId'])
            msg = "Migrated versionId storage (empty string) for %s (%s)" % \
                    (obj.absolute_url(), versionId)
            logger.info(msg)
            transaction.savepoint()
            continue

        if not brain.getVersionId:
            IAnnotations(obj)[VERSION_ID] = _random_id(obj)
            obj.reindexObject(idxs=['getVersionId'])
            transaction.savepoint()
            continue

        migrate_versionId_storage(obj)  #this is an old storage:
