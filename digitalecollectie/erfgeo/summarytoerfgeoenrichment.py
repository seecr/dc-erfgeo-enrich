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

from meresco.core import Observable

from digitalecollectie.erfgeo.utils import first, getitem
from digitalecollectie.erfgeo.namespaces import xpath, xpathFirst
from digitalecollectie.erfgeo.annotationprofiles import ERFGEO_ENRICHMENT_PROFILE, SUMMARY_PROFILE


class SummaryToErfGeoEnrichment(Observable):
    def add(self, identifier, partname, lxmlNode):
        summary = xpathFirst(lxmlNode, '/oai:record/oai:metadata/rdf:RDF')
        annotationUri, annotation = yield self.any.annotationFromSummary(summary)
        if annotation is None:
            yield self.all.delete(identifier=annotationUri)
        else:
            yield self.all.add(identifier=annotationUri, partname=ERFGEO_ENRICHMENT_PROFILE.prefix, lxmlNode=annotation)

    def delete(self, identifier):
        summaryUri = self._summaryUriFromOaiIdentifier(identifier)
        targetUri = SUMMARY_PROFILE.targetUriFrom(summaryUri)
        annotationUri = ERFGEO_ENRICHMENT_PROFILE.uriFor(targetUri)
        yield self.all.delete(identifier=annotationUri)

    def _summaryUriFromOaiIdentifier(self, identifier):
        if identifier.startswith(SUMMARY_DC_OAI_IDENTIFIER_PREFIX):
            return identifier[len(SUMMARY_DC_OAI_IDENTIFIER_PREFIX):]
        return identifier


SUMMARY_DC_OAI_IDENTIFIER_PREFIX = "oai:data.digitalecollectie.nl:"  # Note: unfortunately, rather brittle with respect to possible change of this prefix in the future.
