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

from decimal import Decimal

from simplejson import loads
from lxml.etree import XML

from seecr.test import SeecrTestCase, CallTrace

from weightless.core import be, asString
from meresco.core import Observable
from meresco.components.http.utils import CRLF

from digitalecollectie.erfgeo.searchjsonresponse import SearchJsonResponse, summaryWithEnrichmentToJsonLd


class SearchJsonResponseTest(SeecrTestCase):
    def testSruResponseAsJson(self):
        searchJsonResponse = SearchJsonResponse(sruPort=3333, sruPath='/sru')
        httpRequests = []
        def mockHttprequest(**kwargs):
            httpRequests.append(kwargs)
            response = 'HTTP/1.0 200 OK' + 2 * CRLF + ONE_HIT_SRU_RESPONSE
            raise StopIteration(response)
            yield

        observer = CallTrace('observer', methods=dict(httprequest=mockHttprequest))
        top = be(
            (Observable(),
                (searchJsonResponse,
                    (observer,)
                )
            )
        )
        result = asString(top.all.handleRequest(arguments={'query': ['fiets']}))
        self.assertEquals([{'headers': {}, 'host': '127.0.0.1', 'request': '/sru?version=1.1&operation=searchRetrieve&query=fiets&x-term-drilldown=edm%3AdataProvider%2Cdc%3Asubject', 'port': 3333}], httpRequests)
        header, body = result.split(CRLF * 2)
        self.assertTrue('Access-Control-Allow-Origin: *' in header)
        result = loads(body, parse_float=Decimal)
        result = result['result']
        self.assertEquals('/search?query=fiets', result['request'])
        self.assertEquals('/sru?version=1.1&operation=searchRetrieve&query=fiets&x-term-drilldown=edm%3AdataProvider%2Cdc%3Asubject', result['sruRequest'])
        self.assertEquals(1, result['total'])
        self.assertEquals(result['total'], len(result['items']))
        self.assertEquals('limburgs_erfgoed:oai:le:RooyNet:37', result['items'][0]['@id'])
        facets = result['facets']
        self.assertEquals([{'count': 1, 'value': 'RooyNet (limburgserfgoed.nl)'}], facets['edm:dataProvider'])
        self.assertEquals([
                {'count': 1, 'value': 'Zuivelfabriek Venray'},
                {'count': 1, 'value': 'Zuivelindustrie, melkfabriek'}
            ], facets['dc:subject'])
        self.assertEqual('/search?startRecord=11&query=fiets', result['nextPage'])

    def testFacetsWithHref(self):
        mockSruResponse = ONE_HIT_SRU_RESPONSE
        for (toReplace, replaceWith) in [
                    ('<srw:numberOfRecords>1<', '<srw:numberOfRecords>3<'),
                    ('<dd:item count="1">Zuivelfabriek Venray<', '<dd:item count="2">Zuivelfabriek Venray<')
                ]:
            mockSruResponse = mockSruResponse.replace(toReplace, replaceWith)

        searchJsonResponse = SearchJsonResponse(sruPort=3333, sruPath='/sru')
        httpRequests = []
        def mockHttprequest(**kwargs):
            httpRequests.append(kwargs)
            response = 'HTTP/1.0 200 OK' + 2 * CRLF + mockSruResponse
            raise StopIteration(response)
            yield

        observer = CallTrace('observer', methods=dict(httprequest=mockHttprequest))
        top = be(
            (Observable(),
                (searchJsonResponse,
                    (observer,)
                )
            )
        )
        result = asString(top.all.handleRequest(arguments={'query': ['fiets'], 'facets': ['dc:subject,edm:dataProvider']}))
        self.assertEquals([{'headers': {}, 'host': '127.0.0.1', 'request': '/sru?version=1.1&operation=searchRetrieve&query=fiets&x-term-drilldown=dc%3Asubject%2Cedm%3AdataProvider', 'port': 3333}], httpRequests)
        header, body = result.split(CRLF * 2)
        result = loads(body, parse_float=Decimal)
        facets = result['result']['facets']
        self.assertEquals([{'count': 1, 'href': '/search?query=fiets+AND+edm%3AdataProvider+exact+%22RooyNet+%28limburgserfgoed.nl%29%22&facets=dc%3Asubject%2Cedm%3AdataProvider', 'value': 'RooyNet (limburgserfgoed.nl)'}], facets['edm:dataProvider'])
        self.assertEquals([
                {'count': 2, 'href': '/search?query=fiets+AND+dc%3Asubject+exact+%22Zuivelfabriek+Venray%22&facets=dc%3Asubject%2Cedm%3AdataProvider', 'value': 'Zuivelfabriek Venray'},
                {'count': 1, 'href': '/search?query=fiets+AND+dc%3Asubject+exact+%22Zuivelindustrie%2C+melkfabriek%22&facets=dc%3Asubject%2Cedm%3AdataProvider', 'value': 'Zuivelindustrie, melkfabriek'},
            ], facets['dc:subject'])

    def testSummaryWithEnrichmentToJsonLd(self):
        result = summaryWithEnrichmentToJsonLd(XML(RDF_INPUT))
        self.assertEquals('limburgs_erfgoed:oai:le:RooyNet:37', result['@id'])
        context = result['@context']
        self.assertEquals(['dc', 'dcterms', 'edm', 'edm:isShownAt', 'edm:isShownBy', 'edm:object', 'edm:rights', 'geos', 'geos:hasGeometry', 'hg', 'hg:sameHgConcept', 'rdfs'], sorted(context.keys()))
        self.assertEquals('http://www.europeana.eu/schemas/edm/', context['edm'])
        self.assertEquals(['http://www.limburgserfgoed.nl/detail/RooyNet/37'], result['dc:identifier'])
        self.assertEquals(['gemeente: Venray', 'dorp: Leunen', 'straat: Leunseweg'], result['dc:coverage'])
        self.assertEquals(1, len(result['dcterms:spatial']))
        spatial = result['dcterms:spatial'][0]
        self.assertEquals('http://erfgeo.nl/hg/nwb/venray-leunseweg', spatial['@id'])
        self.assertEquals('hg:Street', spatial['@type'])
        self.assertEquals(['Leunseweg'], spatial['rdfs:label'])
        self.assertEquals(1, len(spatial['geos:hasGeometry']))
        geometry = spatial['geos:hasGeometry'][0]
        self.assertEquals(1, len(geometry['geos:asWKT']))
        wkt = geometry['geos:asWKT'][0]
        self.assertTrue(wkt.startswith('MULTILINESTRING('), wkt)

    def testSummaryWithConceptsToJsonLd(self):
        result = summaryWithEnrichmentToJsonLd(XML(RDF_INPUT_WITH_CONCEPTS))
        self.assertEquals('geluidVanNl:geluid_van_nederland:43663591', result['@id'])
        self.assertEquals('Eigen Opnames', result['dc:subject'][0])
        self.assertEquals('voetstappen', result['dc:subject'][1]['skos:prefLabel'])
        self.assertEquals('Nederland', result['dcterms:spatial'][0]['skos:prefLabel'])
        self.assertEquals(Decimal('52.37022'), result['dcterms:spatial'][1]['geo:lat'])


RDF_INPUT = """<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
<oa:Annotation xmlns:oa="http://www.w3.org/ns/oa#" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" rdf:about="http://data.digitalecollectie.nl/annotation/summary#bGltYnVyZ3NfZXJmZ29lZF9mcm9tX2RpZ2l0YWxlX2NvbGxlY3RpZTpvYWk6ZGF0YS5kaWdpdGFsZWNvbGxlY3RpZS5ubDpsaW1idXJnc19lcmZnb2VkOm9haTpsZTpSb295TmV0OjM3">
    <oa:annotatedBy rdf:resource="http://data.digitalecollectie.nl/id/digitalecollectie"/>
    <oa:motivatedBy rdf:resource="http://data.digitalecollectie.nl/ns/oa#summarizing"/>
    <oa:hasTarget rdf:resource="limburgs_erfgoed:oai:le:RooyNet:37"/>
    <oa:hasBody>
        <rdf:Description xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#" xmlns:prov="http://www.w3.org/ns/prov#" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:edm="http://www.europeana.eu/schemas/edm/" xmlns:meta="http://meresco.org/namespace/harvester/meta" xmlns:dcterms="http://purl.org/dc/terms/">
        <dc:contributor>Provincie Limburg (limburgserfgoed.nl)</dc:contributor>
        <dc:coverage>gemeente: Venray</dc:coverage>
        <dc:coverage>dorp: Leunen</dc:coverage>
        <dc:coverage>straat: Leunseweg</dc:coverage>
        <dc:date>1951</dc:date>
        <dc:date>1951</dc:date>
        <dc:identifier>http://www.limburgserfgoed.nl/detail/RooyNet/37</dc:identifier>
        <dc:language>nl-NL</dc:language>
        <dc:subject>Zuivelfabriek Venray</dc:subject>
        <dc:subject>Zuivelindustrie, melkfabriek</dc:subject>
        <dc:title>Zuivelfabriek Venray</dc:title>
        <dcterms:medium>foto</dcterms:medium>
        <edm:type>IMAGE</edm:type>
        <edm:dataProvider>RooyNet (limburgserfgoed.nl)</edm:dataProvider>
        <edm:isShownAt rdf:resource="http://www.rooynet.nl/index.php?option=com_databank&amp;view=zoekresultaat&amp;controller=zoekresultaat&amp;resultaat=foto&amp;Itemid=114&amp;layout=detail&amp;limitstart=0&amp;q_objectid=37&amp;rm=list&amp;uitgebreid=0&amp;layout=detail&amp;limitstart=0"/>
        <edm:isShownBy rdf:resource="http://www.rooynet.nl/assets/photo/thumbs-200/01/roy/00/001/import/25-09-2007/37.jpg"/>
        <edm:object rdf:resource="http://www.rooynet.nl/assets/photo/thumbs-200/01/roy/00/001/import/25-09-2007/37.jpg"/>
        <edm:provider>Digitale Collectie</edm:provider>
        <edm:rights rdf:resource="http://www.europeana.eu/rights/rr-f/"/>
        <prov:wasDerivedFrom>
          <prov:Entity rdf:about="limburgs_erfgoed_from_digitale_collectie:oai:data.digitalecollectie.nl:limburgs_erfgoed:oai:le:RooyNet:37">
            <dcterms:identifier>oai:data.digitalecollectie.nl:limburgs_erfgoed:oai:le:RooyNet:37</dcterms:identifier>
            <prov:wasGeneratedBy>
              <prov:Activity>
                <rdfs:label>harvest</rdfs:label>
                <prov:startedAtTime>2015-06-29T09:52:52Z</prov:startedAtTime>
                <meta:repository>
                  <rdf:Description>
                    <dcterms:identifier>limburgs_erfgoed_from_digitale_collectie</dcterms:identifier>
                    <meta:metadataPrefix>ese</meta:metadataPrefix>
                    <meta:set>limburgs_erfgoed</meta:set>
                    <meta:baseurl>http://data.digitalecollectie.nl/oai?from=2015-02-26T01:14:37Z</meta:baseurl>
                    <meta:repositoryGroupId>limburgs_erfgoed</meta:repositoryGroupId>
                  </rdf:Description>
                </meta:repository>
              </prov:Activity>
            </prov:wasGeneratedBy>
          </prov:Entity>
        </prov:wasDerivedFrom>
      </rdf:Description>
    </oa:hasBody>
  </oa:Annotation>
<oa:Annotation xmlns:oa="http://www.w3.org/ns/oa#" xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:owl="http://www.w3.org/2002/07/owl#" xmlns:hg="http://schema.histograph.io/#" xmlns:geos="http://www.opengis.net/ont/geosparql#" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" rdf:about="http://data.digitalecollectie.nl/annotation/erfGeoEnrichment#bGltYnVyZ3NfZXJmZ29lZF9mcm9tX2RpZ2l0YWxlX2NvbGxlY3RpZTpvYWk6ZGF0YS5kaWdpdGFsZWNvbGxlY3RpZS5ubDpsaW1idXJnc19lcmZnb2VkOm9haTpsZTpSb295TmV0OjM3">         <oa:annotatedBy rdf:resource="http://data.digitalecollectie.nl/id/digitalecollectie"/>
         <oa:motivatedBy rdf:resource="http://data.digitalecollectie.nl/ns/oa#erfGeoEnriching"/>
         <oa:hasTarget rdf:resource="limburgs_erfgoed:oai:le:RooyNet:37"/>
         <dcterms:source rdf:resource="https://api.erfgeo.nl/search?q=Leunseweg%2C+Leunen%2C+Venray"/>
         <oa:hasBody>
             <rdf:Description>
                 <dcterms:spatial>
<hg:PlaceInTime rdf:about="http://erfgeo.nl/hg/nwb/venray-leunseweg">
    <rdf:type rdf:resource="http://schema.histograph.io/#Street"/>
    <rdfs:label>Leunseweg</rdfs:label>
    <dcterms:source rdf:resource="http://erfgeo.nl/hg/nwb"/>
    <hg:sameHgConcept rdf:resource="http://erfgeo.nl/hg/bag/984300000000320"/>
    <geos:hasGeometry>
        <rdf:Description>
             <geos:asWKT>MULTILINESTRING((5.976364581846588 51.52243586973127, 5.977570822531698 51.521009542433255, 5.977641926636947 51.520937272278), (5.977641926636947 51.520937272278, 5.9779252893052455 51.52056729706881, 5.978463420127178 51.519845466966835), (5.978810297575312 51.51930414638479, 5.978780974683683 51.519300636494314, 5.978753517554276 51.51929103170512, 5.978725963940384 51.519272905985616, 5.978708102058019 51.51925108169847, 5.9786942063007675 51.51923287779468, 5.978688040122361 51.51920855828437, 5.9786858271487935 51.51918908170666, 5.97869714389736 51.519158579206554), (5.978463420127178 51.519845466966835, 5.978689959483037 51.51953869936622, 5.97876059153952 51.5194304755717, 5.978810297575312 51.51930414638479), (5.978942199072787 51.51912122045602, 5.97897402190174 51.519135261536135, 5.979001702402638 51.51916313044837, 5.979015786946229 51.51919471773031, 5.979020071895229 51.519223927694654, 5.979014461839677 51.51924343492792), (5.978942199072787 51.51912122045602, 5.979226543949531 51.518700018617565, 5.979439134138488 51.51842927555684, 5.979760764946663 51.517681570604, 5.979788757821533 51.517618506703975))</geos:asWKT>
        </rdf:Description>
    </geos:hasGeometry>
</hg:PlaceInTime>
                 </dcterms:spatial>
             </rdf:Description>
         </oa:hasBody>
    </oa:Annotation>
</rdf:RDF>"""

ONE_HIT_SRU_RESPONSE = """<?xml version="1.0" encoding="UTF-8"?>
<srw:searchRetrieveResponse xmlns:srw="http://www.loc.gov/zing/srw/" xmlns:diag="http://www.loc.gov/zing/srw/diagnostic/" xmlns:xcql="http://www.loc.gov/zing/cql/xcql/" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:meresco_srw="http://meresco.org/namespace/srw#">
    <srw:version>1.2</srw:version>
    <srw:numberOfRecords>1</srw:numberOfRecords>
    <srw:records>
        <srw:record>
            <srw:recordSchema>summary</srw:recordSchema>
            <srw:recordPacking>xml</srw:recordPacking>
            <srw:recordIdentifier>http://data.digitalecollectie.nl/annotation/summary#bGltYnVyZ3NfZXJmZ29lZF9mcm9tX2RpZ2l0YWxlX2NvbGxlY3RpZTpvYWk6ZGF0YS5kaWdpdGFsZWNvbGxlY3RpZS5ubDpsaW1idXJnc19lcmZnb2VkOm9haTpsZTpSb295TmV0OjM3</srw:recordIdentifier>
            <srw:recordData>%s</srw:recordData>
        </srw:record>
    </srw:records>
    <srw:nextRecordPosition>11</srw:nextRecordPosition>
    <srw:echoedSearchRetrieveRequest>
        <srw:version>1.2</srw:version>
        <srw:query>Zuivelfabriek</srw:query>
        <srw:startRecord>1</srw:startRecord>
        <srw:maximumRecords>10</srw:maximumRecords>
        <srw:recordPacking>xml</srw:recordPacking>
        <srw:recordSchema>erfGeoEnrichment+summary</srw:recordSchema>
        <srw:extraRequestData>
            <dd:drilldown xmlns:dd="http://meresco.org/namespace/drilldown" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://meresco.org/namespace/drilldown http://meresco.org/files/xsd/drilldown-20070730.xsd">
                <dd:term-drilldown>edm:dataProvider:200,dc:subject:20</dd:term-drilldown>
            </dd:drilldown>
        </srw:extraRequestData>
    </srw:echoedSearchRetrieveRequest>
    <srw:extraResponseData>
        <dd:drilldown xmlns:dd="http://meresco.org/namespace/drilldown" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://meresco.org/namespace/drilldown http://meresco.org/files/xsd/drilldown-20070730.xsd">
            <dd:term-drilldown>
                <dd:navigator name="edm:dataProvider">
                    <dd:item count="1">RooyNet (limburgserfgoed.nl)</dd:item>
                </dd:navigator>
                <dd:navigator name="dc:subject">
                    <dd:item count="1">Zuivelfabriek Venray</dd:item>
                    <dd:item count="1">Zuivelindustrie, melkfabriek</dd:item>
                </dd:navigator>
            </dd:term-drilldown>
        </dd:drilldown>
    </srw:extraResponseData>
</srw:searchRetrieveResponse>""" % RDF_INPUT

RDF_INPUT_WITH_CONCEPTS = """<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"><oa:Annotation xmlns:oa="http://www.w3.org/ns/oa#" rdf:about="http://data.digitalecollectie.nl/annotation/summary#Z2VsdWlkVmFuTmw6Z2VsdWlkX3Zhbl9uZWRlcmxhbmQ6NDM2NjM1OTE="><oa:annotatedBy rdf:resource="http://data.digitalecollectie.nl/id/digitalecollectie"/><oa:motivatedBy rdf:resource="http://data.digitalecollectie.nl/ns/oa#summarizing"/><oa:hasTarget rdf:resource="geluidVanNl:geluid_van_nederland:43663591"/><oa:hasBody><rdf:Description xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#" xmlns:prov="http://www.w3.org/ns/prov#" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:edm="http://www.europeana.eu/schemas/edm/" xmlns:meta="http://meresco.org/namespace/harvester/meta" xmlns:dcterms="http://purl.org/dc/terms/"><dc:title>Het voorbij marcheren van een peloton</dc:title>
    <dc:description>Voorbij marcheren van een peloton, over grind</dc:description>
    <dc:subject>Eigen Opnames</dc:subject>
    <dc:subject rdf:resource="http://data.beeldengeluid.nl/gtaa/231590"/>
    <dc:type>sound effect</dc:type>
    <dcterms:spatial rdf:resource="http://data.beeldengeluid.nl/gtaa/39742"/>
    <dcterms:spatial rdf:resource="geo:52.37022,4.89517"/>
    <edm:type>SOUND</edm:type>
    <dc:publisher rdf:resource="http://www.geluidvannederland.nl"/>
    <dc:creator rdf:resource="http://soundcloud.com/beeldengeluid"/>
    <dcterms:issued rdf:datatype="http://www.w3.org/2001/XMLSchema#date">2012-04-19</dcterms:issued>
    <dc:format>wav</dc:format>
    <dcterms:extent>50487 ms</dcterms:extent>
    <dc:identifier>43663591</dc:identifier>
    <dc:type>Field recording</dc:type>
    <dc:type>track</dc:type>
    <dc:language>nl</dc:language>
    <dc:rights>Creative Commons - Attribution-ShareAlike (BY-SA)</dc:rights>
    <edm:dataProvider>Nederlands Instituut voor Beeld en Geluid</edm:dataProvider>
    <edm:isShownAt rdf:resource="http://soundcloud.com/beeldengeluid/het-voorbij-marcheren-van-een"/>
    <edm:isShownBy rdf:resource="urn:soundcloud:43663591"/>
    <edm:object rdf:resource="http://www.geluidvannederland.nl/sites/default/files/HGVN_logo_cirkels.png"/>
    <edm:provider>Digitale Collectie</edm:provider>
    <edm:rights rdf:resource="http://creativecommons.org/licenses/by-sa/4.0/"/>
  </rdf:Description></oa:hasBody></oa:Annotation>
  <skos:Concept xmlns:skos="http://www.w3.org/2004/02/skos/core#" rdf:about="http://data.beeldengeluid.nl/gtaa/231590">
    <skos:notation>231590</skos:notation>
    <skos:broadMatch rdf:resource="http://data.beeldengeluid.nl/gtaa/221194"/>
    <skos:related rdf:resource="http://data.beeldengeluid.nl/gtaa/216843"/>
    <skos:related rdf:resource="http://data.beeldengeluid.nl/gtaa/221237"/>
    <skos:related rdf:resource="http://data.beeldengeluid.nl/gtaa/217293"/>
    <skos:prefLabel xml:lang="nl">voetstappen</skos:prefLabel>
    <skos:inScheme rdf:resource="http://data.beeldengeluid.nl/gtaa/OnderwerpenBenG"/>
  </skos:Concept>
  <edm:Place xmlns:edm="http://www.europeana.eu/schemas/edm/" xmlns:skos="http://www.w3.org/2004/02/skos/core#" rdf:about="http://data.beeldengeluid.nl/gtaa/39742">
    <skos:notation>39742</skos:notation>
    <skos:related rdf:resource="http://data.beeldengeluid.nl/gtaa/37778"/>
    <skos:scopeNote xml:lang="nl">Europa</skos:scopeNote>
    <skos:prefLabel xml:lang="nl">Nederland</skos:prefLabel>
    <skos:inScheme rdf:resource="http://data.beeldengeluid.nl/gtaa/GeografischeNamen"/>
  </edm:Place>
  <edm:Place xmlns:edm="http://www.europeana.eu/schemas/edm/" xmlns:geo="http://www.w3.org/2003/01/geo/wgs84_pos#" rdf:about="geo:52.37022,4.89517">
    <geo:lat>52.37022</geo:lat>
    <geo:long>4.89517</geo:long>
  </edm:Place>
</rdf:RDF>"""
