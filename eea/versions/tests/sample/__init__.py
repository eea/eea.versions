"""package
"""
from Products.CMFCore import utils
from eea.versions import HAS_ARCHETYPES
from eea.versions.tests.sample import config
from eea.versions.tests.sample import content


def initialize(context):
    """Initializer called when used as a Zope 2 product.
    """
    if HAS_ARCHETYPES:
        from Products.Archetypes import atapi

        atapi.registerType(content.SampleData, config.PROJECTNAME)

        content_types, constructors, _ftis = atapi.process_types(
            atapi.listTypes(config.PROJECTNAME),
            config.PROJECTNAME)

        for atype, constructor in zip(content_types, constructors):
            utils.ContentInit('%s: %s' % (config.PROJECTNAME, atype.portal_type),
                content_types=(atype, ),
                permission=config.DEFAULT_ADD_CONTENT_PERMISSION,
                extra_constructors=(constructor,),
                ).initialize(context)
    else:
        # context.registerClass(
        #     content.SampleData,
        #     permission=config.DEFAULT_ADD_CONTENT_PERMISSION,
        # )
        utils.ContentInit('%s: %s' % (config.PROJECTNAME, content.SampleData.portal_type),
            content_types=(content.SampleData, ),
            permission=config.DEFAULT_ADD_CONTENT_PERMISSION,
            ).initialize(context)