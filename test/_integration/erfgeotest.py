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

from StringIO import StringIO
from decimal import Decimal
from urllib import urlencode

from simplejson import loads

from lxml.etree import XML, parse

from seecr.test.utils import getRequest
from seecr.test.integrationtestcase import IntegrationTestCase

from meresco.components import lxmltostring

from digitalecollectie.erfgeo.namespaces import xpathFirst, xpath


class ErfGeoTest(IntegrationTestCase):
    def testApiDescription(self):
        body = self.getPage('/api')
        self.assertFalse('Traceback' in body, body)

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
        self.assertEquals('http://localhost:%s?q=%%22Verenigde+Staten%%22' % self.erfGeoApiPort, xpathFirst(annotation, 'dcterms:source/@rdf:resource'))
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
        header, body = getRequest(self.erfGeoEnrichmentPort, '/about', {'uri': 'NIOD_BBWO2:niod:3366459', 'profile': 'erfGeoEnrichment'}, parse=False)
        bodyLxml = parse(StringIO(body))
        rdf = xpathFirst(bodyLxml, '/rdf:RDF')
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
        self.assertSruQuery(1, '__id__ exact "http://data.digitalecollectie.nl/annotation/erfGeoEnrichment#TklPRF9CQldPMjpuaW9kOjMzNjY0NTk="')
        self.assertSruQuery(1, 'id exact "NIOD_BBWO2:niod:3366459"')
        self.assertSruQuery(1, 'schema:width > 10')
        self.assertSruQuery(0, 'schema:width > 100')
        self.assertSruQuery(1, 'schema:height > 10')
        self.assertSruQuery(1, 'schema:height > 100')
        self.assertSruQuery(0, 'schema:height > 200')

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
        self.assertEquals('NIOD_BBWO2:niod:3366459', xpathFirst(rdfXml, 'oa:Annotation/oa:hasTarget/@rdf:resource'))
        self.assertEquals(['http://data.digitalecollectie.nl/annotation/summary#TklPRF9CQldPMjpuaW9kOjMzNjY0NTk=', 'http://data.digitalecollectie.nl/annotation/erfGeoEnrichment#TklPRF9CQldPMjpuaW9kOjMzNjY0NTk='], xpath(rdfXml, 'oa:Annotation/@rdf:about'))

    def testSearchApi(self):
        body = self.getPage('/search?query=Zeeoorlog')
        d = loads(body, parse_float=Decimal)
        self.assertEquals(1, d['result']['total'])
        self.assertEquals('NIOD_BBWO2:niod:3366459', d['result']['items'][0]['@id'])
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
        self.assertEquals(sorted([{'count': 1, 'value': 'Amerikaanse Strijdkrachten'}, {'count': 1, 'value': 'Piloten'}, {'count': 1, 'value': 'Reddingswezen'}, {'count': 1, 'value': 'Uitrusting - Zie ook: Uniformen, Wapens'}, {'count': 1, 'value': 'Zeeoorlog'}]), sorted(d['result']['facets']['dc:subject']))

    def testSearchApiQueryWithUnsupportedParameter(self):
        body = self.getPage('/search?query=*&xyz=abc')
        d = loads(body, parse_float=Decimal)
        errors = d['result']['errors']
        self.assertEquals(1, len(errors))
        self.assertEquals('Unsupported Parameter', errors[0]['message'])
        self.assertEquals('xyz', errors[0]['details'])
        self.assertFalse('total' in d['result'], d['result'])

    def testSearchApiBoundingBox(self):
        self.assertEquals(set(['geluidVanNl:geluid_van_nederland:47954146']), self._searchResultIds(q='maxGeoLong=5'))
        self.assertEquals(set(['geluidVanNl:geluid_van_nederland:47954146', 'NIOD_BBWO2:niod:3366459', 'limburgs_erfgoed:oai:le:RooyNet:37']), self._searchResultIds(q='minGeoLong=4'))
        self.assertEquals(set(['geluidVanNl:geluid_van_nederland:47954146', 'NIOD_BBWO2:niod:3366459']), self._searchResultIds('minGeoLat=4 AND maxGeoLong=6 AND minGeoLat=52 AND maxGeoLat=53'))
        self.assertEquals(set([]), self._searchResultIds('minGeoLong=4 AND maxGeoLong=6 AND minGeoLat=53 AND maxGeoLat=54'))
        self.assertEquals(set(['limburgs_erfgoed:oai:le:RooyNet:37']), self._searchResultIds('minGeoLong=5.97 AND maxGeoLong=5.98 AND minGeoLat=51.51 AND maxGeoLat=51.52')) # Leunseweg, Leunen, Venray

    def testSearchApiDcDateYearRange(self):
        self.assertEquals(set(['limburgs_erfgoed:oai:le:RooyNet:37']), self._searchResultIds(q='dc:date.year>1700 AND dc:date.year<1990'))

    def testDateYearFacet(self):
        body = self.getPage('/search?query=*&facets=dc:date.year')
        d = loads(body, parse_float=Decimal)
        self.assertEquals(4, d['result']['total'])
        self.assertEquals([{'count': 1, 'href': '/search?query=%2A+AND+dc%3Adate.year+exact+%221951%22&facets=dc%3Adate.year', 'value': '1951'}], d['result']['facets']['dc:date.year'])

    def _searchResultIds(self, q):
        body = self.getPage('/search?' + urlencode(dict(query=q)))
        d = loads(body, parse_float=Decimal)
        return set([item['@id'] for item in d['result']['items']])

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
        queryArguments = {'query': query, 'version': '1.2', 'operation': 'searchRetrieve'}
        header, body = getRequest(self.erfGeoEnrichmentPort, path, queryArguments, parse=False, additionalHeaders=additionalHeaders)
        self.assertTrue(statusCode in header.split('\r\n', 1)[0])
        bodyLxml = XML(body)
        return bodyLxml

    def getPage(self, path, arguments=None):
        header, body = getRequest(self.erfGeoEnrichmentPort, path, arguments if arguments else {}, parse=False)
        return body
