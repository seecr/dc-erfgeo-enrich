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
