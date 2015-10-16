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
    untokenizedFieldnames = [df.name for df in drilldownFields]

    def __init__(self, observable):
        self._observable = observable

    def fieldsFor(self, fieldname, value):
        fieldname = self._rename(fieldname)
        for fieldname, value in self._evaluate(fieldname, value):
            if self._keep(fieldname):
                # print 'fieldname, value', fieldname, value
                # from sys import stdout; stdout.flush()
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
        return fieldname

    def _keep(self, fieldname):
        base, postfix = splitLastSegment(fieldname)
        return fieldname and not fieldname in UNWANTED_FIELDS and not postfix in UNWANTED_POSTFIXES

    def _evaluate(self, fieldname, value):
        if fieldname == 'dcterms:spatial.geos:hasGeometry.geos:asWKT':
            geometry = Geometry.parseWkt(value)
            for (geoLong, geoLat) in geometry.pointCoordinates():
                yield 'dcterms:spatial.geo:long', geoLong
                yield 'dcterms:spatial.geo:lat', geoLat
            return
        if fieldname == 'dcterms:spatial.uri':
            if value.startswith('geo:'):
                geoLat, _, geoLong = value[len('geo:'):].partition(',')
                yield 'dcterms:spatial.geo:long', geoLong
                yield 'dcterms:spatial.geo:lat', geoLat
            return
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
    ('dcterms:spatial.hg:PlaceInTime', 'dcterms:spatial')
]
UNWANTED_FIELDS = [
    #'oa:hasTarget.uri',
    'oa:motivatedBy.uri',
    'dcterms:spatial.vcard:region',
]
UNWANTED_POSTFIXES = set(['uri'])  # Not so sure
EXCLUDED_FROM_ALL = set(['dcterms:spatial.geo:long', 'dcterms:spatial.geo:lat'])
