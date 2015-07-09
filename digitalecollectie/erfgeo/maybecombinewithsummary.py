from lxml.etree import XML

from weightless.core import asString
from meresco.core import Observable
from meresco.components import lxmltostring

from digitalecollectie.erfgeo.annotationprofiles import SUMMARY_PROFILE, ERFGEO_ENRICHMENT_PROFILE
from digitalecollectie.erfgeo.namespaces import xpath


COMBINED_METADATA_PREFIX = 'erfGeoEnrichment+summary'

class MaybeCombineWithSummary(Observable):
    def getData(self, identifier, **kwargs):
        for identifier, data in self.getMultipleData(identifiers=[identifier], **kwargs):
            return data

    def getMultipleData(self, name, identifiers, **kwargs):
        identifiers = list(identifiers)
        erfgeoEnrichments = self.call.getMultipleData(identifiers=identifiers, name='erfGeoEnrichment', **kwargs)
        if name == ERFGEO_ENRICHMENT_PROFILE.prefix:
            return erfgeoEnrichments
        elif name != COMBINED_METADATA_PREFIX:
            raise ValueError('unsupported name %s' % name)

        summaryIdentifiers = [
            SUMMARY_PROFILE.uriFor(ERFGEO_ENRICHMENT_PROFILE.targetUriFrom(identifier))
            for identifier
            in identifiers
        ]
        summaries = dict(self.call.getMultipleData(identifiers=summaryIdentifiers, name=SUMMARY_PROFILE.prefix, **kwargs))
        return (
            (
                erfGeoEnrichmentUri,
                asString(
                    self._combine(
                        erfgeoEnrichmentData,
                        summaries[SUMMARY_PROFILE.uriFor(ERFGEO_ENRICHMENT_PROFILE.targetUriFrom(erfGeoEnrichmentUri))]
                    )
                )
            )
            for erfGeoEnrichmentUri, erfgeoEnrichmentData
            in erfgeoEnrichments
        )

    def yieldRecord(self, identifier, partname):
        yield self.getData(identifier=identifier, name=partname)

    def _combine(self, erfgeoEnrichment, summary):
        yield '<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">\n'
        for data in [summary, erfgeoEnrichment]:
            rdfLxml = XML(data)
            for child in xpath(rdfLxml, '/rdf:RDF/*'):
                yield lxmltostring(child)
        yield '</rdf:RDF>'
