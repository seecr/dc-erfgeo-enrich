#!/usr/bin/env python
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

from random import sample
from urllib2 import urlopen

from simplejson import load


def selectSomeRecords(baseUrl):
    total = determineTotal(baseUrl)
    print 'total', total
    sampleSize = 400
    s = sample(xrange(total), sampleSize)
    print s
    numberWithLocation = 0
    numberOfMatches = 0
    matchesForReview = {}
    for i in s:
        record = getRecord(baseUrl, i)
        id = record['@id']
        print 'id', id
        originalLocations, spatialMatches = splitLocations(record)
        if originalLocations:
            numberWithLocation += 1
            print 'original locations', originalLocations
        assert len(spatialMatches) < 2, spatialMatches
        if spatialMatches:
            match = spatialMatches[0]
            print '  match', match['@id'], match['rdfs:label'], match['@type']
            numberOfMatches += 1
            matchesForReview[id] = (originalLocations, match)

    print '*******'
    print 'total size|%s' % total
    print 'sample size|%s' % sampleSize
    print 'number with location|%s|%s%%' % (numberWithLocation, 100.0 * numberWithLocation / sampleSize)
    print 'number of matches|%s|%s%%' % (numberOfMatches, 100.0 * numberOfMatches / sampleSize)
    print ''
    print 'id|original|matchLabel|matchType'
    for id, (originalLocations, match) in matchesForReview.iteritems():
        original = ', '.join(str(o) for o in originalLocations)
        print "%s|%s|%s|%s" % (id, original, match['rdfs:label'][0], match['@type'])


def splitLocations(record):
    spatialMatches = []
    originalLocations = record.get('dc:coverage', [])
    for s in record.get('dcterms:spatial', []):
        if isinstance(s, basestring):
            originalLocations.append(s)
            continue
        uri = s['@id']
        if '/gtaa/' in uri:
            originalLocations.append((uri, s['skos:prefLabel']))
            continue
        if uri.startswith('geo:'):
            continue
        spatialMatches.append(s)
    return originalLocations, spatialMatches

def determineTotal(baseUrl):
    result = load(urlopen(baseUrl + '?query=*'))
    return result['result']['total']

def getRecord(baseUrl, i):
    result = load(urlopen(baseUrl + '?query=*&startRecord=%s&maximumRecords=1' % (i+1)))
    item = result['result']['items'][0]
    # print item
    return item



if __name__ == '__main__':
    baseUrl = 'http://erfgeo.data.digitalecollectie.nl/search'
    selectSomeRecords(baseUrl)

