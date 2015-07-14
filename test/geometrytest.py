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

from decimal import Decimal

from seecr.test import SeecrTestCase

from simplejson import loads

from weightless.core import asList

from digitalecollectie.erfgeo.geometry import Geometry, Point, MultiLineString, MultiPolygon


class GeometryTest(SeecrTestCase):
    def testPointFromGeoDict(self):
        json = '''{"type":"Point","coordinates":[5.976364581846588,51.52243586973127]}'''
        parsed = loads(json, parse_float=Decimal)
        g = Geometry.fromGeoDict(parsed)
        self.assertEquals(Point(Decimal('5.976364581846588'), Decimal('51.52243586973127')), g)
        self.assertEquals("Point(Decimal('5.976364581846588'), Decimal('51.52243586973127'))", repr(g))

    def testParsePointWkt(self):
        g = Geometry.parseWkt("POINT(30 10)")
        self.assertEquals(Point(30, 10), g)

    def testPointAsWkt(self):
        g = Geometry.fromGeoDict({'type': 'Point', 'coordinates': (5.97978875782, 51.5176185067)})
        self.assertEquals('POINT(5.97978875782 51.5176185067)', g.asWkt())
        self.assertEquals(g, Geometry.parseWkt(g.asWkt()))

    def testMultiLineStringFromGeoDict(self):
        json = '''{"type":"MultiLineString","coordinates":[[[5.976364581846588,51.52243586973127],[5.977570822531698,51.521009542433255],[5.977641926636947,51.520937272278]],[[5.977641926636947,51.520937272278],[5.9779252893052455,51.52056729706881],[5.978463420127178,51.519845466966835]],[[5.978810297575312,51.51930414638479],[5.978780974683683,51.519300636494314],[5.978753517554276,51.51929103170512],[5.978725963940384,51.519272905985616],[5.978708102058019,51.51925108169847],[5.9786942063007675,51.51923287779468],[5.978688040122361,51.51920855828437],[5.9786858271487935,51.51918908170666],[5.97869714389736,51.519158579206554]],[[5.978463420127178,51.519845466966835],[5.978689959483037,51.51953869936622],[5.97876059153952,51.5194304755717],[5.978810297575312,51.51930414638479]],[[5.978942199072787,51.51912122045602],[5.97897402190174,51.519135261536135],[5.979001702402638,51.51916313044837],[5.979015786946229,51.51919471773031],[5.979020071895229,51.519223927694654],[5.979014461839677,51.51924343492792]],[[5.978942199072787,51.51912122045602],[5.979226543949531,51.518700018617565],[5.979439134138488,51.51842927555684],[5.979760764946663,51.517681570604],[5.979788757821533,51.517618506703975]]]}'''
        parsed = loads(json, parse_float=Decimal)
        g = Geometry.fromGeoDict(parsed)
        r = "MultiLineString([[Decimal('5.976364581846588'), Decimal('51.52243586973127')], [Decimal('5.977570822531698'), Decimal('51.521009542433255')], [Decimal('5.977641926636947'), Decimal('51.520937272278')]], [[Decimal('5.977641926636947'), Decimal('51.520937272278')], [Decimal('5.9779252893052455'), Decimal('51.52056729706881')], [Decimal('5.978463420127178'), Decimal('51.519845466966835')]], [[Decimal('5.978810297575312'), Decimal('51.51930414638479')], [Decimal('5.978780974683683'), Decimal('51.519300636494314')], [Decimal('5.978753517554276'), Decimal('51.51929103170512')], [Decimal('5.978725963940384'), Decimal('51.519272905985616')], [Decimal('5.978708102058019'), Decimal('51.51925108169847')], [Decimal('5.9786942063007675'), Decimal('51.51923287779468')], [Decimal('5.978688040122361'), Decimal('51.51920855828437')], [Decimal('5.9786858271487935'), Decimal('51.51918908170666')], [Decimal('5.97869714389736'), Decimal('51.519158579206554')]], [[Decimal('5.978463420127178'), Decimal('51.519845466966835')], [Decimal('5.978689959483037'), Decimal('51.51953869936622')], [Decimal('5.97876059153952'), Decimal('51.5194304755717')], [Decimal('5.978810297575312'), Decimal('51.51930414638479')]], [[Decimal('5.978942199072787'), Decimal('51.51912122045602')], [Decimal('5.97897402190174'), Decimal('51.519135261536135')], [Decimal('5.979001702402638'), Decimal('51.51916313044837')], [Decimal('5.979015786946229'), Decimal('51.51919471773031')], [Decimal('5.979020071895229'), Decimal('51.519223927694654')], [Decimal('5.979014461839677'), Decimal('51.51924343492792')]], [[Decimal('5.978942199072787'), Decimal('51.51912122045602')], [Decimal('5.979226543949531'), Decimal('51.518700018617565')], [Decimal('5.979439134138488'), Decimal('51.51842927555684')], [Decimal('5.979760764946663'), Decimal('51.517681570604')], [Decimal('5.979788757821533'), Decimal('51.517618506703975')]])"
        self.assertEquals(r, repr(g))
        self.assertEquals(eval(r), g)

    def testParseMultiLineStringWkt(self):
        g = Geometry.parseWkt("MULTILINESTRING ((10 10, 20 20, 10 40), (40 40, 30 30, 40 20, 30 10))")
        r = 'MultiLineString([[10, 10], [20, 20], [10, 40]], [[40, 40], [30, 30], [40, 20], [30, 10]])'
        self.assertEquals(r, repr(g))
        self.assertEquals(eval(r), g)

    def testMultiLineStringAsWkt(self):
        g = MultiLineString([[10, 10], [20, 20], [10, 40]], [[40, 40], [30, 30], [40, 20], [30, 10]])
        self.assertEquals("MULTILINESTRING((10 10, 20 20, 10 40), (40 40, 30 30, 40 20, 30 10))", g.asWkt())
        self.assertEquals(g, Geometry.parseWkt(g.asWkt()))

    def testMultiPolygonFromGeoDict(self):
        json = '''{"type":"MultiPolygon","coordinates":[[[[40,40],[20,45],[45,30],[40,40]]],[[[20,35],[10,30],[10,10],[30,5],[45,20],[20,35]],[[30,20],[20,15],[20,25],[30,20]]]]}'''
        parsed = loads(json, parse_float=Decimal)
        g = Geometry.fromGeoDict(parsed)
        r = 'MultiPolygon([[[40, 40], [20, 45], [45, 30], [40, 40]]], [[[20, 35], [10, 30], [10, 10], [30, 5], [45, 20], [20, 35]], [[30, 20], [20, 15], [20, 25], [30, 20]]])'
        self.assertEquals(r, repr(g))
        self.assertEquals(eval(r), g)

    def testParseMultiPolygonWkt(self):
        g = Geometry.parseWkt("MULTIPOLYGON (((40 40, 20 45, 45 30, 40 40)), ((20 35, 10 30, 10 10, 30 5, 45 20, 20 35), (30 20, 20 15, 20 25, 30 20)))")
        r = 'MultiPolygon([[[40, 40], [20, 45], [45, 30], [40, 40]]], [[[20, 35], [10, 30], [10, 10], [30, 5], [45, 20], [20, 35]], [[30, 20], [20, 15], [20, 25], [30, 20]]])'
        self.assertEquals(r, repr(g))
        self.assertEquals(eval(r), g)

    def testMultiPolygonAsWkt(self):
        g = MultiPolygon([[[40, 40], [20, 45], [45, 30], [40, 40]]], [[[20, 35], [10, 30], [10, 10], [30, 5], [45, 20], [20, 35]], [[30, 20], [20, 15], [20, 25], [30, 20]]])
        self.assertEquals("MULTIPOLYGON(((40 40, 20 45, 45 30, 40 40)), ((20 35, 10 30, 10 10, 30 5, 45 20, 20 35), (30 20, 20 15, 20 25, 30 20)))", g.asWkt())
        self.assertEquals(g, Geometry.parseWkt(g.asWkt()))

    def testPointCoordinates(self):
        g = Geometry.parseWkt("POINT(30 10)")
        self.assertEquals([(30, 10)], asList(g.pointCoordinates()))

        g = Geometry.parseWkt("POINT(30.12 10.07)")
        self.assertEquals([(30.12, 10.07)], asList(g.pointCoordinates()))

        g = Geometry.parseWkt("POINT(5.979788757821533 51.517618506703975)")
        self.assertEquals([(5.979788757821533, 51.517618506703975)], asList(g.pointCoordinates()))

        g = Point(Decimal('5.976364581846588'), Decimal('51.52243586973127'))
        self.assertEquals([(Decimal('5.976364581846588'), Decimal('51.52243586973127'))], asList(g.pointCoordinates()))

        g = MultiLineString([[10, 10], [20, 20], [10, 40]], [[40, 40], [30, 30], [40, 20], [30, 10]])
        self.assertEquals([(10, 10), (20, 20), (10, 40), (40, 40), (30, 30), (40, 20), (30, 10)], asList(g.pointCoordinates()))

        g = MultiPolygon([[[40, 40], [20, 45], [45, 30], [40, 40]]], [[[20, 35], [10, 30], [10, 10], [30, 5], [45, 20], [20, 35]], [[30, 20], [20, 15], [20, 25], [30, 20]]])
        self.assertEquals([(40, 40), (20, 45), (45, 30), (40, 40), (20, 35), (10, 30), (10, 10), (30, 5), (45, 20), (20, 35), (30, 20), (20, 15), (20, 25), (30, 20)], asList(g.pointCoordinates()))

