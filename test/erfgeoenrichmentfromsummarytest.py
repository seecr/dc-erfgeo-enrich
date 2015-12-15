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

from lxml.etree import XML

from seecr.test import SeecrTestCase, CallTrace

from weightless.core import be, retval
from meresco.core import Observable

from digitalecollectie.erfgeo.geometry import MultiLineString
from digitalecollectie.erfgeo.namespaces import xpathFirst, createSubElement
from digitalecollectie.erfgeo.annotationprofiles import ERFGEO_ENRICHMENT_PROFILE
from digitalecollectie.erfgeo.erfgeoenrichmentfromsummary import ErfGeoEnrichmentFromSummary
from digitalecollectie.erfgeo.pittoannotation import PitToAnnotation


class ErfGeoEnrichmentFromSummaryTest(SeecrTestCase):
    def testQueryFromSummary(self):
        egefs = ErfGeoEnrichmentFromSummary()
        query, expectedType = egefs.queryFromSummary(summary=makeSummary(['Turbinestraat 9', 'Veenendaal']))
        self.assertEquals('"Turbinestraat 9", "Veenendaal"', query)
        self.assertEquals(None, expectedType)

    def testQueryFromSummaryStraatDorpGemeente(self):
        egefs = ErfGeoEnrichmentFromSummary()
        query, expectedType = egefs.queryFromSummary(summary=makeSummary(['straat: Leunseweg', 'dorp: Leunen', 'gemeente: Venray']))
        self.assertEquals('"Leunseweg", "Leunen", "Venray"', query)
        self.assertEquals('hg:Street', expectedType)
        query, expectedType = egefs.queryFromSummary(summary=makeSummary(['gemeente: Venray', 'straat: Leunseweg', 'dorp: Leunen']))
        self.assertEquals('"Leunseweg", "Leunen", "Venray"', query)
        self.assertEquals('hg:Street', expectedType)

    def testQueryFromSummaryDorpGemeente(self):
        egefs = ErfGeoEnrichmentFromSummary()
        query, expectedType = egefs.queryFromSummary(summary=makeSummary(['gemeente: Venray', 'dorp: Leunen', ]))
        self.assertEquals('"Leunen", "Venray"', query)
        self.assertEquals('hg:Place', expectedType)

    def testQueryFromSummaryWithParenthesizedLiesIn(self):
        egefs = ErfGeoEnrichmentFromSummary()
        query, expectedType = egefs.queryFromSummary(summary=makeSummary(['Serooskerke (Walcheren)']))
        self.assertEquals('"Serooskerke", "Walcheren"', query)
        self.assertEquals(None, expectedType)

    def testQueryFromSummaryWithParenthesizedType(self):
        egefs = ErfGeoEnrichmentFromSummary()
        query, expectedType = egefs.queryFromSummary(summary=makeSummary(['Groningen (stad)']))
        self.assertEquals('"Groningen"', query)
        self.assertEquals('hg:Place', expectedType)

        query, expectedType = egefs.queryFromSummary(summary=makeSummary(['Groningen (provincie)']))
        self.assertEquals('"Groningen"', query)
        self.assertEquals('hg:Province', expectedType)

    def testQueryFromSummaryWithMoreThenOneParenthesizedType(self):
        egefs = ErfGeoEnrichmentFromSummary()
        query, expectedType = egefs.queryFromSummary(summary=makeSummary(['Groningen (stad)', 'Groningen (provincie)']))
        self.assertEquals('"Groningen", "Groningen"', query)
        self.assertEquals('hg:Place', expectedType)

        query, expectedType = egefs.queryFromSummary(summary=makeSummary(['Groningen (provincie)', 'Groningen (stad)']))
        self.assertEquals('"Groningen", "Groningen"', query)
        self.assertEquals('hg:Place', expectedType)

    def testQueryFromSummaryWithParenthesizedQuestionMarkIgnored(self):
        egefs = ErfGeoEnrichmentFromSummary()
        query, expectedType = egefs.queryFromSummary(summary=makeSummary(['Utrecht (?)']))
        self.assertEquals('"Utrecht"', query)
        self.assertEquals(None, expectedType)

    def testQueryFromSummarySanitized(self):
        egefs = ErfGeoEnrichmentFromSummary()
        query, expectedType = egefs.queryFromSummary(summary=makeSummary(['Abc (def "ghi']))
        self.assertEquals('"Abc  def  ghi"', query)
        self.assertEquals(None, expectedType)

    def testApostrophAndDashKeptInQuery(self):
        egefs = ErfGeoEnrichmentFromSummary()
        query, expectedType = egefs.queryFromSummary(summary=makeSummary(["'s-Gravenhage"]))
        self.assertEquals("\"'s-Gravenhage\"", query)
        self.assertEquals(None, expectedType)

    def testTremaKeptInQuery(self):
        egefs = ErfGeoEnrichmentFromSummary()
        query, expectedType = egefs.queryFromSummary(summary=makeSummary(["Groot-Brittanië"]))
        self.assertEquals('"Groot-Brittanië"', query)
        self.assertEquals(None, expectedType)

    def testJustNederlandNotQueried(self):
        egefs = ErfGeoEnrichmentFromSummary()
        query, expectedType = egefs.queryFromSummary(summary=makeSummary(["Nederland"]))
        self.assertEquals(None, query)
        self.assertEquals(None, expectedType)

        egefs = ErfGeoEnrichmentFromSummary()
        query, expectedType = egefs.queryFromSummary(summary=makeSummary(["Veenendaal", "Nederland"]))
        self.assertEquals('"Veenendaal", "Nederland"', query)
        self.assertEquals(None, expectedType)

    def testSelectPit(self):
        egefs = ErfGeoEnrichmentFromSummary()
        pit = egefs.selectPit(QUERY_RESULTS, expectedType=None)
        self.assertEquals('other:id', pit['@id'])

        pit = egefs.selectPit(QUERY_RESULTS, expectedType='hg:Street')
        self.assertEquals('nwb/venray-leunseweg', pit['@id'])

    def testAnnotationFromSummary(self):
        queries = []
        def queryErfGeoApi(query, expectedType=None, exact=None):
            queries.append(dict(query=query, expectedType=expectedType, exact=exact))
            raise StopIteration(QUERY_RESULTS)
            yield

        def toAnnotation(pit, targetUri, query, **kwargs):
            return PitToAnnotation().toAnnotation(pit=pit, targetUri=targetUri, query=query)

        observer = CallTrace('observer', methods={'queryErfGeoApi': queryErfGeoApi, 'toAnnotation': toAnnotation})
        top = be(
            (Observable(),
                (ErfGeoEnrichmentFromSummary(),
                    (observer,)
                )
            )
        )
        summary = makeSummary(['straat: Leunseweg', 'dorp: Leunen', 'gemeente: Venray'])
        result = retval(top.any.annotationFromSummary(summary))
        self.assertEquals([dict(query='"Leunseweg", "Leunen", "Venray"', expectedType='hg:Street', exact=True)], queries)
        annotationUri, annotation = result
        self.assertEquals(ERFGEO_ENRICHMENT_PROFILE.uriFor('uri:target'), annotationUri)
        self.assertEquals('nwb/venray-leunseweg', xpathFirst(annotation, '/rdf:RDF/oa:Annotation/oa:hasBody/rdf:Description/dcterms:spatial/hg:PlaceInTime/@rdf:about'))

    def testNoQueryInCaseOfGeoLatLong(self):
        queries = []
        def queryErfGeoApi(query, expectedType=None):
            queries.append(dict(query=query, expectedType=expectedType))
            raise StopIteration(QUERY_RESULTS)
            yield

        def toAnnotation(pit, targetUri, query, geoCoordinates=None):
            return PitToAnnotation().toAnnotation(pit=pit, targetUri=targetUri, query=query, geoCoordinates=geoCoordinates)

        observer = CallTrace('observer', methods={'queryErfGeoApi': queryErfGeoApi, 'toAnnotation': toAnnotation})
        top = be(
            (Observable(),
                (ErfGeoEnrichmentFromSummary(),
                    (observer,)
                )
            )
        )

        summary = makeSummary([], geoLatLong=('51.8', '5.0'))
        result = retval(top.any.annotationFromSummary(summary))
        self.assertEquals([], queries)
        annotationUri, annotation = result
        self.assertEquals(ERFGEO_ENRICHMENT_PROFILE.uriFor('uri:target'), annotationUri)
        self.assertEquals('51.8', xpathFirst(annotation, '/rdf:RDF/oa:Annotation/oa:hasBody/rdf:Description/geo:lat/text()'))



QUERY_RESULTS = [
    ('hg:Place', [
        {'@id': 'some:id', 'type': 'hg:Place', 'name': "a place"},
        {'@id': 'other:id', 'hasBegin': '2010-01-01', 'type': 'hg:Place', 'name': "a place"},
        {'@id': 'different:id', 'type': 'hg:Place', 'name': "a place"}
    ]),
    ('hg:Street', [
        {'@id': 'bag/984300000000320', 'type': 'hg:Street', 'name': "Leunseweg"},
        {'@id': 'nwb/venray-leunseweg', 'type': 'hg:Street', 'name': "Leunseweg", 'geometry': MultiLineString([[[5.976364581846588,51.52243586973127],[5.977570822531698,51.521009542433255],[5.977641926636947,51.520937272278]],[[5.977641926636947,51.520937272278],[5.9779252893052455,51.52056729706881],[5.978463420127178,51.519845466966835]],[[5.978810297575312,51.51930414638479],[5.978780974683683,51.519300636494314],[5.978753517554276,51.51929103170512],[5.978725963940384,51.519272905985616],[5.978708102058019,51.51925108169847],[5.9786942063007675,51.51923287779468],[5.978688040122361,51.51920855828437],[5.9786858271487935,51.51918908170666],[5.97869714389736,51.519158579206554]],[[5.978463420127178,51.519845466966835],[5.978689959483037,51.51953869936622],[5.97876059153952,51.5194304755717],[5.978810297575312,51.51930414638479]],[[5.978942199072787,51.51912122045602],[5.97897402190174,51.519135261536135],[5.979001702402638,51.51916313044837],[5.979015786946229,51.51919471773031],[5.979020071895229,51.519223927694654],[5.979014461839677,51.51924343492792]],[[5.978942199072787,51.51912122045602],[5.979226543949531,51.518700018617565],[5.979439134138488,51.51842927555684],[5.979760764946663,51.517681570604],[5.979788757821533,51.517618506703975]]])}
    ]),
]

def makeSummary(dcCoverageValues, geoLatLong=None):
    summary = XML("""<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:oa="http://www.w3.org/ns/oa#" xmlns:dc="http://purl.org/dc/elements/1.1/">
    <oa:Annotation>
        <oa:hasTarget rdf:resource="uri:target"/>
        <oa:hasBody>
            <rdf:Description>
            </rdf:Description>
        </oa:hasBody>
    </oa:Annotation>
</rdf:RDF>""")
    bodyElement = xpathFirst(summary, '//oa:hasBody/rdf:Description')
    for value in dcCoverageValues:
        createSubElement(bodyElement, 'dc:coverage', text=value)
    if not geoLatLong is None:
        geoLat, geoLong = geoLatLong
        createSubElement(bodyElement, 'geo:lat', text=geoLat)
        createSubElement(bodyElement, 'geo:long', text=geoLong)
    return summary

