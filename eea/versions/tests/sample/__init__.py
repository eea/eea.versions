"""package
"""
from Products.Archetypes import atapi
from Products.CMFCore import utils
from eea.versions.tests.sample import config

def initialize(context):
    """Initializer called when used as a Zope 2 product.
    """
    from eea.versions.tests.sample import content
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
