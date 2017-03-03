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

from os import getenv
from os.path import join, dirname, abspath

from weightless.core import compose, be
from weightless.io import Reactor
from weightless.http import HttpRequest1_1, SocketPool, HttpRequestAdapter

from meresco.core import Observable
from meresco.core.processtools import setSignalHandlers, registerShutdownHandler

from meresco.components import readConfig, XmlXPath, XmlParseLxml, FilterMessages, PeriodicDownload
from meresco.components.http import BasicHttpHandler, ObservableHttpServer, PathFilter, StringServer
from meresco.components.http.utils import ContentTypePlainText
from meresco.components.log import LogCollector, ApacheLogWriter, HandleRequestLog, LogComponent

from meresco.oai import OaiDownloadProcessor, UpdateAdapterFromOaiDownloadProcessor

from meresco.lucene import LuceneSettings, Lucene, LuceneSettings, Fields2LuceneDoc, KEY_PREFIX, FieldsListToLuceneDocument
from meresco.lucene.adaptertolucenequery import AdapterToLuceneQuery
from meresco.lucene.fieldregistry import FieldRegistry, DOUBLEFIELD
from meresco.lucene.queryexpressiontolucenequerydict import QueryExpressionToLuceneQueryDict
from meresco.lucene.remote import LuceneRemoteService

from digitalecollectie.erfgeo import VERSION_STRING
from digitalecollectie.erfgeo.namespaces import namespaces
from digitalecollectie.erfgeo.maybecombinewithsummary import COMBINED_METADATA_PREFIX

from digitalecollectie.erfgeo.index.constants import ALL_FIELD
from digitalecollectie.erfgeo.index.lxmltofieldslist import LxmlToFieldsList
from digitalecollectie.erfgeo.index.indexfields import IndexFields
from digitalecollectie.erfgeo.index.termnumerate import TermNumerate


workingPath = dirname(abspath(__file__))

unqualifiedTermFields = [(ALL_FIELD, 1.0)]

fieldRegistry = FieldRegistry(drilldownFields=IndexFields.drilldownFields)
fieldRegistry.register('dcterms:spatial.geo:long', fieldDefinition=DOUBLEFIELD)
fieldRegistry.register('dcterms:spatial.geo:lat', fieldDefinition=DOUBLEFIELD)

parseHugeOptions = dict(huge_tree=True, remove_blank_text=True)

erfGeoEnrichedCoreName = 'erfGeoEnriched'


def createErfGeoEnrichmentPeriodicDownloadHelix(reactor, lucene, config, statePath, termNumerate):
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
                                    (FieldsListToLuceneDocument(fieldRegistry, IndexFields.untokenizedFieldnames, IndexFields),
                                        (lucene,),
                                        (termNumerate,),
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
    lucenePortNumber = int(config['erfgeoEnrich.index.lucenePortNumber'])

    indexCommitTimeout = config.get('debug.global.index.commitTimeout', 10)

    luceneSettings = LuceneSettings(
        fieldRegistry=fieldRegistry,
        commitTimeout=indexCommitTimeout,
        readonly=False,
    )

    http11Request = be(
        (HttpRequest1_1(),
            (SocketPool(reactor=reactor, unusedTimeout=5, limits=dict(totalSize=100, destinationSize=10)),
            ),
        )
    )

    http11RequestAdapter = be(
        (HttpRequestAdapter(),
            (http11Request,),
        )
    )

    termNumerate = be((TermNumerate(host='localhost', port=lucenePortNumber),
        (http11RequestAdapter,)
    ))

    lucene = be(
        (Lucene(
                host='localhost',
                port=lucenePortNumber,
                reactor=reactor,
                settings=luceneSettings,
                name=erfGeoEnrichedCoreName),
            (http11Request,),
        )
    )
    erfGeoEnrichmentPeriodicDownloadHelix = createErfGeoEnrichmentPeriodicDownloadHelix(reactor, lucene, config, statePath=statePath, termNumerate=termNumerate)

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
                                    (FilterMessages(allowed=['fieldnames', 'drilldownFieldnames']),
                                        (lucene,),
                                    ),
                                    (FilterMessages(allowed=['executeQuery']),
                                        (AdapterToLuceneQuery(
                                            defaultCore=erfGeoEnrichedCoreName,
                                            coreConverters={
                                                erfGeoEnrichedCoreName: QueryExpressionToLuceneQueryDict(unqualifiedTermFields=unqualifiedTermFields, luceneSettings=luceneSettings)
                                            }),
                                            (lucene,),
                                        ),
                                    )
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
