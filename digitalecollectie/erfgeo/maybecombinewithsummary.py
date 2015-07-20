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
