from meresco.lucene import DrilldownField, SORTED_PREFIX, UNTOKENIZED_PREFIX

from digitalecollectie.erfgeo.index.constants import ALL_FIELD


class SummaryFields(object):
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
        if self._keep(fieldname):
            yield fieldname, value
            if self._inAll(fieldname):
                yield ALL_FIELD, value
        yield self._untokenizedField(fieldname, value)

    def isSingleValueField(self, fieldname):
        return fieldname.startswith(SORTED_PREFIX)

    def _rename(self, fieldname):
        base, postfix = splitLastSegment(fieldname)
        if postfix in LABEL_TAGS:
            fieldname = base
        for prefix, replacement in PREFIX_RENAMES:
            if fieldname.startswith(prefix):
                fieldname = replacement + fieldname[len(prefix):]
        return fieldname

    def _keep(self, fieldname):
        base, postfix = splitLastSegment(fieldname)
        return fieldname and not fieldname in UNWANTED_FIELDS and not postfix in UNWANTED_POSTFIXES

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
]
UNWANTED_FIELDS = [
    #'oa:hasTarget.uri',
    'oa:motivatedBy.uri',
    'dcterms:spatial.geo:lat',
    'dcterms:spatial.geo:long',
    'dcterms:spatial.vcard:region',
]
UNWANTED_POSTFIXES = set(['uri'])
EXCLUDED_FROM_ALL = set([])
