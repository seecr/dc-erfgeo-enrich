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
# Copyright (C) 2016 Netherlands Institute for Sound and Vision http://instituut.beeldengeluid.nl/
# Copyright (C) 2016 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2016 Stichting DEN http://www.den.nl
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

from os.path import join, dirname

from seecr.test import SeecrTestCase

from digitalecollectie.erfgeo.erfgeoquery import ErfGeoQuery


testDataDir = join(dirname(__file__), 'data')


class ErfGeoQueryTest(SeecrTestCase):
    def testParseQueryResponse(self):
        egq = ErfGeoQuery()
        body = open(join(testDataDir, 'haarlem.response.json')).read()
        results = egq.parseQueryResponse(body)
        hgType, pits = results[0]
        self.assertEquals('hg:Municipality', hgType)
        self.assertEquals('http://rdf.histograph.io/atlas-verstedelijking/Haarlemmermeer-1950', pits[0]['@id'])
        self.assertEquals('http://rdf.histograph.io/militieregisters/2703', pits[1]['@id'])
        pitIds = [p['@id'] for p in pits]
        self.assertTrue('http://sws.geonames.org/2754999/' in pitIds, pitIds)
        self.assertTrue('http://www.gemeentegeschiedenis.nl/gemeentenaam/Haarlemmermeer' in pitIds, pitIds)
