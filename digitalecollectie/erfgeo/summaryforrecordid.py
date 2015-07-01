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

from urllib import urlencode

from lxml.etree import XML

from weightless.http import httpget
from meresco.core import Observable

from digitalecollectie.erfgeo.namespaces import xpathFirst


class SummaryForRecordId(Observable):
    def __init__(self, digitaleCollectieHost='127.0.0.1', digitaleCollectiePort=None, **kwargs):
        Observable.__init__(self, **kwargs)
        self._digitaleCollectieHost = digitaleCollectieHost
        self._digitaleCollectiePort = int(digitaleCollectiePort) if digitaleCollectiePort else digitaleCollectiePort

    def retrieveSummaryForRecordId(self, recordId):
        if not self._digitaleCollectieHost or not self._digitaleCollectiePort:
            raise StopIteration(None)
        response = yield httpget(
            host=self._digitaleCollectieHost,
            port=self._digitaleCollectiePort,
            request='/about?%s' % urlencode({
                'uri': recordId,
                'profile': 'summary'
            })
        )
        header, body = response.split('\r\n\r\n', 1)
        lxmlNode = xpathFirst(XML(body), '/rdf:RDF')
        raise StopIteration(lxmlNode)
