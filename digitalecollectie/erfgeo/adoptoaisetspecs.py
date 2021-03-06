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
# Copyright (C) 2011-2012, 2015 Netherlands Institute for Sound and Vision http://instituut.beeldengeluid.nl/
# Copyright (C) 2011-2012, 2015 Seecr (Seek You Too B.V.) http://seecr.nl
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

from functools import partial

from urllib import quote

from meresco.core import Observable

from digitalecollectie.erfgeo.callstackdict import callStackDictGet


class AdoptOaiSetSpecs(Observable):
    def __init__(self, newSetSpecsFromOriginals=None, name=None):
        Observable.__init__(self, name=name)
        newSetSpecsFromOriginals = newSetSpecsFromOriginals or (lambda x: x)
        self._newSetSpecsFromOriginals = newSetSpecsFromOriginals

    def addOaiRecord(self, identifier, setSpecs, metadataPrefixes):
        callStackSetSpecs = callStackDictGet('setSpecs')
        self.do.addOaiRecord(
            identifier=identifier,
            setSpecs=setSpecs + list(self._newSetSpecsFromOriginals(callStackSetSpecs)),
            metadataPrefixes=metadataPrefixes
        )


def prefixWithValueFromCallStackDict(setSpecs, key):
    value = callStackDictGet(key)
    yield setSpecEscape(value)
    for setSpec in setSpecs:
        yield setSpecEscape("%s:%s" % (value, setSpec))

def setSpecEscape(value):
    return quote(value, safe=':')

prefixWithRepositoryGroupId = partial(
    prefixWithValueFromCallStackDict,
    key='repositoryGroupId'
)

prefixWithCollection = partial(
    prefixWithValueFromCallStackDict,
    key='collection')
