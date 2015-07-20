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
# Copyright (C) 2014-2015 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
# Copyright (C) 2015 Netherlands Institute for Sound and Vision http://instituut.beeldengeluid.nl/
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

from weightless.core import consume, compose

from seecr.test import SeecrTestCase, CallTrace

from meresco.lucene import DrilldownField, UNTOKENIZED_PREFIX, SORTED_PREFIX
from meresco.lucene.fieldregistry import FieldRegistry

from org.apache.lucene.facet import FacetField

from digitalecollectie.erfgeo.index.constants import ALL_FIELD
from digitalecollectie.erfgeo.index.fieldslisttolucenedocument import FieldsListToLuceneDocument
from digitalecollectie.erfgeo.index.lxmltofieldslist import fieldsFromAnnotation


class FieldsListToLuceneDocumentTest(SeecrTestCase):
    def testAddAnnotation(self):
        fieldRegistry = FieldRegistry(drilldownFields=_SummaryFields.drilldownFields)
        index = FieldsListToLuceneDocument(fieldRegistry, indexFieldFactory=_SummaryFields)
        observer = CallTrace(
            emptyGeneratorMethods=['addDocument'],
            returnValues=dict(numerateTerm=1)
        )
        index.addObserver(observer)
        consume(index.add(identifier="", fieldslist=compose(fieldsFromAnnotation(XML(SUMMARY_ANNOTATION)))))
        self.assertEquals(['addDocument'], observer.calledMethodNames())
        document = observer.calledMethods[0].kwargs['document']
        searchFields, facetsFields = fieldsFromDocument(document)
        self.assertEquals(set([u'oa:motivatedBy.uri', u'dc:type', u'dc:title', u'dc:language', u'edm:type', u'dc:publisher.uri', u'dcterms:extent', u'dc:subject', u'__all__', u'dc:identifier', u'edm:object.uri', u'edm:isShownBy.uri', u'dc:format', u'edm:isShownAt.uri', u'dc:description', u'dc:rights', u'oa:annotatedBy.uri', u'oa:hasTarget.uri', u'edm:dataProvider', u'dcterms:issued', u'dcterms:spatial.uri', u'dc:creator.uri', u'edm:provider', u'edm:rights.uri']), set([f.name() for f in searchFields]))
        self.assertEquals([(u'untokenized.dc:subject', [u'hoorspelen']), (u'untokenized.dc:subject', [u'artis']), (u'untokenized.dc:subject', [u'nijlpaarden']), (u'untokenized.dc:subject', [u'bejaardentehuizen']), (u'untokenized.dc:subject', [u'concertgebouw']), (u'untokenized.dc:subject', [u'gesprekken']), (u'untokenized.dc:type', [u'spoken']), (u'untokenized.edm:type', [u'SOUND']), (u'untokenized.dcterms:issued', [u'2013-05-07']), (u'untokenized.dc:type', [u'Hoorspelen']), (u'untokenized.dc:type', [u'track']), (u'untokenized.dc:language', [u'nl']), (u'untokenized.edm:dataProvider', [u'Nederlands Instituut voor Beeld en Geluid'])], [(f.dim, list(f.path)) for f in facetsFields])


def fieldsFromDocument(document):
    searchFields = [f for f in document.getFields() if not FacetField.instance_(f)]
    facetsFields = [FacetField.cast_(f) for f in document.getFields() if FacetField.instance_(f)]
    return searchFields, facetsFields


class _SummaryFields(object):
    drilldownFields = [
        DrilldownField(name=UNTOKENIZED_PREFIX + fieldname, hierarchical=False, multiValued=True) for fieldname in [
            'dc:language',
            'dcterms:issued',
            'dc:subject',
            'dc:type',
            'edm:dataProvider',
            'edm:type',
            'meta.repository.id',
            'meta.repository.repositoryGroupId',
            'meta.repository.collection',
            'header.setSpec',
        ]
    ]
    untokenizedFieldnames = [df.name for df in drilldownFields]

    def __init__(self, observable):
        self._observable = observable
        self._fieldnames = set()

    def fieldsFor(self, fieldname, value):
        yield fieldname, value
        if not fieldname.endswith(".uri"):
            yield ALL_FIELD, value
        name = UNTOKENIZED_PREFIX + fieldname
        if name in self.untokenizedFieldnames:
            yield name, value

    def isSingleValueField(self, fieldname):
        return fieldname.startswith(SORTED_PREFIX)


SUMMARY_ANNOTATION = """<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"><oa:Annotation xmlns:oa="http://www.w3.org/ns/oa#" rdf:about="http://data.digitalecollectie.nl/annotation/summary#aHR0cDovL2FwaS5zb3VuZGNsb3VkLmNvbS90cmFja3MvOTEwNzA4NzQ="><oa:annotatedBy rdf:resource="http://data.digitalecollectie.nl/id/digitalecollectie"/><oa:motivatedBy rdf:resource="http://data.digitalecollectie.nl/ns/oa#summarizing"/><oa:hasTarget rdf:resource="http://api.soundcloud.com/tracks/91070874"/><oa:hasBody><rdf:Description xmlns:dcterms="http://purl.org/dc/terms/" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:edm="http://www.europeana.eu/schemas/edm/"><dc:title>Hoorspel "Tanja"</dc:title>
    <dc:description>Tijdens het evenement "Wiki Loves Sound" georganiseerd door www.geluidvannederland.nl en Wikimedia Nederland is een workshop "hoorspelen maken" georganiseerd. Workshopleden maakten in samenwerking met rADIO MOBi het hoorspel "Tanja".

In dit hoorspel herbeleeft Meneer de Vries zijn herinneringen aan Tanja samen met een medebewoner uit het bejaardentehuis. Hun herinneringen lijken elkaar onverwacht te kruisen.

Gebruikte opnamen komen uit het Geluidenarchief van Het Nederlands Instituut voor Beeld en Geluid:

1. https://soundcloud.com/beeldengeluid/algemene-sfeer-in-de-aula-van
2. https://soundcloud.com/beeldengeluid/artis-publiek-bij-de
3. https://soundcloud.com/beeldengeluid/concertgebouw-amsterdam-11 </dc:description>
    <dc:subject>hoorspelen</dc:subject>
    <dc:subject>artis</dc:subject>
    <dc:subject>nijlpaarden</dc:subject>
    <dc:subject>bejaardentehuizen</dc:subject>
    <dc:subject>concertgebouw</dc:subject>
    <dc:subject>gesprekken</dc:subject>
    <dc:type>spoken</dc:type>
    <dcterms:spatial rdf:resource="http://example.org/location/VeenendaalTurbinestraat9"/>
    <edm:type>SOUND</edm:type>
    <dc:publisher rdf:resource="http://www.geluidvannederland.nl"/>
    <dc:creator rdf:resource="http://soundcloud.com/beeldengeluid"/>
    <dcterms:issued rdf:datatype="http://www.w3.org/2001/XMLSchema#date">2013-05-07</dcterms:issued>
    <dc:format>wav</dc:format>
    <dcterms:extent>120591 ms</dcterms:extent>
    <dc:identifier>91070874</dc:identifier>
    <dc:type>Hoorspelen</dc:type>
    <dc:type>track</dc:type>
    <dc:language>nl</dc:language>
    <dc:rights>Creative Commons - Attribution-ShareAlike (BY-SA)</dc:rights>
  <edm:dataProvider>Nederlands Instituut voor Beeld en Geluid</edm:dataProvider>
    <edm:isShownAt rdf:resource="http://soundcloud.com/beeldengeluid/hoorspel-tanja"/>
    <edm:isShownBy rdf:resource="urn:soundcloud:91070874"/>
    <edm:object rdf:resource="http://www.geluidvannederland.nl/sites/default/files/HGVN_logo_cirkels.png"/>
    <edm:provider>Digitale Collectie</edm:provider>
    <edm:rights rdf:resource="http://creativecommons.org/licenses/by-sa/4.0/"/>
  </rdf:Description></oa:hasBody></oa:Annotation><edm:Place xmlns:geo="http://www.w3.org/2003/01/geo/wgs84_pos#" xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#" xmlns:edm="http://www.europeana.eu/schemas/edm/" rdf:about="http://example.org/location/VeenendaalTurbinestraat9">
    <rdfs:label xml:lang="nl">Turbinestraat 9, Veenendaal</rdfs:label>
    <geo:lat>52.008763</geo:lat>
    <geo:long>5.5715179,17</geo:long>
  </edm:Place>
  <edm:Agent xmlns:edm="http://www.europeana.eu/schemas/edm/" xmlns:skos="http://www.w3.org/2004/02/skos/core#" xmlns:foaf="http://xmlns.com/foaf/0.1/" rdf:about="http://www.geluidvannederland.nl">
    <skos:prefLabel>Het Geluid van Nederland</skos:prefLabel>
    <foaf:name>Het Geluid van Nederland</foaf:name>
    <foaf:homepage rdf:resource="http://www.geluidvannederland.nl"/>
  </edm:Agent>
  <edm:Agent xmlns:edm="http://www.europeana.eu/schemas/edm/" xmlns:skos="http://www.w3.org/2004/02/skos/core#" xmlns:foaf="http://xmlns.com/foaf/0.1/" rdf:about="http://soundcloud.com/beeldengeluid">
    <skos:prefLabel>Beeld en Geluid</skos:prefLabel>
    <foaf:homepage rdf:resource="http://soundcloud.com/beeldengeluid"/>
  </edm:Agent>
  </rdf:RDF>"""
