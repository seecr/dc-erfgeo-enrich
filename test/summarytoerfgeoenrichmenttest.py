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

from lxml.etree import XML, _Element

from seecr.test import SeecrTestCase, CallTrace

from weightless.core import consume, be
from meresco.core.observable import Observable

from digitalecollectie.erfgeo.summarytoerfgeoenrichment import SummaryToErfGeoEnrichment
from digitalecollectie.erfgeo.annotationprofiles import SUMMARY_PROFILE, ERFGEO_ENRICHMENT_PROFILE


class SummaryToErfGeoEnrichmentTest(SeecrTestCase):
    def testAdd(self):
        summaryToErfGeoEnrichment = SummaryToErfGeoEnrichment()

        def annotationFromSummary(summary):
            raise StopIteration(("uri:erfgeoannotation", XML(ERFGEO_ANNOTATION)))
            yield
        observer = CallTrace('observer', methods={'annotationFromSummary': annotationFromSummary})
        top = be(
            (Observable(),
                (summaryToErfGeoEnrichment,
                    (observer,)
                )
            )
        )
        consume(top.all.add(identifier='uri:ignored', partname='record', lxmlNode=XML(INPUT)))
        self.assertEquals(['annotationFromSummary', 'add'], observer.calledMethodNames())
        addKwargs = observer.calledMethods[1].kwargs
        self.assertEquals('uri:erfgeoannotation', addKwargs['identifier'])
        self.assertEquals('erfGeoEnrichment', addKwargs['partname'])
        self.assertEquals(_Element, type(addKwargs['lxmlNode']))
        self.assertXmlEquals(ERFGEO_ANNOTATION, addKwargs['lxmlNode'])

    def testNoAnnotationMeansDelete(self):
        # should never happen now that 'annotationFromSummary' always results in an Annotation, even to indicate no match could be made.
        summaryToErfGeoEnrichment = SummaryToErfGeoEnrichment()

        def annotationFromSummary(summary):
            raise StopIteration(("uri:erfgeoannotation", None))
            yield
        observer = CallTrace('observer', methods={'annotationFromSummary': annotationFromSummary})
        top = be(
            (Observable(),
                (summaryToErfGeoEnrichment,
                    (observer,)
                )
            )
        )
        consume(top.all.add(identifier='uri:ignored', partname='record', lxmlNode=XML(INPUT)))
        self.assertEquals(['annotationFromSummary', 'delete'], observer.calledMethodNames())
        self.assertEquals({'identifier': 'uri:erfgeoannotation'}, observer.calledMethods[1].kwargs)

    def testDelete(self):
        summaryToErfGeoEnrichment = SummaryToErfGeoEnrichment()
        observer = CallTrace('observer')
        top = be(
            (Observable(),
                (summaryToErfGeoEnrichment,
                    (observer,)
                )
            )
        )
        targetUri = 'target:uri'
        consume(top.all.delete(identifier=SUMMARY_PROFILE.uriFor(targetUri)))
        self.assertEquals(['delete'], observer.calledMethodNames())
        self.assertEquals(ERFGEO_ENRICHMENT_PROFILE.uriFor(targetUri), observer.calledMethods[0].kwargs['identifier'])


INPUT = """<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
    <oa:Annotation xmlns:oa="http://www.w3.org/ns/oa#">
        <oa:hasTarget rdf:resource="uri:target"/>
        <oa:hasBody>
        </oa:hasBody>
    </oa:Annotation>
</rdf:RDF>"""

ERFGEO_ANNOTATION = """<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:oa="http://www.w3.org/ns/oa#">
    <oa:Annotation>
        <oa:hasTarget rdf:resource="uri:target"/>
        <oa:hasBody>
        </oa:hasBody>
    </oa:Annotation>
</rdf:RDF>"""
