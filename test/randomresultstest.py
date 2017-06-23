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
# Copyright (C) 2017 Netherlands Institute for Sound and Vision http://instituut.beeldengeluid.nl/
# Copyright (C) 2017 Seecr (Seek You Too B.V.) http://seecr.nl
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

from seecr.test import SeecrTestCase, CallTrace

from weightless.core import be, retval
from meresco.core import Observable

from digitalecollectie.erfgeo.randomresults import RandomResults


class RandomResultsTest(SeecrTestCase):
    def setUp(self):
        SeecrTestCase.setUp(self)
        self.randomResults = RandomResults()
        def executeQuery(maximumRecords=10, **kwargs):
            self.response = CallTrace('response')
            self.response.hits = range(maximumRecords)
            raise StopIteration(self.response)
            yield
        self.observer = CallTrace('observer', methods={'executeQuery': executeQuery})
        self.top = be(
            (Observable(),
                (self.randomResults,
                    (self.observer,),
                )
            )
        )

    def testNoRandom(self):
        result = retval(self.top.any.executeQuery(query='q', extraArguments={}, otherKwarg='value'))
        self.assertEquals(['executeQuery'], self.observer.calledMethodNames())
        self.assertEquals(dict(query='q', extraArguments={}, otherKwarg='value'), self.observer.calledMethods[0].kwargs)
        self.assertEquals(10, len(result.hits))
        self.assertEquals(range(10), result.hits)

    def testRandom(self):
        self.randomResults._sample = lambda population, k: population[::-len(population)/k]
        result = retval(self.top.any.executeQuery(query='q', extraArguments={'x-random': ['True']}, otherKwarg='value'))
        self.assertEquals(['executeQuery'], self.observer.calledMethodNames())
        self.assertEquals(dict(query='q', extraArguments={'x-random': ['True']}, maximumRecords=1000, otherKwarg='value'), self.observer.calledMethods[0].kwargs)
        self.assertEquals([999, 899, 799, 699, 599, 499, 399, 299, 199, 99], result.hits)