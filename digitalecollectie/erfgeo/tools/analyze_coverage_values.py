#!/usr/bin/env python2.6
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

from os.path import dirname
from seecrdeps import includeParentAndDeps  #DO_NOT_DISTRIBUTE
includeParentAndDeps(dirname(dirname(__file__)))  #DO_NOT_DISTRIBUTE

from collections import defaultdict

from simplejson import dump

from meresco.oai.tools import iterateOaiPmh

from natag.erfgeo.namespaces import xpath, xpathFirst


def main():
    for set in ['NIOD', 'zeeuwse_bibliotheek', 'limburgs_erfgoed', 'geluidVanNl']:
        print 'set', set
        from sys import stdout; stdout.flush()
        setValues = defaultdict(int)
        for i, item in enumerate(iterateOaiPmh(baseurl="http://data.digitalecollectie.nl/oai", metadataPrefix='summary', set=set)):
            annotationBody = xpathFirst(item.metadata, 'oa:Annotation/oa:hasBody/*')
            coverageValues = xpath(annotationBody, 'dc:coverage/text()') + xpath(annotationBody, 'dcterms:spatial/text()')
            for value in coverageValues:
                print '[%s %s]: %s' % (set, i, value)
                from sys import stdout; stdout.flush()
                setValues[value] += 1

        print 'set', set
        print 'number of different values', len(setValues)
        print 'highest counts:'
        print sorted(setValues.items(), key=lambda (k, v): v, reverse=True)[:20]
        from sys import stdout; stdout.flush()

        with open("/home/natag/digitalecollectie_%s_coverage_values.json" % set, "w") as f:
            dump(setValues, f, indent=4, item_sort_key=lambda (k, v): -v if type(v) == int else k)


if __name__ == '__main__':
    main()