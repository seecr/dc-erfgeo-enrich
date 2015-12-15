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

from sys import stdout
from shutil import rmtree
from tempfile import mkdtemp

from weightless.core import consume, be
from weightless.io import Reactor

from meresco.core import Observable
from meresco.components.http import ObservableHttpServer, PathFilter, StringServer
from meresco.components.http.utils import ContentTypePlainText, CRLF
from meresco.core.processtools import setSignalHandlers, registerShutdownHandler
from meresco.oai.oaijazz import DEFAULT_BATCH_SIZE

from test._integration.testutils.mockoaiserver import DataStorage, prepareOaiPmh

from digitalecollectie.erfgeo.annotationprofiles import SUMMARY_PROFILE


def dna(reactor, portNumber, oaiPmh, storage):
    return \
        (Observable(),
            (ObservableHttpServer(reactor, portNumber),
                (PathFilter('/', excluding=['/ready', '/about']),
                    (oaiPmh,)
                ),
                (PathFilter('/about'),
                    (MockAbout(),
                        (storage,),
                    )
                ),
                (PathFilter("/ready"),
                    (StringServer('yes', ContentTypePlainText),)
                )
            )
        )

class MockAbout(Observable):
    def handleRequest(self, arguments, **kwargs):
        uri = arguments['uri'][0]
        summaryUri = SUMMARY_PROFILE.uriFor(uri)
        print 'uri', uri, 'summaryUri', summaryUri
        from sys import stdout; stdout.flush()
        data = self.call.getData(identifier=summaryUri, name=SUMMARY_PROFILE.prefix)
        yield 'HTTP/1.0 200 OK' + CRLF
        yield 'Content-Type: application/xml' + CRLF
        yield CRLF
        yield data


def startServer(port, dataDir, dataDirFirst=None, dataDirLast=None, batchSize=None):
    batchSize = batchSize or DEFAULT_BATCH_SIZE
    setSignalHandlers()
    tempDir = mkdtemp(prefix='mockoai-')
    storage = DataStorage()
    try:
        reactor = Reactor()
        oaiPmh = prepareOaiPmh(dataDirs=[d for d in [dataDirFirst, dataDir, dataDirLast] if d], tempDir=tempDir, storage=storage, batchSize=batchSize)
        server = be(dna(reactor, port, oaiPmh, storage))
        print 'Ready to rumble the mock plein server at', port
        consume(server.once.observer_init())
        registerShutdownHandler(statePath=tempDir, server=server, reactor=reactor)
        stdout.flush()
        reactor.loop()
    finally:
        rmtree(tempDir)
