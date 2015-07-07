from weightless.core import compose, Yield
from meresco.core import Observable

from org.apache.lucene.document import Document
from org.apache.lucene.facet import FacetField


class FieldsListToLuceneDocument(Observable):
    def __init__(self, fieldRegistry, indexFieldFactory, rewriteIdentifier=None, **kwargs):
        Observable.__init__(self, **kwargs)
        self._fieldRegistry = fieldRegistry
        self._indexFieldFactory = indexFieldFactory(self)
        self._rewriteIdentifier = rewriteIdentifier or (lambda i: i)

    def add(self, identifier, fieldslist, **kwargs):
        fieldnamesSeen = set()
        doc = Document()
        for fieldname, value in fieldslist:
            for o in compose(self._indexFieldFactory.fieldsFor(fieldname, value)):
                if callable(o) or o is Yield:
                    yield o
                    continue
                fieldname, value = o
                if self._fieldRegistry.isDrilldownField(fieldname):
                    if not type(value) is list:
                        value = [str(value)]
                    value = [v[:MAX_FACET_STRING_LENGTH] for v in value]
                    doc.add(FacetField(fieldname, value))
                else:
                    field = self._fieldRegistry.createField(fieldname, value, mayReUse=(fieldname not in fieldnamesSeen))
                    doc.add(field)
                    fieldnamesSeen.add(fieldname)
                    if self._indexFieldFactory.isSingleValueField(fieldname):
                        break
        yield self.all.addDocument(identifier=self._rewriteIdentifier(identifier), document=doc)

MAX_FACET_STRING_LENGTH = 256
