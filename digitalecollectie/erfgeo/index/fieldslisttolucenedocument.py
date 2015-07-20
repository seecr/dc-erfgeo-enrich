## begin license ##
#
# "Digitale Collectie ErfGeo Enrichment" is a service that attempts to automatically create
# geographical enrichments for records in "Digitale Collectie" (http://digitalecollectie.nl)
# by querying the ErfGeo search API (https://erfgeo.nl/search).
# "Digitale Collectie ErfGeo Enrichment" is developed for Stichting DEN (http://www.den.nl)
# and the Netherlands Institute for Sound and Vision (http://instituut.beeldengeluid.nl/)
# by Seecr (http://seecr.nl).
# The project is based on the open source project Meresco (http://meresco.org).
#
# Copyright (C) 2015 Netherlands Institute for Sound and Vision http://instituut.beeldengeluid.nl/
# Copyright (C) 2015 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2015 Stichting DEN http://www.den.nl
#
# This file is part of "Digitale Collectie ErfGeo Enrichment"
#
# "Digitale Collectie ErfGeo Enrichment" is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# "Digitale Collectie ErfGeo Enrichment" is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with "Digitale Collectie ErfGeo Enrichment".  If not, see <http://www.gnu.org/licenses/>.
#
## end license ##

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
