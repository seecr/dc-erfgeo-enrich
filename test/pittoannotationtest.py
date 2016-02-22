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
# Copyright (C) 2015-2016 Netherlands Institute for Sound and Vision http://instituut.beeldengeluid.nl/
# Copyright (C) 2015-2016 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2015-2016 Stichting DEN http://www.den.nl
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

from seecr.test import SeecrTestCase

from digitalecollectie.erfgeo.geometry import Geometry
from digitalecollectie.erfgeo.namespaces import xpathFirst
from digitalecollectie.erfgeo.pittoannotation import PitToAnnotation


class PitToAnnotationTest(SeecrTestCase):
    def testAnnotationFromPit(self):
        pitToAnnotation = PitToAnnotation(searchApiBaseUrl="http://example.org/search")
        pit = {'@base': "http://rdf.histograph.io/", '@id': 'nwb/venray-leunseweg', 'data': {'woonplaatsnaam': 'Venray'}, 'type': 'hg:Street', 'name': "Leunseweg", 'geometry': Geometry.fromGeoDict({'type':'MultiLineString', 'coordinates': [[[5.976364581846588,51.52243586973127],[5.977570822531698,51.521009542433255],[5.977641926636947,51.520937272278]],[[5.977641926636947,51.520937272278],[5.9779252893052455,51.52056729706881],[5.978463420127178,51.519845466966835]],[[5.978810297575312,51.51930414638479],[5.978780974683683,51.519300636494314],[5.978753517554276,51.51929103170512],[5.978725963940384,51.519272905985616],[5.978708102058019,51.51925108169847],[5.9786942063007675,51.51923287779468],[5.978688040122361,51.51920855828437],[5.9786858271487935,51.51918908170666],[5.97869714389736,51.519158579206554]],[[5.978463420127178,51.519845466966835],[5.978689959483037,51.51953869936622],[5.97876059153952,51.5194304755717],[5.978810297575312,51.51930414638479]],[[5.978942199072787,51.51912122045602],[5.97897402190174,51.519135261536135],[5.979001702402638,51.51916313044837],[5.979015786946229,51.51919471773031],[5.979020071895229,51.519223927694654],[5.979014461839677,51.51924343492792]],[[5.978942199072787,51.51912122045602],[5.979226543949531,51.518700018617565],[5.979439134138488,51.51842927555684],[5.979760764946663,51.517681570604],[5.979788757821533,51.517618506703975]]]}), 'relations': {'hg:sameHgConcept': [{'@id': "http://sws.geonames.org/2754999/"}]}}

        annotation = pitToAnnotation.toAnnotation(pit=pit, targetUri='the:uri', query="Leunseweg, Leunen, Venray")

        self.assertEquals('the:uri', xpathFirst(annotation, '/rdf:RDF/oa:Annotation/oa:hasTarget/@rdf:resource'))
        self.assertEquals('http://data.digitalecollectie.nl/ns/oa#erfGeoEnriching', xpathFirst(annotation, '/rdf:RDF/oa:Annotation/oa:motivatedBy/@rdf:resource'))
        self.assertEquals("http://data.digitalecollectie.nl/id/digitalecollectie", xpathFirst(annotation, '/rdf:RDF/oa:Annotation/oa:annotatedBy/@rdf:resource'))
        self.assertEquals('http://example.org/search?q=Leunseweg%2C+Leunen%2C+Venray', xpathFirst(annotation, '/rdf:RDF/oa:Annotation/dcterms:source/@rdf:resource'))

        annotationBody = xpathFirst(annotation, '/rdf:RDF/oa:Annotation/oa:hasBody/rdf:Description')
        placeInTime = xpathFirst(annotationBody, 'dcterms:spatial/hg:PlaceInTime')
        self.assertEquals("nwb/venray-leunseweg", xpathFirst(placeInTime, '@rdf:about'))
        self.assertEquals("http://schema.histograph.io/#Street", xpathFirst(placeInTime, 'rdf:type/@rdf:resource'))
        self.assertEquals('Leunseweg', xpathFirst(placeInTime, 'rdfs:label/text()'))
        self.assertEquals("http://sws.geonames.org/2754999/", xpathFirst(placeInTime, 'hg:sameHgConcept/@rdf:resource'))
        geometry = xpathFirst(placeInTime, 'geos:hasGeometry/rdf:Description/geos:asWKT/text()')
        self.assertTrue(geometry.startswith('MULTILINESTRING((5.97'), geometry)
        self.assertEquals('Venray', xpathFirst(placeInTime, 'dcterms:isPartOf/hg:Place/rdfs:label/text()'))

    def testNoResultPit(self):
        pitToAnnotation = PitToAnnotation(searchApiBaseUrl="http://example.org/search")
        annotation = pitToAnnotation.toAnnotation(pit=None, targetUri='the:uri', query="No match to be found")
        self.assertEquals('the:uri', xpathFirst(annotation, '/rdf:RDF/oa:Annotation/oa:hasTarget/@rdf:resource'))
        self.assertEquals('http://data.digitalecollectie.nl/ns/oa#erfGeoEnriching', xpathFirst(annotation, '/rdf:RDF/oa:Annotation/oa:motivatedBy/@rdf:resource'))
        self.assertEquals("http://data.digitalecollectie.nl/id/digitalecollectie", xpathFirst(annotation, '/rdf:RDF/oa:Annotation/oa:annotatedBy/@rdf:resource'))
        self.assertEquals('http://example.org/search?q=No+match+to+be+found', xpathFirst(annotation, '/rdf:RDF/oa:Annotation/dcterms:source/@rdf:resource'))
        self.assertEquals('No PlaceInTime could be found for target record', xpathFirst(annotation, '/rdf:RDF/oa:Annotation/dcterms:description/text()'))
        self.assertEquals(None, xpathFirst(annotation, '/rdf:RDF/oa:Annotation/oa:hasBody/rdf:Description'))

    def testNoQuery(self):
        pitToAnnotation = PitToAnnotation(searchApiBaseUrl="http://example.org/search")
        annotation = pitToAnnotation.toAnnotation(pit=None, targetUri='the:uri', query=None)
        self.assertEquals('the:uri', xpathFirst(annotation, '/rdf:RDF/oa:Annotation/oa:hasTarget/@rdf:resource'))
        self.assertEquals('http://data.digitalecollectie.nl/ns/oa#erfGeoEnriching', xpathFirst(annotation, '/rdf:RDF/oa:Annotation/oa:motivatedBy/@rdf:resource'))
        self.assertEquals("http://data.digitalecollectie.nl/id/digitalecollectie", xpathFirst(annotation, '/rdf:RDF/oa:Annotation/oa:annotatedBy/@rdf:resource'))
        self.assertEquals(None, xpathFirst(annotation, '/rdf:RDF/oa:Annotation/dcterms:source/@rdf:resource'))
        self.assertEquals('No ErfGeo search API query could be constructed from target record', xpathFirst(annotation, '/rdf:RDF/oa:Annotation/dcterms:description/text()'))
        self.assertEquals(None, xpathFirst(annotation, '/rdf:RDF/oa:Annotation/oa:hasBody/rdf:Description'))

    def testGeoCoordinatesInsteadOfPit(self):
        pitToAnnotation = PitToAnnotation(searchApiBaseUrl="http://example.org/search")
        annotation = pitToAnnotation.toAnnotation(pit=None, targetUri='the:uri', query=None, geoCoordinates=('5.0', '51.23'))
        self.assertEquals('the:uri', xpathFirst(annotation, '/rdf:RDF/oa:Annotation/oa:hasTarget/@rdf:resource'))
        self.assertEquals('http://data.digitalecollectie.nl/ns/oa#erfGeoEnriching', xpathFirst(annotation, '/rdf:RDF/oa:Annotation/oa:motivatedBy/@rdf:resource'))
        self.assertEquals("http://data.digitalecollectie.nl/id/digitalecollectie", xpathFirst(annotation, '/rdf:RDF/oa:Annotation/oa:annotatedBy/@rdf:resource'))
        self.assertEquals(None, xpathFirst(annotation, '/rdf:RDF/oa:Annotation/dcterms:source'))
        self.assertEquals('Geographical coordinates were already provided in original record', xpathFirst(annotation, '/rdf:RDF/oa:Annotation/dcterms:description/text()'))
        self.assertEquals('5.0', xpathFirst(annotation, '/rdf:RDF/oa:Annotation/oa:hasBody/rdf:Description/geo:lat/text()'))
        self.assertEquals('51.23', xpathFirst(annotation, '/rdf:RDF/oa:Annotation/oa:hasBody/rdf:Description/geo:long/text()'))
