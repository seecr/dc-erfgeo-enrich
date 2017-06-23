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

from random import sample

from meresco.core import Observable


class RandomResults(Observable):
    def executeQuery(self, **kwargs):
        extraArguments = kwargs.get('extraArguments', {})
        random = ('true' == extraArguments.get('x-random', ['false'])[0].lower())
        if random:
            maxRecords = kwargs.get('maximumRecords', 10)
            kwargs['maximumRecords'] = maxRecords * RETRIEVE_EXTRA_FACTOR
        response = yield self.any.executeQuery(**kwargs)
        if random:
            if len(response.hits) >= maxRecords:
                response.hits = self._sample(response.hits, maxRecords)
        raise StopIteration(response)

    def _sample(self, population, k):
        return sample(population, k)


RETRIEVE_EXTRA_FACTOR = 100
