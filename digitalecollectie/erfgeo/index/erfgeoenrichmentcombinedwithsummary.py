from lxml.etree import XML

from weightless.core import asString
from meresco.core import Observable
from meresco.components import lxmltostring

from digitalecollectie.erfgeo.annotationprofiles import SUMMARY_PROFILE, ERFGEO_ENRICHMENT_PROFILE
from digitalecollectie.erfgeo.namespaces import xpath, xpathFirst


class ErfGeoEnrichmentCombinedWithSummary(Observable):
    def add(self, identifier, partname, lxmlNode):
        targetUri = xpathFirst(lxmlNode, '/rdf:RDF/oa:Annotation/oa:hasTarget/@rdf:resource')
        summary = yield self.any.about(uri=targetUri, profile=SUMMARY_PROFILE.prefix)
        combined = summary
        if not xpathFirst(lxmlNode, '/rdf:RDF/oa:Annotation/oa:hasBody') is None:
            combined = asString(self.combine(erfgeoEnrichmentLxml=lxmlNode, summaryLxml=XML(summary)))
        yield self.all.add(identifier=targetUri, partname='combined', lxmlNode=XML(combined))

    def yieldRecord(self, identifier, partname):
        assert partname == 'summary+erfGeoEnrichment', partname
        erfGeoEnrichmentUri = ERFGEO_ENRICHMENT_PROFILE.uriFor(identifier)
        erfgeoEnrichment = self.call.getData(identifier=erfGeoEnrichmentUri, name=ERFGEO_ENRICHMENT_PROFILE.prefix)
        summary = yield self.any.about(uri=identifier, profile=SUMMARY_PROFILE.prefix)
        combined = asString(self.combine(erfgeoEnrichmentLxml=XML(erfgeoEnrichment), summaryLxml=XML(summary)))
        yield combined

    def combine(self, erfgeoEnrichmentLxml, summaryLxml):
        yield '<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">\n'
        for rdfLxml in [summaryLxml, erfgeoEnrichmentLxml]:
            for child in xpath(rdfLxml, '/rdf:RDF/*'):
                yield lxmltostring(child)
        yield '</rdf:RDF>'
