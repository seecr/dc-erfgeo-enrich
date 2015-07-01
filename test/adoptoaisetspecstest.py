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

from unittest import TestCase
from seecr.test import CallTrace

from meresco.core import Observable

from digitalecollectie.erfgeo.adoptoaisetspecs import AdoptOaiSetSpecs, prefixWithRepositoryGroupId, prefixWithCollection


class AdoptOaiSetSpecsTest(TestCase):
    def testPrefixSetWithRepositoryGroupId(self):
        observable = Observable()
        adoptOaiSetSpecs = AdoptOaiSetSpecs(newSetSpecsFromOriginals=prefixWithRepositoryGroupId)
        observer = CallTrace('observer')
        observable.addObserver(adoptOaiSetSpecs)
        adoptOaiSetSpecs.addObserver(observer)

        __callstack_dict__ = {
            'repositoryGroupId': 'x:y%z',
            'setSpecs': ['set1', 'set2']
        }

        observable.do.addOaiRecord(
            identifier='identifier',
            sets=[('aSet', 'aSet')],
            metadataFormats=[('ese', '', 'http://www.europeana.eu/schemas/ese/')]
        )
        self.assertEquals(['addOaiRecord'], [m.name for m in observer.calledMethods])
        self.assertEquals(
            {
                'identifier': 'identifier',
                'metadataFormats': [('ese', '', 'http://www.europeana.eu/schemas/ese/')],
                'sets': [('aSet', 'aSet'), ('x:y%25z', 'x:y%25z'), ('x:y%25z:set1', 'x:y%25z:set1'), ('x:y%25z:set2', 'x:y%25z:set2')]
            },
            observer.calledMethods[0].kwargs
        )

    def testPrefixSetWithCollection(self):
        observable = Observable()
        adoptOaiSetSpecs = AdoptOaiSetSpecs(newSetSpecsFromOriginals=prefixWithCollection)
        observer = CallTrace('observer')
        observable.addObserver(adoptOaiSetSpecs)
        adoptOaiSetSpecs.addObserver(observer)

        __callstack_dict__ = {
            'collection': 'collection1',
            'setSpecs': ['set1']
        }

        observable.do.addOaiRecord(
            identifier='identifier',
            sets=[('aSet', 'aSet')],
            metadataFormats=[('ese', '', 'http://www.europeana.eu/schemas/ese/')]
        )
        self.assertEquals(['addOaiRecord'], [m.name for m in observer.calledMethods])
        self.assertEquals(
            {
                'identifier': 'identifier',
                'metadataFormats': [('ese', '', 'http://www.europeana.eu/schemas/ese/')],
                'sets': [('aSet', 'aSet'), ('collection1', 'collection1'), ('collection1:set1', 'collection1:set1')]
            },
            observer.calledMethods[0].kwargs
        )

    def testSetAsIs(self):
        observable = Observable()
        adoptOaiSetSpecs = AdoptOaiSetSpecs()
        observer = CallTrace('observer')
        observable.addObserver(adoptOaiSetSpecs)
        adoptOaiSetSpecs.addObserver(observer)

        __callstack_dict__ = {
            'repositoryGroupId': 'x:y%z',
            'collection': 'collection1',
            'setSpecs': ['set1']
        }

        observable.do.addOaiRecord(
            identifier='identifier',
            sets=[('aSet', 'aSet')],
            metadataFormats=[('ese', '', 'http://www.europeana.eu/schemas/ese/')]
        )
        self.assertEquals(['addOaiRecord'], [m.name for m in observer.calledMethods])
        self.assertEquals(
            {
                'identifier': 'identifier',
                'metadataFormats': [('ese', '', 'http://www.europeana.eu/schemas/ese/')],
                'sets': [('aSet', 'aSet'), ('set1', 'set1')]
            },
            observer.calledMethods[0].kwargs
        )

