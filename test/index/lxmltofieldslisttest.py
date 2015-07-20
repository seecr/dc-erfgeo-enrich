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

from weightless.core import asList, consume

from seecr.test import SeecrTestCase, CallTrace

from digitalecollectie.erfgeo.namespaces import namespaces
from digitalecollectie.erfgeo.index.lxmltofieldslist import fieldsFromAnnotation, LxmlToFieldsList


class LxmlToFieldsListTest(SeecrTestCase):
    def testTranslateLxmlToFieldsList(self):
        lxmlTofieldslist = LxmlToFieldsList()
        observer = CallTrace(emptyGeneratorMethods=['add'])
        lxmlTofieldslist.addObserver(observer)

        consume(lxmlTofieldslist.add(lxmlNode=XML(SUMMARY_ANNOTATION)))

        self.assertEquals(['add'], observer.calledMethodNames())
        self.assertEquals(['fieldslist'], observer.calledMethods[0].kwargs.keys())

    def testFieldsFromSummaryAnnotation(self):
        fields = asList(fieldsFromAnnotation(XML(SUMMARY_ANNOTATION)))
        self.assertEquals([
                ('oa:annotatedBy.uri', "http://data.bibliotheek.nl/id/bnl"),
                ('oa:motivatedBy.uri', "http://data.bibliotheek.nl/ns/nbc/oa#summarizing"),
                ('oa:hasTarget.uri', "http://data.bibliotheek.nl/ggc/ppn/78240829X"),
                ('dcterms:type.uri', "http://dbpedia.org/ontology/Book"),
                ('dcterms:title', 'De Baerkenhuizen, Anno 1349'),
                ('dcterms:identifier.uri', 'http://data.bibliotheek.nl/ggc/ppn/78240829X'),
                ('dcterms:creator', 'Nieuwkerk Kramer, H G'),
                ('dcterms:creator.uri', 'http://data.bibliotheek.nl/ggc/ppn/987'),
                ('dcterms:creator.rdfs:label', 'Some Author'),
                ('dcterms:date', '1966'),
                ('dcterms:language.uri', 'urn:iso:std:iso:639:-2:dut'),
                ('dcterms:language.rdfs:label', 'Nederlands'),
                ('dcterms:extent', '15 p'),
                ('dcterms:isFormatOf.uri', "urn:a:work:123"),
                ('dcterms:spatial.uri', 'http://data.bibliotheek.nl/uitburo/location/8e71243e-abb0-407b-83a1-303db1f676e0'),
                ('dcterms:spatial.rdfs:label', 'Museum Boerhaave'),
                ('dcterms:spatial.geo:lat', '52.1613636'),
                ('dcterms:spatial.geo:long', '4.4891784'),
                ('dcterms:spatial.vcard:region', 'Leiden')
            ], fields)


SUMMARY_ANNOTATION = """<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
<oa:Annotation xmlns:oa="http://www.w3.org/ns/oa#" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns="http://www.openarchives.org/OAI/2.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" rdf:about="http://data.bibliotheek.nl/nbc/summary#a7c42194d70564da62e2f184a9c488298fd1493d">
    <oa:annotatedBy rdf:resource="http://data.bibliotheek.nl/id/bnl"/>
    <oa:motivatedBy rdf:resource="http://data.bibliotheek.nl/ns/nbc/oa#summarizing"/>
    <oa:hasTarget rdf:resource="http://data.bibliotheek.nl/ggc/ppn/78240829X"/>
    <oa:hasBody>
      <rdf:Description xmlns:dcterms="http://purl.org/dc/terms/" xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#" xmlns:skos="%(skos)s" xmlns:geo="%(geo)s" xmlns:vcard="%(vcard)s">
        <dcterms:type rdf:resource="http://dbpedia.org/ontology/Book"/>
        <dcterms:title>De Baerkenhuizen, Anno 1349</dcterms:title>
        <dcterms:identifier rdf:resource="http://data.bibliotheek.nl/ggc/ppn/78240829X"/>
        <dcterms:creator>Nieuwkerk Kramer, H G</dcterms:creator>
        <dcterms:creator>
            <rdf:Description rdf:about="http://data.bibliotheek.nl/ggc/ppn/987">
                <rdfs:label>Some Author</rdfs:label>
            </rdf:Description>
        </dcterms:creator>
        <dcterms:date>1966</dcterms:date>
        <dcterms:language>
          <rdf:Description rdf:about="urn:iso:std:iso:639:-2:dut">
            <rdfs:label>Nederlands</rdfs:label>
          </rdf:Description>
        </dcterms:language>
        <dcterms:extent>15 p</dcterms:extent>
        <dcterms:isFormatOf rdf:resource="urn:a:work:123"/>
        <dcterms:spatial>
          <rdf:Description rdf:about="http://data.bibliotheek.nl/uitburo/location/8e71243e-abb0-407b-83a1-303db1f676e0">
            <rdfs:label>Museum Boerhaave</rdfs:label>
            <geo:lat>52.1613636</geo:lat>
            <geo:long>4.4891784</geo:long>
            <vcard:region>Leiden</vcard:region>
          </rdf:Description>
        </dcterms:spatial>
      </rdf:Description>
    </oa:hasBody>
  </oa:Annotation>
</rdf:RDF>""" % namespaces
