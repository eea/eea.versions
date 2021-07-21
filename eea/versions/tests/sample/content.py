"""Definition of the Sample Data content type
"""

from Products.ATContentTypes.content import base
from Products.ATContentTypes.content import schemata
from Products.Archetypes import atapi
from eea.versions.tests.sample.interfaces import ISampleData
from eea.versions.interfaces import IVersionEnhanced
from zope.interface import implementer


SampleDataSchema = schemata.ATContentTypeSchema.copy() + atapi.Schema((

    atapi.StringField(
        name='somedata',
        widget=atapi.StringField._properties['widget'](
            label="Some Data",
            label_msgid='versions_label_some_data',
            i18n_domain='eea.versions',
            ),
        schemata="default",
        searchable=True,
        required=True,
        ),

))

SampleDataSchema['relatedItems'].keepReferencesOnCopy = True

schemata.finalizeATCTSchema(SampleDataSchema, moveDiscussion=False)


@implementer(ISampleData, IVersionEnhanced)
class SampleData(base.ATCTBTreeFolder):
    """Description of the Example Type"""

    meta_type = "Sample Data"
    schema = SampleDataSchema
