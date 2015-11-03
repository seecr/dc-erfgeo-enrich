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

from xml.sax.saxutils import escape as xmlEscape
from urllib import urlencode
from lxml.etree import XML

from weightless.core import asString
from meresco.core import Observable

from digitalecollectie.erfgeo.utils import getitem
from digitalecollectie.erfgeo.namespaces import namespaces, curieToUri
from digitalecollectie.erfgeo.uris import uris
from digitalecollectie.erfgeo.annotationprofiles import ERFGEO_ENRICHMENT_PROFILE


class PitToAnnotation(Observable):
    def __init__(self, searchApiBaseUrl='https://api.erfgeo.nl/search', **kwargs):
        Observable.__init__(self, **kwargs)
        self._searchApiBaseUrl = searchApiBaseUrl

    def toAnnotation(self, pit, targetUri=None, query=None, geoCoordinates=None):
        uri = None
        if targetUri:
            uri = ERFGEO_ENRICHMENT_PROFILE.uriFor(targetUri)
        return XML(asString(self._renderRdfXml(pit, uri=uri, targetUri=targetUri, query=query, geoCoordinates=geoCoordinates)))

    def _renderRdfXml(self, pit, uri, targetUri, query, geoCoordinates=None):
        source = None
        if query:
            source = "%s?%s" % (self._searchApiBaseUrl, urlencode({'q': query}))
        yield '''<rdf:RDF %(xmlns_rdf)s>\n''' % namespaces
        annotationRdfAbout = ''
        if uri:
            annotationRdfAbout = ' rdf:about="%s"' % uri
        yield '    <oa:Annotation %(xmlns_oa)s %(xmlns_rdfs)s %(xmlns_dcterms)s %(xmlns_owl)s %(xmlns_hg)s %(xmlns_geos)s %(xmlns_geo)s' % namespaces
        yield '%s\n>' % annotationRdfAbout
        yield '         <oa:annotatedBy rdf:resource="%s"/>\n' % uris.idDigitaleCollectie
        yield '         <oa:motivatedBy rdf:resource="%s"/>\n' % ERFGEO_ENRICHMENT_PROFILE.motive
        if targetUri:
            yield '         <oa:hasTarget rdf:resource="%s"/>\n' % targetUri
        if source:
            yield '         <dcterms:source rdf:resource="%s"/>\n' % xmlEscape(source)
            if pit is None:
                yield '         <dcterms:description>No PlaceInTime could be found for target record</dcterms:description>\n'
        elif not geoCoordinates is None:
            yield '         <dcterms:description>Geographical coordinates were already provided in original record</dcterms:description>\n'
        else:
            yield '         <dcterms:description>No ErfGeo search API query could be constructed from target record</dcterms:description>\n'
        if not pit is None:
            yield '         <oa:hasBody>\n'
            yield '             <rdf:Description>\n'
            yield '                 <dcterms:spatial>\n'
            yield self._renderPit(pit)
            yield '                 </dcterms:spatial>\n'
            yield '             </rdf:Description>\n'
            yield '         </oa:hasBody>\n'
        elif not geoCoordinates is None:
            geoLat, geoLong = geoCoordinates
            yield '         <oa:hasBody>\n'
            yield '             <rdf:Description>\n'
            yield '                 <geo:lat>%s</geo:lat>\n' % geoLat
            yield '                 <geo:long>%s</geo:long>\n' % geoLong
            yield '             </rdf:Description>\n'
            yield '         </oa:hasBody>\n'

        yield '    </oa:Annotation>\n'
        yield '</rdf:RDF>\n'

    def _renderPit(self, pit):
        yield '<hg:PlaceInTime rdf:about="%s">\n' % xmlEscape(pit['@id'])
        yield '    <rdf:type rdf:resource="%s"/>\n' % xmlEscape(curieToUri(pit['type']))
        yield '    <rdfs:label>%s</rdfs:label>\n' % xmlEscape(pit['name'])
        yield self._renderPartOf(pit)
        owlSameAs = pit.get('uri')
        if owlSameAs:
            yield '    <owl:sameAs rdf:resource="%s"/>\n' % xmlEscape(owlSameAs)
        sameHgConceptRelations = getitem(pit.get('relations'), 'hg:sameHgConcept', [])
        for sameHgConcept in sameHgConceptRelations:
            yield self._renderSameHgConcept(pit['@base'] + sameHgConcept['@id'])
        hasBeginning = pit.get('hasBeginning')
        if hasBeginning:
            yield '<hg:hasBeginning>%s</hg:hasBeginning>\n' % hasBeginning
        hasEnd = pit.get('hasEnd')
        if hasEnd:
            yield '<hg:hasEnd>%s</hg:hasEnd>\n' % hasEnd
        geometry = pit['geometry']
        if geometry:
            yield self._renderGeometry(geometry)
        yield '</hg:PlaceInTime>\n'

    def _renderPartOf(self, pit):
        woonplaatsnaam = getitem(pit.get('data'), 'woonplaatsnaam')
        if woonplaatsnaam:
            yield '''\
    <dcterms:isPartOf>
        <hg:Place>
            <rdfs:label>%s</rdfs:label>
        </hg:Place>
    </dcterms:isPartOf>\n''' % xmlEscape(woonplaatsnaam)

        gemeentenaam = getitem(pit.get('data'), 'gme_naam')
        if gemeentenaam:
            yield '''\
    <dcterms:isPartOf>
        <hg:Municipality>
            <rdfs:label>%s</rdfs:label>
        </hg:Municipality>
    </dcterms:isPartOf>\n''' % xmlEscape(gemeentenaam)

    def _renderSameHgConcept(self, concept):
        yield '    <hg:sameHgConcept rdf:resource="%s"/>\n' % concept

    def _renderGeometry(self, geometry):
        yield '    <geos:hasGeometry>\n'
        yield '        <rdf:Description>\n'
        yield '             <geos:asWKT>%s</geos:asWKT>\n' % geometry.asWkt()
        yield '        </rdf:Description>\n'
        yield '    </geos:hasGeometry>\n'
