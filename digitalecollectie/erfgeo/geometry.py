from re import compile

from weightless.core import compose


class Geometry(object):
    def __init__(self, coordinates):
        self.coordinates = coordinates

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, self.coordinates)

    def pointCoordinates(self):
        def _pointCoordinates(s):
            if type(s[0]) == float:
                yield s
                return
            for item in s:
                yield _pointCoordinates(item)
        return compose(_pointCoordinates(self.coordinates))

    @classmethod
    def fromGeoDict(cls, geometry):
        try:
            cls = cls._geometryTypes[geometry['type']]
        except KeyError:
            print 'skipping', geometry['type']
            from sys import stdout; stdout.flush()
            return
        return cls(geometry['coordinates'])

    @classmethod
    def parseWkt(cls, s):
        wktName, openingBracket, remainder = s.partition('(')
        s = cls._typeByWktName[wktName].__name__ + openingBracket + remainder
        expr = cls._wktPointCoordinatesRe.sub(r"(\1, \2)", s)
        evaluated = eval(expr)
        return evaluated

    _wktPointCoordinatesRe = compile('(\d+\.\d+)\s(\d+\.\d+)')

    _geometryTypes = {}
    _typeByWktName = {}

    @classmethod
    def _registerGeometryType(cls, geometryType):
        cls._geometryTypes[geometryType.__name__] = geometryType
        cls._typeByWktName[geometryType.wktName] = geometryType


class Point(Geometry):
    wktName = 'POINT'
    def asWkt(self):
        return self.wktName + '(%s)' % " ".join(str(c) for c in self.coordinates)
Geometry._registerGeometryType(Point)

class MultiLineString(Geometry):
    wktName = 'MULTILINESTRING'
    def asWkt(self):
        return self.wktName + '(%s)' % ', '.join(
            "(%s)" % ', '.join(
                ' '.join(str(c) for c in point)
                for point in lineString
            )
            for lineString in self.coordinates
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
            for polygon in self.coordinates
        )
Geometry._registerGeometryType(MultiPolygon)
