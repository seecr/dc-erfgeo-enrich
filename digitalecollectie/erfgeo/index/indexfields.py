from meresco.lucene import DrilldownField, SORTED_PREFIX, UNTOKENIZED_PREFIX

from digitalecollectie.erfgeo.index.constants import ALL_FIELD
from digitalecollectie.erfgeo.geometry import Geometry, Point, MultiLineString, MultiPolygon


class IndexFields(object):
    drilldownFields = [
        DrilldownField(name=UNTOKENIZED_PREFIX + fieldname, hierarchical=False, multiValued=True) for fieldname in [
            # in summary index
            'dc:creator',
            'dc:date',
            'dc:language',
            'dc:publisher',
            'dc:subject',
            'dc:type',
            'edm:dataProvider',
            'meta:repository',
            'meta:repositoryGroupId',
            'meta:collection',
            'oai:setSpec',
        ]
    ]
    untokenizedFieldnames = [df.name for df in drilldownFields]

    def __init__(self, observable):
        self._observable = observable

    def fieldsFor(self, fieldname, value):
        fieldname = self._rename(fieldname)
        for fieldname, value in self._evaluate(fieldname, value):
            if self._keep(fieldname):
                print 'fieldname, value', fieldname, value
                from sys import stdout; stdout.flush()
                yield fieldname, value
                if self._inAll(fieldname):
                    yield ALL_FIELD, value
        yield self._untokenizedField(fieldname, value)

    def isSingleValueField(self, fieldname):
        return fieldname.startswith(SORTED_PREFIX)

    def _rename(self, fieldname):
        for prefix, replacement in PREFIX_RENAMES:
            if fieldname.startswith(prefix):
                fieldname = replacement + fieldname[len(prefix):]
        base, postfix = splitLastSegment(fieldname)
        if postfix in LABEL_TAGS:
            fieldname = base
        return fieldname

    def _keep(self, fieldname):
        base, postfix = splitLastSegment(fieldname)
        return fieldname and not fieldname in UNWANTED_FIELDS and not postfix in UNWANTED_POSTFIXES

    def _evaluate(self, fieldname, value):
        if fieldname != 'dcterms:spatial.geos:hasGeometry.geos:asWKT':
            yield fieldname, value
            return
        geometry = Geometry.parseWkt(value)
        for (geoLong, geoLat) in geometry.pointCoordinates():
            yield 'dcterms:spatial.geo:long', geoLong
            yield 'dcterms:spatial.geo:lat', geoLat

        # if isinstance(geometry, Point):
        #     print 'Point'
        #     from sys import stdout; stdout.flush()
        #     yield 'dcterms:spatial.geo:long', geometry.coordinates[0]
        #     yield 'dcterms:spatial.geo:lat', geometry.coordinates[1]
        # elif isinstance(geometry, MultiPolygon):
        #     print 'MultiPolygon'
        #     from sys import stdout; stdout.flush()
        #     for c in geometry.coordinates:
        #         if type(c) == tuple:
        #             yield 'dcterms:spatial.geo:long', c[0]
        #             yield 'dcterms:spatial.geo:lat', c[1]
        # elif isinstance(geometry, MultiLineString):
        #     print 'MultiLineString'
        #     from sys import stdout; stdout.flush()
        #     yield 'dcterms:spatial.geo:long', geometry.coordinates[0][0]
        #     yield 'dcterms:spatial.geo:lat', geometry.coordinates[0][1]


    def _inAll(self, fieldname):
        return not fieldname in EXCLUDED_FROM_ALL

    def _untokenizedField(self, fieldname, value):
        name = untokenizedFieldname(fieldname)
        if name in self.untokenizedFieldnames:
            yield name, value


def splitLastSegment(name):
    base, sep, postfix = name.rpartition('.')
    return (base, postfix) if sep else (postfix, '')

def untokenizedFieldname(fieldname):
    return UNTOKENIZED_PREFIX + fieldname


LABEL_TAGS = ['rdfs:label', 'skos:altLabel', 'skos:prefLabel']

# prov:wasDerivedFrom.prov:Entity.prov:wasGeneratedBy.prov:Activity.prov:startedAtTime

PREFIX_RENAMES = [
    ('prov:wasDerivedFrom.prov:Entity.dcterms:identifier', 'meta:recordId'),
    ('prov:wasDerivedFrom.prov:Entity.prov:wasGeneratedBy.prov:Activity', ''),
    ('.', ''),
    ('prov:startedAtTime', ''),
    ('meta:repository.dcterms:identifier', 'meta:repository'),
    ('meta:repository.', ''),
    ('meta:baseurl', ''),
    ('meta:metadataPrefix', ''),
    ('meta:set', ''),
    ('dcterms:spatial.hg:PlaceInTime', 'dcterms:spatial')
]
UNWANTED_FIELDS = [
    #'oa:hasTarget.uri',
    'oa:motivatedBy.uri',
    'dcterms:spatial.vcard:region',
]
UNWANTED_POSTFIXES = set(['uri'])  # Not so sure
EXCLUDED_FROM_ALL = set(['dcterms:spatial.geo:long', 'dcterms:spatial.geo:lat'])
