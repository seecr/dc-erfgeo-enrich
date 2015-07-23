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
from re import compile

from weightless.core import compose


class Geometry(object):
    def __init__(self, *coordinates):
        self._coordinates = coordinates

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, ", ".join(repr(c) for c in self._coordinates))

    def __eq__(self, o):
        return self.__class__ is o.__class__ and \
            self._coordinates == o._coordinates

    def pointCoordinates(self):
        def _pointCoordinates(s):
            if type(s[0]) in (int, float, Decimal):
                yield tuple(s)
                return
            for item in s:
                yield _pointCoordinates(item)
        return compose(_pointCoordinates(self._coordinates))

    @classmethod
    def fromGeoDict(cls, geometry):
        try:
            cls = cls._geometryTypes[geometry['type']]
        except KeyError:
            print 'skipping', geometry['type']
            from sys import stdout; stdout.flush()
            return
        return cls(*geometry['coordinates'])

    @classmethod
    def parseWkt(cls, s):
        s = s.strip()
        wktName, openingBracket, remainder = s.partition('(')
        expr = remainder[:-1].replace('(', '[').replace(')', ']')
        expr = cls._wktPointCoordinatesRe.sub(r"[\1, \2]", expr)
        return cls._typeByWktName[wktName.strip()](*eval(expr))

    _coordinateRegex = r'[\-0-9\.Ee]+'  # not very precise, but much more maintainable and efficient than any alternative I can imagine.
    _wktPointCoordinatesRe = compile(r'(%s)\s(%s)' % (_coordinateRegex, _coordinateRegex))

    _geometryTypes = {}
    _typeByWktName = {}

    @classmethod
    def _registerGeometryType(cls, geometryType):
        cls._geometryTypes[geometryType.__name__] = geometryType
        cls._typeByWktName[geometryType.wktName] = geometryType


class Point(Geometry):
    wktName = 'POINT'
    def asWkt(self):
        return self.wktName + '(%s)' % " ".join(str(c) for c in self._coordinates)
Geometry._registerGeometryType(Point)


class MultiLineString(Geometry):
    wktName = 'MULTILINESTRING'
    def asWkt(self):
        return self.wktName + '(%s)' % ', '.join(
            "(%s)" % ', '.join(
                ' '.join(str(c) for c in point)
                for point in lineString
            )
            for lineString in self._coordinates
        )
Geometry._registerGeometryType(MultiLineString)


class MultiPolygon(Geometry):
    wktName = 'MULTIPOLYGON'
    def asWkt(self):
        return self.wktName + '(%s)' % ', '.join(
            "(%s)" % ', '.join(
                "(%s)" % ', '.join(
                    ' '.join(str(c) for c in point)
                    for point in lineString
                )
                for lineString in polygon
            )
            for polygon in self._coordinates
        )
        from sys import stdout; stdout.flush()
Geometry._registerGeometryType(MultiPolygon)
