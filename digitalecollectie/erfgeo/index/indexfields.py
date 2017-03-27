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
# "Digitale Collectie ErfGeo Enrichment" is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# "Digitale Collectie ErfGeo Enrichment" is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with "Digitale Collectie ErfGeo Enrichment"; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##

from weightless.core import compose, Yield

from meresco.lucene import DrilldownField, SORTED_PREFIX, UNTOKENIZED_PREFIX

from digitalecollectie.erfgeo.index.constants import ALL_FIELD
from digitalecollectie.erfgeo.index.dateparse import parseYears
from digitalecollectie.erfgeo.geometry import Geometry


class IndexFields(object):
    drilldownFields = [
        DrilldownField(name=UNTOKENIZED_PREFIX + fieldname, hierarchical=False, multiValued=True) for fieldname in [
            # in summary index
            'dc:creator',
            'dc:date',
            'dc:date.year',
            'dc:language',
            'dc:publisher',
            'dc:subject',
            'dc:type',
            'edm:dataProvider',
            'meta:repository',
            'meta:repositoryGroupId',
            'meta:collection',
            'oai:setSpec',
        ]
    ]
    untokenizedFieldnames = [df.name for df in drilldownFields] + [
        'untokenized.id',
    ]

    def __init__(self, observable, _):
        self._observable = observable
        self._fieldnames = set()

    def fieldsFor(self, fieldname, value):
        fields = []
        for o in compose(self._fieldsFor(fieldname, value)):
            if callable(o) or o is Yield:
                yield o
                continue
            f, v = o
            if f.startswith(SORTED_PREFIX) and f in self._fieldnames:
                continue
            fields.append((f, v))
            self._fieldnames.add(f)
        raise StopIteration(fields)
        yield

    def _fieldsFor(self, fieldname, value):
        fieldname = self._rename(fieldname)
        for fieldname, value in compose(self._evaluate(fieldname, value)):
            if self._keep(fieldname):
                yield fieldname, value
                if self._inAll(fieldname):
                    yield ALL_FIELD, value
            yield self._untokenizedField(fieldname, value)

    def isSingleValueField(self, fieldname):
        return fieldname.startswith(SORTED_PREFIX)

    def _rename(self, fieldname):
        for prefix, replacement in PREFIX_RENAMES:
            if fieldname.startswith(prefix):
                fieldname = replacement + fieldname[len(prefix):]
        base, postfix = splitLastSegment(fieldname)
        if postfix in LABEL_TAGS:
            fieldname = base
        for name in FIELDNAMES_AS_POSTFIX:
            if fieldname.endswith('.' + name):
                fieldname = postfix
        return fieldname

    def _keep(self, fieldname):
        base, postfix = splitLastSegment(fieldname)
        return fieldname and not fieldname in UNWANTED_FIELDS and not postfix in UNWANTED_POSTFIXES

    def _evaluate(self, fieldname, value):
        if fieldname in INT_FIELDS:
            try:
                value = int(value)
            except ValueError:
                return
        if fieldname.startswith('dcterms:spatial.'):
            if fieldname.endswith('.geos:asWKT'):
                geometry = Geometry.parseWkt(value)
                for (geoLong, geoLat) in geometry.pointCoordinates():
                    yield 'dcterms:spatial.geo:long', geoLong
                    yield 'dcterms:spatial.geo:lat', geoLat
                return
            if fieldname == 'dcterms:spatial.uri':
                if value.startswith('geo:'):
                    geoLat, _, geoLong = value[len('geo:'):].partition(',')
                    yield 'dcterms:spatial.geo:long', float(geoLong)
                    yield 'dcterms:spatial.geo:lat', float(geoLat)
                return
            if fieldname in {'dcterms:spatial.geo:long', 'dcterms:spatial.geo:lat'}:
                value = float(value)
        if fieldname in ['dc:date', 'dcterms:created']:
            for year in parseYears(value):
                yield 'dc:date.year', str(year)
        yield fieldname, value

    def _inAll(self, fieldname):
        return not fieldname in EXCLUDED_FROM_ALL

    def _untokenizedField(self, fieldname, value):
        name = untokenizedFieldname(fieldname)
        if name in self.untokenizedFieldnames:
            yield name, value


def splitLastSegment(name):
    base, sep, postfix = name.rpartition('.')
    return (base, postfix) if sep else (postfix, '')

def untokenizedFieldname(fieldname):
    return UNTOKENIZED_PREFIX + fieldname


LABEL_TAGS = ['rdfs:label', 'skos:altLabel', 'skos:prefLabel']

# prov:wasDerivedFrom.prov:Entity.prov:wasGeneratedBy.prov:Activity.prov:startedAtTime

PREFIX_RENAMES = [
    ('prov:wasDerivedFrom.prov:Entity.dcterms:identifier', 'meta:recordId'),
    ('prov:wasDerivedFrom.prov:Entity.prov:wasGeneratedBy.prov:Activity', ''),
    ('.', ''),
    ('prov:startedAtTime', ''),
    ('meta:repository.dcterms:identifier', 'meta:repository'),
    ('meta:repository.', ''),
    ('meta:baseurl', ''),
    ('meta:metadataPrefix', ''),
    ('meta:set', ''),
    ('dcterms:spatial.hg:PlaceInTime', 'dcterms:spatial'),
    ('oa:hasTarget.uri', 'id')
]
FIELDNAMES_AS_POSTFIX = ['schema:width', 'schema:height']
UNWANTED_FIELDS = [
    #'oa:hasTarget.uri',
    'oa:motivatedBy.uri',
    'dcterms:spatial.vcard:region',
]
UNWANTED_POSTFIXES = {'uri'}
EXCLUDED_FROM_ALL = {
    'dcterms:spatial.geo:long',
    'dcterms:spatial.geo:lat',
    'schema:width',
    'schema:height'
}
INT_FIELDS = {'schema:width', 'schema:height'}
