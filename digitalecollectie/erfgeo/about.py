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
from cgi import escape as htmlEscape

from weightless.http import httpget
from meresco.core import Observable

from meresco.components.http import utils as httputils
from meresco.components.http.utils import CRLF

from digitalecollectie.erfgeo.annotationprofiles import ERFGEO_ENRICHMENT_PROFILE


class About(Observable):
    def __init__(self, digitaleCollectieHost=None, digitaleCollectiePort=None, digitaleCollectieApiKey=None):
        Observable.__init__(self)
        self._digitaleCollectieHost = digitaleCollectieHost
        self._digitaleCollectiePort = digitaleCollectiePort
        self._digitaleCollectieApiKey = digitaleCollectieApiKey

    def handleRequest(self, arguments, **kwargs):
        uri = arguments.get('uri', [None])[0]
        if not uri:
            yield badRequest("'uri' query parameter missing.")
            return
        profile = arguments.get('profile', [ERFGEO_ENRICHMENT_PROFILE.prefix])[0]

        try:
            data = yield self.about(uri=uri, profile=profile)
        except ValueError, e:
            yield badRequest(str(e))
            return
        except KeyError:
            yield badRequest("profile '%s' not found for uri '%s'." % (profile, uri))
            return

        yield 'HTTP/1.0 200 OK' + CRLF
        yield 'Content-Type: application/xml' + CRLF
        yield CRLF
        yield data

    def about(self, uri, profile):
        if profile == ERFGEO_ENRICHMENT_PROFILE.prefix:
            data = self.call.getData(identifier=ERFGEO_ENRICHMENT_PROFILE.uriFor(uri), name=profile)
        else:
            arguments = {'uri': [uri], 'profile': [profile]}
            if self._digitaleCollectieApiKey:
                arguments['apikey'] = [self._digitaleCollectieApiKey]
            result = yield httpget(host=self._digitaleCollectieHost, port=self._digitaleCollectiePort, request='/about?' + urlencode(arguments, doseq=True))
            header, body = result.split(2 * CRLF, 1)
            if not 'HTTP/1.0 200' in header:
                raise ValueError(body)
            data = body
        raise StopIteration(data)


def badRequest(message):
    yield httputils.badRequestHtml
    yield '<!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML 2.0//EN">\n'
    yield "<html><head>\n"
    yield "<title>400 Bad Request</title>\n"
    yield "</head><body>\n"
    yield "<h1>Not Found</h1>\n"
    yield "<!-- %s -->\n" % htmlEscape(str(message))
    yield "</body></html>\n"
