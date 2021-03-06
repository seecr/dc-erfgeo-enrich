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
# Copyright (C) 2015, 2017 Netherlands Institute for Sound and Vision http://instituut.beeldengeluid.nl/
# Copyright (C) 2015, 2017 Seecr (Seek You Too B.V.) http://seecr.nl
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
from urllib import urlencode

from simplejson import dumps
from lxml.etree import XML, Element

from meresco.core import Observable
from meresco.components.http.utils import CRLF, redirectHttp

from digitalecollectie.erfgeo.namespaces import namespaces, xpath, xpathFirst, tagToCurie, uriToCurie
from digitalecollectie.erfgeo.utils import indexOf


class SearchJsonResponse(Observable):
    def __init__(self, sruPort, sruPath, **kwargs):
        Observable.__init__(self, **kwargs)
        self._sruPort = sruPort
        self._sruPath = sruPath

    def handleRequest(self, **kwargs):
        sruRequest = self._sruPath
        arguments = kwargs.get('arguments')
        if not 'query' in arguments:
            yield redirectHttp % '/api'
            return
        sruArguments = self._rewriteArgumentsForSru(arguments)
        if sruArguments:
            sruRequest = sruRequest + '?' + urlencode(sruArguments, doseq=True)
        requestHeaders = {'User-Agent': self.__class__.__name__}
        headers = kwargs.get('Headers', {})
        if 'Host' in headers:
            requestHeaders['Host'] = headers['Host']
        response = yield self.any.httprequest(host='127.0.0.1', port=self._sruPort, request=sruRequest, headers=requestHeaders)
        header, body = response.split(CRLF * 2)
        try:
            bodyLxml = XML(body)
        except Exception:
            print 'got reponse', header + CRLF * 2 + body
            import sys; sys.stdout.flush()
            raise
        jsonResponse = self._sruResponseToJson(arguments=arguments, sruResponseLxml=bodyLxml, sruRequest=sruRequest)
        yield 'HTTP/1.0 200 OK' + CRLF
        yield 'Content-Type: application/json' + CRLF
        yield 'Access-Control-Allow-Origin: *' + CRLF
        yield 'Access-Control-Allow-Headers: X-Requested-With' + CRLF
        yield 'Access-Control-Allow-Methods: GET, POST, OPTIONS' + CRLF
        yield 'Access-Control-Max-Age: 86400' + CRLF
        yield CRLF
        yield jsonResponse

    def _rewriteArgumentsForSru(self, arguments):
        sruArguments = dict(arguments)
        facets = []
        for value in arguments.get('facets', []):
            facets.extend(f.strip() for f in value.split(','))
        if facets:
            del sruArguments['facets']
        else:
            facets = ['edm:dataProvider', 'dc:subject']
        if not 'x-termdrilldown' in arguments:
            sruArguments['x-term-drilldown'] = ','.join(facets)
        if 'random' in arguments:
            random = sruArguments.pop('random')
            sruArguments['x-random'] = random
        return [('version', ['1.2']), ('operation', 'searchRetrieve')] + sruArguments.items()

    def _sruResponseToJson(self, arguments, sruResponseLxml, sruRequest):
        request = '/search?' + urlencode(arguments, doseq=True)
        result = dict(
            request=request,
            sruRequest=sruRequest
        )
        errors = xpath(sruResponseLxml, '/srw:searchRetrieveResponse/srw:diagnostics/diag:diagnostic')
        if len(errors) > 0:
            errorDicts = result['errors'] = []
            for error in errors:
                errorDicts.append({
                    'message': xpathFirst(error, 'diag:message/text()'),
                    'details': xpathFirst(error, 'diag:details/text()')
                })
                return self._resultAsJson(result)

        total = int(xpathFirst(sruResponseLxml, '/srw:searchRetrieveResponse/srw:numberOfRecords/text()'))
        result['total'] = total
        result['items'] = [summaryWithEnrichmentToJsonLd(rdf) for rdf in xpath(sruResponseLxml, '/srw:searchRetrieveResponse/srw:records/srw:record/srw:recordData/rdf:RDF')]
        facets = {}
        for navigator in xpath(sruResponseLxml, '/srw:searchRetrieveResponse/srw:extraResponseData/drilldown:drilldown/drilldown:term-drilldown/drilldown:navigator'):
            name = xpathFirst(navigator, '@name')
            facetEntries = []
            for ddItem in xpath(navigator, 'drilldown:item'):
                value = xpathFirst(ddItem, 'text()')
                count = int(xpathFirst(ddItem, '@count'))
                facetEntry = dict(value=value, count=count)
                if count != total:
                    newQuery = arguments['query'][0] + ' AND %s exact "%s"' % (name, value)
                    facetEntry['href'] = '/search?' + urlencode(dict(arguments, query=newQuery), doseq=True)
                facetEntries.append(facetEntry)
            facets[name] = facetEntries
        if facets:
            result['facets'] = facets
        nextRecordPosition = xpathFirst(sruResponseLxml, '/srw:searchRetrieveResponse/srw:nextRecordPosition/text()')
        if nextRecordPosition and not 'random' in arguments and not 'x-random' in arguments:
            result['nextPage'] = '/search?' + urlencode(dict(arguments, startRecord=nextRecordPosition), doseq=True)
        return self._resultAsJson(result)

    def _resultAsJson(self, result):
        d = dict(result=result)
        return dumps(d, indent=4, use_decimal=True, item_sort_key=lambda item: (indexOf(item[0], ['request', 'total', 'items', 'nextPage', 'facets', 'sruRequest']), item[0]))


def summaryWithEnrichmentToJsonLd(rdf):
    urisResolved = set()

    def processResourceElement(d, element):
        uri = xpathFirst(element, '@rdf:about')
        if uri:
            d['@id'] = uri
        elementCurie = tagToCurie(element.tag)
        if elementCurie != 'rdf:Description' and not elementCurie in TYPES_TO_IGNORE:
            d['@type'] = elementCurie
        for child in element.iterchildren(tag=Element):
            processRelationElement(d, child)

    def processRelationElement(d, element):
        try:
            elementCurie = tagToCurie(element.tag)
        except KeyError:
            return
        if elementCurie == 'prov:wasDerivedFrom':
            return
        objects = []
        value = element.text
        if value and value.strip():
            value = value.strip()
            if elementCurie in DECIMAL_VALUE_RELATIONS:
                value = Decimal(value)
            elif elementCurie in INTEGER_VALUE_RELATIONS:
                value = int(value)
            if elementCurie in SINGLE_LITERAL_VALUE_RELATIONS:
                d[elementCurie] = value
                return
            objects.append(value)
        uri = xpathFirst(element, '@rdf:resource')
        if uri:
            if elementCurie == 'rdf:type':
                typeCurie = uriToCurie(uri)
                if not typeCurie in TYPES_TO_IGNORE:
                    d['@type'] = typeCurie
                return
            value = uri
            if not uri in urisResolved:
                urisResolved.add(uri)
                for descriptionElement in xpath(rdf, '//*[@rdf:about="%s"]' % uri):
                    value = {}
                    processResourceElement(value, descriptionElement)
            objects.append(value)
        for child in element.iterchildren(tag=Element):
            resourceDict = {}
            processResourceElement(resourceDict, child)
            objects.append(resourceDict)
        if objects:
            d.setdefault(elementCurie, []).extend(objects)
            prefix, _, _ = elementCurie.partition(':')
            context[prefix] = namespaces[prefix]
            if elementCurie in RESOURCE_RELATIONS:
                context[elementCurie] = {"@type": "@id"}

    context = {'oa': namespaces.oa}
    d = {
        '@context': context,
        '@id': xpathFirst(rdf, 'oa:Annotation/oa:hasTarget/@rdf:resource'),
    }
    for annotationBody in xpath(rdf, 'oa:Annotation/oa:hasBody/rdf:Description'):
        for element in annotationBody.iterchildren(tag=Element):
            processRelationElement(d, element)
    return d


RESOURCE_RELATIONS = set([
    'edm:isShownAt',
    'edm:isShownBy',
    'edm:object',
    'edm:rights',
    'geos:hasGeometry',
    'hg:sameHgConcept',
    'owl:sameAs',
    'skos:inScheme',
    'skos:related',
])

DECIMAL_VALUE_RELATIONS = set(['geo:lat', 'geo:long'])

INTEGER_VALUE_RELATIONS = set(['schema:width', 'schema:height'])

SINGLE_LITERAL_VALUE_RELATIONS = set(['geo:lat', 'geo:long', 'skos:prefLabel'])

TYPES_TO_IGNORE = set(['edm:Place', 'hg:PlaceInTime', 'oa:Annotation'])
