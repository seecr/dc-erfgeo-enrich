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

from re import compile


def parseYears(value):
    if not value:
        return
    value = value.lower().replace(' ', '')
    value = value.replace('ca.', '')
    value = value.replace('cop.', '')
    for yearRe in YEAR_REGEXES:
        match = yearRe.match(value)
        if match:
            years = _expandYearPattern(match.group('year'))
            years2 = years
            if 'year_to' in yearRe.pattern:
                years2 = _expandYearPattern(match.group('year_to'))
            return range(min(years), max(years2) + 1)
    return []


def _expandYearPattern(year):
    numberOfX = year.count('x')
    if numberOfX:
        numberOfX = numberOfX + (4 - len(year))
        year = year.replace('xx', 'x')
    return [
        int(year.replace('x', ("{0:0%s}" % numberOfX).format(i)))
        for i in range(10 ** numberOfX)
    ]


YEAR_X = '\d{2}(\d(\d|x)|xx?)' # 194X, #18XX, #18X

YEAR_REGEXES = [
    compile(r)
    for r in [
        r'^(?P<year>%s)$' % YEAR_X, #2000
        r'^\[(?P<year>%s)\]$' % YEAR_X, #[2000]
        r'^(?P<year>%s)-(?P<year_to>%s)$' % (YEAR_X, YEAR_X), #2000-2010
        r'^(?P<year>%s)-...$' % YEAR_X, #2000-...
        r'^(?P<year>\d{4})-\d{2}(-\d{2}(t\d{2}:\d{2}(:\d{2})?z?)?)?$', #2000-01-01
        r'^\d{2}-\d{2}-(?P<year>\d{4})$', #01-01-2000
    ]
]
