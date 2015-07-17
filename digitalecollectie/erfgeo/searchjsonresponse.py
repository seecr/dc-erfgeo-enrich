from decimal import Decimal
from urllib import urlencode

from simplejson import dumps
from lxml.etree import XML, Element

from meresco.core import Observable
from meresco.components.http.utils import CRLF

from digitalecollectie.erfgeo.namespaces import namespaces, xpath, xpathFirst, tagToCurie, uriToCurie
from digitalecollectie.erfgeo.utils import indexOf


class SearchJsonResponse(Observable):
    def __init__(self, sruPort, sruPath, **kwargs):
        Observable.__init__(self, **kwargs)
        self._sruPort = sruPort
        self._sruPath = sruPath

    def handleRequest(self, **kwargs):
        sruRequest = self._sruPath
        headers = kwargs.get('Headers', {})
        arguments = kwargs.get('arguments')
        sruArguments = self._rewriteArgumentsForSru(arguments)
        if sruArguments:
            sruRequest = sruRequest + '?' + urlencode(sruArguments, doseq=True)
        response = yield self.any.httprequest(host='127.0.0.1', port=self._sruPort, request=sruRequest, headers=headers)
        header, body = response.split(CRLF * 2)
        jsonResponse = self._sruResponseToJson(arguments=arguments, sruResponseLxml=XML(body), sruRequest=sruRequest)
        yield 'HTTP/1.0 200 OK' + CRLF
        yield 'Content-Type: application/json' + CRLF * 2
        yield jsonResponse

    def _rewriteArgumentsForSru(self, arguments):
        sruArguments = dict(arguments, version=['1.1'], operation=['searchRetrieve'])
        if not 'x-termdrilldown' in arguments:
            sruArguments['x-term-drilldown'] = ['edm:dataProvider:200,dc:subject:20']
        # TODO: startRecord, maxRecords
        return sruArguments

    def _sruResponseToJson(self, arguments, sruResponseLxml, sruRequest):
        request = '/search?' + urlencode(arguments, doseq=True)
        total = int(xpathFirst(sruResponseLxml, '/srw:searchRetrieveResponse/srw:numberOfRecords/text()'))
        result = dict(
            request=request,
            sruRequest=sruRequest,
            total=total
        )
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
                    facetEntry['href'] = '/search?' + urlencode(dict(arguments, query=newQuery), doseq=True) # TODO: what if no query?
                facetEntries.append(facetEntry)
            facets[name] = facetEntries
        if facets:
            result['facets'] = facets
        d = dict(result=result)
        return dumps(d, indent=4, use_decimal=True, item_sort_key=lambda item: (indexOf(item[0], ['request', 'total', 'items', 'facets', 'sruRequest']), item[0]))


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
        elementCurie = tagToCurie(element.tag)
        if elementCurie == 'prov:wasDerivedFrom':
            return
        objects = []
        value = element.text
        if value and value.strip():
            value = value.strip()
            if elementCurie in DECIMAL_VALUE_RELATIONS:
                value = Decimal(value)
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
                descriptionElement = xpathFirst(rdf, '//*[@rdf:about="%s"]' % uri)
                if not descriptionElement is None:
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

    context = {}
    d = {
        '@context': context,
        '@id': xpathFirst(rdf, 'oa:Annotation/oa:hasTarget/@rdf:resource')
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

SINGLE_LITERAL_VALUE_RELATIONS = set(['geo:lat', 'geo:long', 'skos:prefLabel'])

TYPES_TO_IGNORE = set(['edm:Place', 'hg:PlaceInTime', 'oa:Annotation'])
