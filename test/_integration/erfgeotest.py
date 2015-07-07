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

from digitalecollectie.erfgeo.namespaces import xpathFirst, xpath

from seecr.test.utils import getRequest
from seecr.test.integrationtestcase import IntegrationTestCase
from meresco.components import lxmltostring
from lxml.etree import XML


class ErfGeoTest(IntegrationTestCase):
    def testOaiIdentify(self):
        header, body = getRequest(self.erfGeoEnrichmentPort, '/oai', {'verb': 'Identify'})
        self.assertEquals("Digitale Collectie ErfGeo enrichments", xpathFirst(body, '/oai:OAI-PMH/oai:Identify/oai:repositoryName/text()'))

    def testOaiListRecords(self):
        header, body = getRequest(self.erfGeoEnrichmentPort, '/oai', {'verb': 'ListRecords', 'metadataPrefix': 'erfGeoEnrichment'})
        self.assertEquals(2, len(xpath(body, '/oai:OAI-PMH/oai:ListRecords/oai:record')))

        rdfElements = xpath(body, '/oai:OAI-PMH/oai:ListRecords/oai:record/oai:metadata/rdf:RDF')
        rdf = rdfElements[0]
        self.assertEquals('NIOD_BBWO2:niod:3441263', xpathFirst(rdf, 'oa:Annotation/oa:hasTarget/@rdf:resource'))
        # contains no location information to even construct a ErfGeo search API query from
        self.assertEquals(None, xpathFirst(rdf, 'oa:Annotation/oa:hasBody'))
        self.assertEquals('No ErfGeo search API query could be constructed from target record', xpathFirst(rdf, 'oa:Annotation/dcterms:description/text()'))
        self.assertEquals(None, xpathFirst(rdf, 'oa:Annotation/dcterms:source/@rdf:resource'))

        rdf = rdfElements[1]
        self.assertEquals('http://data.digitalecollectie.nl/annotation/erfGeoEnrichment#TklPRF9CQldPMjpuaW9kOjMzNjY0NTk=', xpathFirst(rdf, 'oa:Annotation/@rdf:about'))
        self.assertEquals('http://localhost:%s?q=Verenigde+Staten' % self.erfGeoApiPort, xpathFirst(rdf, 'oa:Annotation/dcterms:source/@rdf:resource'))
        self.assertEquals('NIOD_BBWO2:niod:3366459', xpathFirst(rdf, 'oa:Annotation/oa:hasTarget/@rdf:resource'))
        annotationBody = xpathFirst(rdf, 'oa:Annotation/oa:hasBody/rdf:Description')
        placeInTime = xpathFirst(annotationBody, 'dcterms:spatial/hg:PlaceInTime')
        self.assertEquals('http://erfgeo.nl/hg/bestuurlijke-grenzen-provincies-actueel/26', xpathFirst(placeInTime, '@rdf:about'))
        self.assertEquals('Utrecht', xpathFirst(placeInTime, 'rdfs:label/text()'))
        geometryWKT = xpathFirst(placeInTime, 'geos:hasGeometry/rdf:Description/geos:asWKT/text()')
        self.assertTrue(geometryWKT.startswith('MULTIPOLYGON((('), geometryWKT)

    def testOaiSets(self):
        header, body = getRequest(self.erfGeoEnrichmentPort, '/oai', {'verb': 'GetRecord', 'identifier': 'http://data.digitalecollectie.nl/annotation/erfGeoEnrichment#TklPRF9CQldPMjpuaW9kOjMzNjY0NTk=', 'metadataPrefix': 'erfGeoEnrichment'})
        self.assertEquals(set(['NIOD']), set(xpath(body, '//oai:setSpec/text()')))

        header, body = getRequest(self.erfGeoEnrichmentPort, '/oai', {'verb': 'ListSets'})
        self.assertEquals(set(['NIOD']), set(xpath(body, '//oai:setSpec/text()')))

    def testAbout(self):
        header, body = getRequest(self.erfGeoEnrichmentPort, '/about', {'uri': 'NIOD_BBWO2:niod:3366459', 'profile': 'erfGeoEnrichment'})
        rdf = xpathFirst(body, '/rdf:RDF')
        self.assertEquals('http://data.digitalecollectie.nl/annotation/erfGeoEnrichment#TklPRF9CQldPMjpuaW9kOjMzNjY0NTk=', xpathFirst(rdf, 'oa:Annotation/@rdf:about'))
        self.assertEquals('NIOD_BBWO2:niod:3366459', xpathFirst(rdf, 'oa:Annotation/oa:hasTarget/@rdf:resource'))
        annotationBody = xpathFirst(rdf, 'oa:Annotation/oa:hasBody/rdf:Description')
        placeInTime = xpathFirst(annotationBody, 'dcterms:spatial/hg:PlaceInTime')
        self.assertEquals('http://erfgeo.nl/hg/bestuurlijke-grenzen-provincies-actueel/26', xpathFirst(placeInTime, '@rdf:about'))
        self.assertEquals('Utrecht', xpathFirst(placeInTime, 'rdfs:label/text()'))
        geometryWKT = xpathFirst(placeInTime, 'geos:hasGeometry/rdf:Description/geos:asWKT/text()')
        self.assertTrue(geometryWKT.startswith('MULTIPOLYGON((('), geometryWKT)

    def testMinimalWebPresence(self):
        body = self.getPage('/index')
        self.assertTrue('<h1>ErfGeo Verrijkingen</h1>' in body, body)

    def testSru(self):
        self.assertSruQuery(2, '*')
        self.assertSruQuery(1, 'dc:subject=Zeeoorlog')
        self.assertSruQuery(2, 'meta:repositoryGroupId exact "NIOD"')

    def assertSruQuery(self, numberOfRecords, query, path=None, additionalHeaders=None):
        path = path or '/sru'
        responseBody = self._doQuery({'query': query}, path=path, additionalHeaders=additionalHeaders)
        diagnostic = xpathFirst(responseBody, "//diag:diagnostic")
        if not diagnostic is None:
            raise RuntimeError(lxmltostring(diagnostic))
        count = int(xpath(responseBody, "/srw:searchRetrieveResponse/srw:numberOfRecords/text()")[0])
        self.assertEquals(numberOfRecords, count)

    def _doQuery(self, arguments, path=None, additionalHeaders=None, statusCode='200'):
        path = path or '/sru'
        queryArguments = {'version': '1.1', 'operation': 'searchRetrieve'}
        queryArguments.update(arguments)
        header, body = getRequest(self.erfGeoEnrichmentPort, path, queryArguments, parse=False, additionalHeaders=additionalHeaders)
        print 'header:', header
        print 'body:', body
        from sys import stdout; stdout.flush()
        self.assertTrue(statusCode in header.split('\r\n', 1)[0])
        bodyLxml = XML(body)
        return bodyLxml

    def getPage(self, path, arguments=None):
        header, body = getRequest(self.erfGeoEnrichmentPort, path, arguments if arguments else {}, parse=False)
        return body
