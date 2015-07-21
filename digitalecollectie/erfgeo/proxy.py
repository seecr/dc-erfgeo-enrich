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

from urllib import urlencode

from weightless.http import httpget
from meresco.core import Observable


class Proxy(Observable):
    def __init__(self, rewriteRequest, **kwargs):
        Observable.__init__(self, **kwargs)
        self._rewriteRequest = rewriteRequest

    def handleRequest(self, **kwargs):
        newKwargs = self._rewriteRequest(**kwargs)
        headers = newKwargs.get('Headers')
        host = newKwargs.get('host', 'localhost')
        port = newKwargs.get('port', 80)
        request = newKwargs.get('path', '/')
        arguments = newKwargs.get('arguments')
        if arguments:
            request += '?' + urlencode(arguments, doseq=True)
        result = yield httpget(host=host, port=port, request=request, headers=headers)
        yield result