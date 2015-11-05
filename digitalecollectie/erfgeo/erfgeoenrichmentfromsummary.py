# -*- coding: utf-8 -*-
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
        geoCoordinates = self._geoCoordinatesPresent(summary)
        query, expectedType = self.queryFromSummary(summary) if geoCoordinates is None else (None, None)
        annotation = yield self.annotationFromQuery(query, expectedType=expectedType, targetUri=targetUri, geoCoordinates=geoCoordinates)
        raise StopIteration((annotationUri, annotation))

    def queryFromSummary(self, summary):
        annotationBody = xpathFirst(summary, 'oa:Annotation/oa:hasBody/*')
        spatialValues = [s.strip() for s in xpath(annotationBody, 'dcterms:spatial[@xml:lang="nl"]/text()') if s.strip()]
        if len(spatialValues) == 0:
            spatialValues = [s.strip() for s in xpath(annotationBody, 'dcterms:spatial/text()') if s.strip()]
        for uri in xpath(annotationBody, 'dcterms:spatial/@rdf:resource'):
            for value in xpath(summary, '*[@rdf:about="%s"]/skos:prefLabel/text()' % uri):
                value = value.strip()
                if value and not value in spatialValues:
                    spatialValues.append(value)
        if spatialValues:
            coverageValues = spatialValues  # prefer the more specific relation; helps to ignore uses of dc:coverage for time related values
        else:
            coverageValues = [s.strip() for s in xpath(annotationBody, 'dc:coverage[@xml:lang="nl"]/text()') if s.strip()]
            if len(coverageValues) == 0:
                coverageValues = [s.strip() for s in xpath(annotationBody, 'dc:coverage/text()') if s.strip()]
        return self._queryFromCoverageValues(coverageValues)

    def annotationFromQuery(self, query, expectedType=None, targetUri=None, geoCoordinates=None):
        pit = None
        if query:
            queryResults = yield self.any.queryErfGeoApi(query=query, expectedType=expectedType)
            pit = self.selectPit(queryResults, expectedType=expectedType)
        raise StopIteration(self.call.toAnnotation(pit, targetUri, query, geoCoordinates=geoCoordinates))

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

    def _geoCoordinatesPresent(self, summary):
        annotationBody = xpathFirst(summary, 'oa:Annotation/oa:hasBody/*')
        nodes = [annotationBody]
        for uri in xpath(annotationBody, 'dcterms:spatial/@rdf:resource'):
            node = xpathFirst(summary, '*[@rdf:about="%s"]')
            if not node is None:
                nodes.append(node)
        for node in xpath(annotationBody, 'dcterms:spatial/rdf:Description'):
            nodes.append(node)
        for node in nodes:
            geoLat = xpathFirst(node, 'geo:lat/text()')
            geoLong = xpathFirst(node, 'geo:long/text()')
            if geoLat and geoLong:
                return (geoLat, geoLong)
        return None

    def _queryFromCoverageValues(self, coverageValues):
        locationValues, expectedType = self._recognizeLocationKeyValues(coverageValues)
        locationValues, expectedType = self._recognizedParenthesizedParts(locationValues, expectedType)
        query = ', '.join(locationValues)
        query = self._sanitizeQuery(query)
        if query.lower() == 'nederland' and expectedType is None:
            query = None
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
                    type = TYPE_MARKERS[scope]
                    if not expectedType or indexOf(expectedType, TYPE_PRECEDENCE) > indexOf(type, TYPE_PRECEDENCE):
                        expectedType = type
                    scope = None
                locationValues[i] = ', '.join(v for v in [head, scope, tail] if v)
        return locationValues, expectedType

    def _sanitizeQuery(self, query):
        return FORBIDDEN_IN_QUERY.sub(' ', query)



PARENTHESIZED = re.compile(r"(.+?)\((.+?)\)(.*)")

FORBIDDEN_IN_QUERY = re.compile(r"[^0-9\w,'\-\s]+", re.UNICODE)

LOCATION_PROPERTIES = [
    dict(dutchLabel='straat', expectedType='hg:Street'),
    dict(dutchLabel='dorp', expectedType='hg:Place'),
    dict(dutchLabel='stad', expectedType='hg:Place'),
    dict(dutchLabel='plaats', expectedType='hg:Place'),
    dict(dutchLabel='water', expectedType='hg:Water'),
    dict(dutchLabel='gemeente', expectedType='hg:Municipality'),
    dict(dutchLabel='regio', expectedType='hg:Region'),
    dict(dutchLabel='provincie', expectedType='hg:Province'),
    dict(dutchLabel='land', expectedType='hg:Country'),
    # Note: 'postcode:' also occurs, but currently not useful for matching
]

TYPE_MARKERS = dict((d['dutchLabel'], d['expectedType']) for d in LOCATION_PROPERTIES)
TYPE_MARKERS.update({
    '?': None,
    'eiland': None,
    'waterschap': None,
})

TYPE_PRECEDENCE = ['hg:Street', 'hg:Place', 'hg:Water', 'hg:Municipality', 'hg:Region', 'hg:Province', 'hg:Country']
SHAPE_PRECEDENCE = [Point, MultiLineString, MultiPolygon]
