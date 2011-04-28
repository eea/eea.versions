"""Definition of the Sample Data content type
"""

from Products.ATContentTypes.content import base
from Products.ATContentTypes.content import schemata
from Products.Archetypes import atapi
from eea.versions.tests.sample.interfaces import ISampleData
from zope.interface import implements


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


schemata.finalizeATCTSchema(SampleDataSchema, moveDiscussion=False)


class SampleData(base.ATCTContent):
    """Description of the Example Type"""

    implements(ISampleData)

    meta_type = "Sample Data"
    schema = SampleDataSchema


