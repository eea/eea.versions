""" Vocabularies
"""
from zope.schema.interfaces import IVocabularyFactory
from zope.interface import implements
from zope.schema.vocabulary import SimpleVocabulary
from zope.schema.vocabulary import SimpleTerm
from Products.CMFCore.utils import getToolByName
#
# Object provides
#
class ObjectProvidesVocabulary(object):
    """Vocabulary factory for object provides index.
    """
    implements(IVocabularyFactory)

    def __call__(self, context):
        """ See IVocabularyFactory interface
        """
        ctool = getToolByName(context, 'portal_catalog')
        if not ctool:
            return SimpleVocabulary([])

        provides = ctool.Indexes.get('object_provides', None)
        if not provides:
            return SimpleVocabulary([])

        items = list(provides.uniqueValues())
        items.sort(key=str.lower)
        items = [SimpleTerm(i, i, i) for i in items]
        return SimpleVocabulary(items)
