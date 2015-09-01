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
# Copyright (C) 2011-2012, 2014-2015 Netherlands Institute for Sound and Vision http://instituut.beeldengeluid.nl/
# Copyright (C) 2011-2012, 2014-2015 Seecr (Seek You Too B.V.) http://seecr.nl
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

from lxml.etree import XML

from seecr.test.utils import getRequest
from seecr.test.integrationtestcase import IntegrationTestCase

from meresco.components import lxmltostring

from digitalecollectie.erfgeo.namespaces import xpathFirst, xpath
from simplejson import loads
from decimal import Decimal
from urllib import urlencode


class ErfGeoTest(IntegrationTestCase):
    def testOaiIdentify(self):
        header, body = getRequest(self.erfGeoEnrichmentPort, '/oai', {'verb': 'Identify'})
        self.assertEquals("Digitale Collectie ErfGeo enrichments", xpathFirst(body, '/oai:OAI-PMH/oai:Identify/oai:repositoryName/text()'))

    def testOaiListRecords(self):
        header, body = getRequest(self.erfGeoEnrichmentPort, '/oai', {'verb': 'ListRecords', 'metadataPrefix': 'erfGeoEnrichment'}, parse=False)
        bodyLxml = XML(body)
        self.assertEquals(4, len(xpath(bodyLxml, '/oai:OAI-PMH/oai:ListRecords/oai:record')))
        d = dict(zip(
            xpath(bodyLxml, '/oai:OAI-PMH/oai:ListRecords/oai:record/oai:metadata/rdf:RDF/oa:Annotation/oa:hasTarget/@rdf:resource'),
            xpath(bodyLxml, '/oai:OAI-PMH/oai:ListRecords/oai:record/oai:metadata/rdf:RDF/oa:Annotation')))
        self.assertEquals(set(['NIOD_BBWO2:niod:3366459', 'geluidVanNl:geluid_van_nederland:47954146', 'NIOD_BBWO2:niod:3441263', 'limburgs_erfgoed:oai:le:RooyNet:37']), set(d.keys()))

        # contains no location information to even construct a ErfGeo search API query from
        annotation = d['NIOD_BBWO2:niod:3441263']
        self.assertEquals(None, xpathFirst(annotation, 'oa:hasBody'))
        self.assertEquals('No ErfGeo search API query could be constructed from target record', xpathFirst(annotation, 'dcterms:description/text()'))
        self.assertEquals(None, xpathFirst(annotation, 'dcterms:source/@rdf:resource'))

        annotation = d['NIOD_BBWO2:niod:3366459']
        self.assertEquals('http://data.digitalecollectie.nl/annotation/erfGeoEnrichment#TklPRF9CQldPMjpuaW9kOjMzNjY0NTk=', xpathFirst(annotation, '@rdf:about'))
        self.assertEquals('http://localhost:%s?q=Verenigde+Staten' % self.erfGeoApiPort, xpathFirst(annotation, 'dcterms:source/@rdf:resource'))
        self.assertEquals('NIOD_BBWO2:niod:3366459', xpathFirst(annotation, 'oa:hasTarget/@rdf:resource'))
        annotationBody = xpathFirst(annotation, 'oa:hasBody/rdf:Description')
        placeInTime = xpathFirst(annotationBody, 'dcterms:spatial/hg:PlaceInTime')
        self.assertEquals('http://erfgeo.nl/hg/geonames/2747032', xpathFirst(placeInTime, '@rdf:about'))
        self.assertEquals('Soestdijk', xpathFirst(placeInTime, 'rdfs:label/text()'))
        geometryWKT = xpathFirst(placeInTime, 'geos:hasGeometry/rdf:Description/geos:asWKT/text()')
        self.assertEquals('POINT(5.28472 52.19083)', geometryWKT)

    def testOaiSets(self):
        header, body = getRequest(self.erfGeoEnrichmentPort, '/oai', {'verb': 'GetRecord', 'identifier': 'http://data.digitalecollectie.nl/annotation/erfGeoEnrichment#TklPRF9CQldPMjpuaW9kOjMzNjY0NTk=', 'metadataPrefix': 'erfGeoEnrichment'})
        self.assertEquals(set(['NIOD']), set(xpath(body, '//oai:setSpec/text()')))

        header, body = getRequest(self.erfGeoEnrichmentPort, '/oai', {'verb': 'ListSets'})
        self.assertEquals(set(['NIOD', 'limburgs_erfgoed', 'geluidVanNl']), set(xpath(body, '//oai:setSpec/text()')))

    def testAbout(self):
        header, body = getRequest(self.erfGeoEnrichmentPort, '/about', {'uri': 'NIOD_BBWO2:niod:3366459', 'profile': 'erfGeoEnrichment'})
        rdf = xpathFirst(body, '/rdf:RDF')
        self.assertEquals('http://data.digitalecollectie.nl/annotation/erfGeoEnrichment#TklPRF9CQldPMjpuaW9kOjMzNjY0NTk=', xpathFirst(rdf, 'oa:Annotation/@rdf:about'))
        self.assertEquals('NIOD_BBWO2:niod:3366459', xpathFirst(rdf, 'oa:Annotation/oa:hasTarget/@rdf:resource'))
        annotationBody = xpathFirst(rdf, 'oa:Annotation/oa:hasBody/rdf:Description')
        placeInTime = xpathFirst(annotationBody, 'dcterms:spatial/hg:PlaceInTime')
        self.assertEquals('http://erfgeo.nl/hg/geonames/2747032', xpathFirst(placeInTime, '@rdf:about'))
        self.assertEquals('Soestdijk', xpathFirst(placeInTime, 'rdfs:label/text()'))
        geometryWKT = xpathFirst(placeInTime, 'geos:hasGeometry/rdf:Description/geos:asWKT/text()')
        self.assertEquals('POINT(5.28472 52.19083)', geometryWKT)

    def testMinimalWebPresence(self):
        body = self.getPage('/index')
        self.assertTrue('<h1>ErfGeo Verrijkingen</h1>' in body, body)

    def testSruNumberOfHits(self):
        self.assertSruQuery(4, '*')
        self.assertSruQuery(1, 'dc:subject=Zeeoorlog')
        self.assertSruQuery(2, 'meta:repositoryGroupId exact "NIOD"')
        self.assertSruQuery(1, 'dcterms:spatial=Soestdijk')
        self.assertSruQuery(1, 'dcterms:spatial=Leunseweg')

    def testSruGeoRangesHits(self):
        self.assertSruQuery(set(['geluidVanNl:geluid_van_nederland:47954146']), 'dcterms:spatial.geo:long<5')
        self.assertSruQuery(set(['geluidVanNl:geluid_van_nederland:47954146', 'NIOD_BBWO2:niod:3366459', 'limburgs_erfgoed:oai:le:RooyNet:37']), 'dcterms:spatial.geo:long>4')
        self.assertSruQuery(set(['geluidVanNl:geluid_van_nederland:47954146', 'NIOD_BBWO2:niod:3366459']), 'dcterms:spatial.geo:long>4 AND dcterms:spatial.geo:long<6 AND dcterms:spatial.geo:lat>52 AND dcterms:spatial.geo:lat<53')
        self.assertSruQuery(set([]), 'dcterms:spatial.geo:long>4 AND dcterms:spatial.geo:long<6 AND dcterms:spatial.geo:lat>53 AND dcterms:spatial.geo:lat<54')

        self.assertSruQuery(set(['limburgs_erfgoed:oai:le:RooyNet:37']), 'dcterms:spatial.geo:long>5.97 AND dcterms:spatial.geo:long<5.98 AND dcterms:spatial.geo:lat>51.51 AND dcterms:spatial.geo:lat<51.52')  # Leunseweg, Leunen, Venray

    def testSruRecordData(self):
        responseLxml = self._doQuery('dc:subject=Zeeoorlog')
        rdfXml = xpathFirst(responseLxml, '/srw:searchRetrieveResponse/srw:records/srw:record/srw:recordData/rdf:RDF')
        self.assertEquals(2, len(rdfXml.getchildren()))
        self.assertEquals('Verenigde Staten', xpathFirst(rdfXml, 'oa:Annotation/oa:hasBody/rdf:Description/dc:coverage/text()'))
        self.assertEquals(1, len(xpath(rdfXml, 'oa:Annotation/oa:hasBody/rdf:Description/dcterms:spatial/hg:PlaceInTime')))

    def testSearchApi(self):
        body = self.getPage('/search?query=Zeeoorlog')
        d = loads(body, parse_float=Decimal)
        self.assertEquals(1, d['result']['total'])
        spatial = d['result']['items'][0]['dcterms:spatial'][0]
        self.assertEquals(['Soestdijk'], spatial['rdfs:label'])
        self.assertEquals(['POINT(5.28472 52.19083)'], spatial['geos:hasGeometry'][0]['geos:asWKT'])

        body = self.getPage('/search?query=Leunseweg')
        d = loads(body, parse_float=Decimal)
        self.assertEquals(1, d['result']['total'])
        spatial = d['result']['items'][0]['dcterms:spatial'][0]
        self.assertEquals(['Leunseweg'], spatial['rdfs:label'])
        self.assertEquals('hg:Municipality', spatial['dcterms:isPartOf'][0]['@type'])
        self.assertEquals(['Venray'], spatial['dcterms:isPartOf'][0]['rdfs:label'])

    def testSearchApiQueryWithFacets(self):
        body = self.getPage('/search?query=Zeeoorlog&facets=dc:subject')
        d = loads(body, parse_float=Decimal)
        self.assertEquals(1, d['result']['total'])
        spatial = d['result']['items'][0]['dcterms:spatial'][0]
        self.assertEquals(['Soestdijk'], spatial['rdfs:label'])
        self.assertEquals(['POINT(5.28472 52.19083)'], spatial['geos:hasGeometry'][0]['geos:asWKT'])

    def testSearchApiBoundingBox(self):
        def searchResultIds(q):
            body = self.getPage('/search?' + urlencode(dict(query=q)))
            d = loads(body, parse_float=Decimal)
            return set([item['@id'] for item in d['result']['items']])
        self.assertEquals(set(['geluidVanNl:geluid_van_nederland:47954146']), searchResultIds(q='maxGeoLong=5'))
        self.assertEquals(set(['geluidVanNl:geluid_van_nederland:47954146', 'NIOD_BBWO2:niod:3366459', 'limburgs_erfgoed:oai:le:RooyNet:37']), searchResultIds(q='minGeoLong=4'))
        self.assertEquals(set(['geluidVanNl:geluid_van_nederland:47954146', 'NIOD_BBWO2:niod:3366459']), searchResultIds('minGeoLat=4 AND maxGeoLong=6 AND minGeoLat=52 AND maxGeoLat=53'))
        self.assertEquals(set([]), searchResultIds('minGeoLong=4 AND maxGeoLong=6 AND minGeoLat=53 AND maxGeoLat=54'))
        self.assertEquals(set(['limburgs_erfgoed:oai:le:RooyNet:37']), searchResultIds('minGeoLong=5.97 AND maxGeoLong=5.98 AND minGeoLat=51.51 AND maxGeoLat=51.52')) # Leunseweg, Leunen, Venray

    def assertSruQuery(self, expectedHits, query, path=None, additionalHeaders=None):
        path = path or '/sru'
        responseBody = self._doQuery(query=query, path=path, additionalHeaders=additionalHeaders)
        diagnostic = xpathFirst(responseBody, "//diag:diagnostic")
        if not diagnostic is None:
            raise RuntimeError(lxmltostring(diagnostic))
        targetUris = set(xpath(responseBody, "/srw:searchRetrieveResponse/srw:records/srw:record/srw:recordData/rdf:RDF/oa:Annotation/oa:hasTarget/@rdf:resource"))
        count = int(xpath(responseBody, "/srw:searchRetrieveResponse/srw:numberOfRecords/text()")[0])
        if type(expectedHits) is int:
            self.assertEquals(expectedHits, count)
        else:
            self.assertEquals(expectedHits, targetUris)
            self.assertEquals(len(expectedHits), count)

    def _doQuery(self, query, path=None, additionalHeaders=None, statusCode='200'):
        path = path or '/sru'
        queryArguments = {'query': query, 'version': '1.1', 'operation': 'searchRetrieve'}
        header, body = getRequest(self.erfGeoEnrichmentPort, path, queryArguments, parse=False, additionalHeaders=additionalHeaders)
        self.assertTrue(statusCode in header.split('\r\n', 1)[0])
        bodyLxml = XML(body)
        return bodyLxml

    def getPage(self, path, arguments=None):
        header, body = getRequest(self.erfGeoEnrichmentPort, path, arguments if arguments else {}, parse=False)
        return body
