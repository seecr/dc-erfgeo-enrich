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

from digitalecollectie.erfgeo.index.dateparse import parseYears


class DateParseTest(SeecrTestCase):
    def testParseYears(self):
        self.assertEquals([2000], parseYears("2000-01-01"))
        self.assertEquals([2000], parseYears("2000-01-01T01:01:01Z"))
        self.assertEquals([2000], parseYears("2000-01"))
        self.assertEquals([2000], parseYears("2000"))
        self.assertEquals([2000, 2001, 2002, 2003, 2004], parseYears("2000 - 2004"))
        self.assertEquals([2000, 2001, 2002, 2003, 2004], parseYears("2000-2004"))
        self.assertEquals([2000], parseYears("2000 - ..."))
        self.assertEquals([2000], parseYears("2000-..."))
        self.assertEquals([2001], parseYears("[2001]"))
        self.assertEquals([2000], parseYears("01-01-2000"))
        self.assertEquals([2000], parseYears("[ca. 2000]"))
        self.assertEquals([2000, 2001, 2002, 2003, 2004], parseYears("ca. 2000 - ca. 2004"))
        self.assertEquals([2000], parseYears("cop. 2000"))
        self.assertEquals([1940, 1941, 1942, 1943, 1944, 1945, 1946, 1947, 1948, 1949], parseYears("194X"))
        self.assertEquals(range(1940, 1970), parseYears("194X - 196x"))
        self.assertEquals([], parseYears("20e eeuw"))
        self.assertEquals(range(1900, 2000), parseYears("19X"))

