from sys import stdout

from os import getenv
from os.path import join, dirname, abspath

from weightless.core import compose, be
from weightless.io import Reactor

from meresco.core import Observable
from meresco.core.processtools import setSignalHandlers, registerShutdownHandler

from meresco.components import readConfig, XmlXPath, XmlParseLxml, FilterMessages, PeriodicDownload
from meresco.components.http import BasicHttpHandler, ObservableHttpServer, PathFilter, StringServer
from meresco.components.http.utils import ContentTypePlainText
from meresco.components.log import LogCollector, ApacheLogWriter, HandleRequestLog, LogComponent

from meresco.oai import OaiDownloadProcessor, UpdateAdapterFromOaiDownloadProcessor

def initJVM():
    vmargs = []
    maxheap = getenv('PYLUCENE_MAXHEAP')
    heapDumpPath = getenv('PYLUCENE_HEAPDUMP_PATH')
    if heapDumpPath:
        vmargs.extend(['-XX:+HeapDumpOnOutOfMemoryError', '-XX:HeapDumpPath=%s' % heapDumpPath])
    from lucene import initVM
    try:
        initVM(maxheap=maxheap, vmargs=','.join(vmargs))
    except ValueError:
        pass
initJVM()

from meresco.lucene import LuceneSettings, Lucene, CqlToLuceneQuery, TermNumerator
from meresco.lucene.fieldregistry import FieldRegistry
from meresco.lucene.remote import LuceneRemoteService

from digitalecollectie.erfgeo import VERSION_STRING
from digitalecollectie.erfgeo.namespaces import namespaces
from digitalecollectie.erfgeo.maybecombinewithsummary import COMBINED_METADATA_PREFIX

from digitalecollectie.erfgeo.index.constants import ALL_FIELD
from digitalecollectie.erfgeo.index.lxmltofieldslist import LxmlToFieldsList
from digitalecollectie.erfgeo.index.fieldslisttolucenedocument import FieldsListToLuceneDocument
from digitalecollectie.erfgeo.index.summaryfields import SummaryFields


workingPath = dirname(abspath(__file__))

unqualifiedTermFields = [(ALL_FIELD, 1.0)]

fieldRegistry = FieldRegistry(drilldownFields=SummaryFields.drilldownFields)
untokenizedFieldnames = [df.name for df in SummaryFields.drilldownFields]

parseHugeOptions = dict(huge_tree=True, remove_blank_text=True)


def createErfGeoEnrichmentPeriodicDownloadHelix(reactor, lucene, config, statePath):
    erfgeoEnrichPortNumber = int(config['erfgeoEnrich.portNumber'])
    downloadName = 'erfgeoEnrich-%s' % COMBINED_METADATA_PREFIX
    erfGeoEnrichPeriodicDownload = PeriodicDownload(
        reactor,
        host='127.0.0.1',
        port=erfgeoEnrichPortNumber,
        name=downloadName,
        autoStart=True)

    erfGeoEnrichOaiDownload = OaiDownloadProcessor(
        path='/oai',
        metadataPrefix=COMBINED_METADATA_PREFIX,
        workingDirectory=join(statePath, 'harvesterstate/' + downloadName),
        xWait=True,
        name=downloadName,
        autoCommit=True)

    termNumerator = TermNumerator(join(statePath, 'keys-termnumerator'))

    return \
        (erfGeoEnrichPeriodicDownload,
            (XmlParseLxml(fromKwarg="data", toKwarg="lxmlNode", parseOptions=parseHugeOptions),
                (erfGeoEnrichOaiDownload,
                    (UpdateAdapterFromOaiDownloadProcessor(),
                        (FilterMessages(allowed=['delete']),
                            (lucene,),
                        ),
                        (FilterMessages(allowed=['add']),
                            (XmlXPath(['/oai:record/oai:metadata/rdf:RDF'], namespaces=namespaces, fromKwarg='lxmlNode'),
                                (LxmlToFieldsList(),
                                    (FieldsListToLuceneDocument(fieldRegistry, SummaryFields),
                                        # TODO: index geo coordinates from WKT
                                        (lucene,),
                                        (termNumerator,),
                                    )
                                )
                            )
                        )
                    )
                )
            )
        )


def dna(reactor, config, statePath):
    portNumber = int(config['erfgeoEnrich.index.portNumber'])
    indexCommitTimeout = config.get('debug.global.index.commitTimeout', 10)

    luceneSettings = LuceneSettings(
        fieldRegistry=fieldRegistry,
        commitTimeout=indexCommitTimeout,
        readonly=False,
    )

    lucene = Lucene(
        join(statePath, 'lucene'),
        reactor=reactor,
        settings=luceneSettings,
        name='erfGeoEnriched'
    )
    erfGeoEnrichmentPeriodicDownloadHelix = createErfGeoEnrichmentPeriodicDownloadHelix(reactor, lucene, config, statePath=statePath)

    observableHttpServer = ObservableHttpServer(reactor, portNumber, prio=1)

    return \
        (Observable(),
            (observableHttpServer,
                (LogCollector(),
                    (ApacheLogWriter(stdout),),
                    (HandleRequestLog(),
                        (BasicHttpHandler(),
                            (PathFilter('/lucene'),
                                (LuceneRemoteService(reactor=reactor),
                                    (CqlToLuceneQuery(unqualifiedFields=unqualifiedTermFields, luceneSettings=luceneSettings),
                                        (lucene,),
                                    ),
                                )
                            ),
                            (PathFilter('/info/version'),
                                (StringServer(VERSION_STRING, ContentTypePlainText),)
                            ),
                        )
                    )
                )
            ),
            erfGeoEnrichmentPeriodicDownloadHelix,
        )

def startServer(configFile, stateDir):
    setSignalHandlers()

    config = readConfig(configFile)
    statePath = abspath(stateDir)

    reactor = Reactor()
    server = be(dna(reactor, config=config, statePath=statePath))
    list(compose(server.once.observer_init()))
    registerShutdownHandler(statePath=statePath, server=server, reactor=reactor)

    print "Server listening on port", config['erfgeoEnrich.index.portNumber']
    print "   - local state:", statePath

    stdout.flush()
    reactor.loop()
