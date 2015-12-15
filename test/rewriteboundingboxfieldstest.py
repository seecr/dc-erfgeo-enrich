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


from seecr.test import SeecrTestCase

from cqlparser import cqlToExpression
from meresco.components import CqlMultiSearchClauseConversion

from digitalecollectie.erfgeo.rewriteboundingboxfields import RewriteBoundingBoxFields


class RewriteBoundingBoxFieldsTest(SeecrTestCase):
    def testNothingToBeDone(self):
        self.assertEquals(cqlToExpression('field=value'), self.convert('field=value'))

    def testRewrite(self):
        self.assertEquals(cqlToExpression('dcterms:spatial.geo:lat > 1.23'), self.convert('minGeoLat=1.23'))
        self.assertEquals(cqlToExpression('dcterms:spatial.geo:lat < 7.23'), self.convert('maxGeoLat = 7.23'))
        self.assertEquals(cqlToExpression('dcterms:spatial.geo:long > 50.23'), self.convert('minGeoLong=50.23'))
        self.assertEquals(cqlToExpression('dcterms:spatial.geo:long < 52.23'), self.convert('maxGeoLong = 52.23'))

    def convert(self, cqlString):
        converter = CqlMultiSearchClauseConversion([
            RewriteBoundingBoxFields().filterAndModifier()
        ], fromKwarg="query")
        query = cqlToExpression(cqlString)
        return converter._convert(query=query)
