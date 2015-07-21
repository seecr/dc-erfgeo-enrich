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

import re

from meresco.core import Observable

from digitalecollectie.erfgeo.annotationprofiles import ERFGEO_ENRICHMENT_PROFILE
from digitalecollectie.erfgeo.geometry import Point, MultiLineString, MultiPolygon
from digitalecollectie.erfgeo.namespaces import xpath, xpathFirst
from digitalecollectie.erfgeo.utils import first, indexOf


class ErfGeoEnrichmentFromSummary(Observable):
    def annotationFromSummary(self, summary):
        targetUri = xpathFirst(summary, 'oa:Annotation/oa:hasTarget/@rdf:resource')
        annotationUri = ERFGEO_ENRICHMENT_PROFILE.uriFor(targetUri)
        annotation = None
        query, expectedType = self.queryFromSummary(summary)
        annotation = yield self.annotationFromQuery(query, expectedType=expectedType, targetUri=targetUri)
        raise StopIteration((annotationUri, annotation))

    def queryFromSummary(self, summary):
        annotationBody = xpathFirst(summary, 'oa:Annotation/oa:hasBody/*')
        coverageValues = [s.strip() for s in (xpath(annotationBody, 'dc:coverage/text()') + xpath(annotationBody, 'dcterms:spatial/text()'))]
        return self._queryFromCoverageValues(coverageValues)

    def annotationFromQuery(self, query, expectedType=None, targetUri=None):
        pit = None
        if query:
            queryResults = yield self.any.queryErfGeoApi(query, expectedType=expectedType)
            pit = self.selectPit(queryResults, expectedType=expectedType)
        raise StopIteration(self.call.toAnnotation(pit, targetUri, query))

    def selectPit(self, queryResults, expectedType=None):
        pits = None
        for queryResult in queryResults:
            qrType, qrPits = queryResult
            if expectedType is None or qrType == expectedType:
                pits = qrPits
                break
        if pits is None:
            return None
        pits = sorted(
            pits,
            key=lambda pit: (
                indexOf(type(pit.get('geometry')), SHAPE_PRECEDENCE),
                pit.get('hasEnd', '2030-00-00'),
                pit.get('hasBegin', '0000-00-00'),
            ),
            reverse=True)
        pit = first(pits)
        return pit

    def _queryFromCoverageValues(self, coverageValues):
        locationValues, expectedType = self._recognizeLocationKeyValues(coverageValues)
        locationValues, expectedType = self._recognizedParenthesizedParts(locationValues, expectedType)
        query = ', '.join(locationValues)
        query = self._sanitizeQuery(query)
        return query, expectedType

    def _recognizeLocationKeyValues(self, locationValues):
        expectedType = None
        locationProperties = {}
        for locationValue in locationValues:
            for locationProperty in LOCATION_PROPERTIES:
                key = locationProperty['dutchLabel']
                _, keyFound, value = locationValue.partition("%s: " % key)
                if keyFound:
                    locationProperties[key] = value
        if locationProperties:
            sortedLocationProperties = [
                dict(value=locationProperties.get(prop['dutchLabel']), **prop)
                for prop in LOCATION_PROPERTIES
                if locationProperties.get(prop['dutchLabel'])
            ]
            locationValues = [d['value'] for d in sortedLocationProperties]
            expectedType = sortedLocationProperties[0]['expectedType']
        return locationValues, expectedType

    def _recognizedParenthesizedParts(self, locationValues, expectedType):
        for i, locationValue in enumerate(locationValues):
            m = PARENTHESIZED.match(locationValue)
            if not m is None:
                head = m.group(1).strip()
                scope = m.group(2).strip()
                tail = m.group(3).strip()
                if scope in TYPE_MARKERS:
                    if not expectedType:
                        expectedType = TYPE_MARKERS[scope]
                    scope = None
                locationValues[i] = ', '.join(v for v in [head, scope, tail] if v)
        return locationValues, expectedType

    def _sanitizeQuery(self, query):
        return FORBIDDEN_IN_QUERY.sub(' ', query)


LOCATION_PROPERTIES = [
    dict(dutchLabel='straat', expectedType='hg:Street'),
    dict(dutchLabel='dorp', expectedType='hg:Place'),
    dict(dutchLabel='gemeente', expectedType='hg:Municipality'),
    # Note: 'postcode:' also occurs, but currently not useful for matching
]

PARENTHESIZED = re.compile(r"(.+?)\((.+?)\)(.*)")

FORBIDDEN_IN_QUERY = re.compile(r"[^0-9a-zA-Z,\s]+")

TYPE_MARKERS = {
    'stad': 'hg:Place',
    'plaats': 'hg:Place',
    'provincie': 'hg:Province',
    'waterschap': None,
    'eiland': None,
    '?': None
}

SHAPE_PRECEDENCE = [Point, MultiLineString, MultiPolygon]
