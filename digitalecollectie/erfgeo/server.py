# -*- coding: utf-8 -*-
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
from os.path import join, dirname, abspath, isfile
from socket import gethostname, gethostbyname

from weightless.core import be, consume
from weightless.io import Reactor

from meresco.core import Observable, Transparent
from meresco.core.processtools import setSignalHandlers, registerShutdownHandler
from meresco.components import readConfig, FilterMessages, XmlPrintLxml, lxmltostring
from meresco.components.http import ObservableHttpServer, PathFilter, FileServer, PathRename, ApacheLogger, StringServer, Deproxy
from meresco.components.http.utils import ContentTypePlainText
from meresco.components.log import LogComponent
from meresco.oai import OaiJazz, OaiPmh, OaiAddRecordWithDefaults
from meresco.sequentialstore import MultiSequentialStorage, AddDeleteToMultiSequential
from meresco.html import DynamicHtml

from digitalecollectie.erfgeo import VERSION_STRING
from digitalecollectie.erfgeo.about import About
from digitalecollectie.erfgeo.adoptoaisetspecs import AdoptOaiSetSpecs
from digitalecollectie.erfgeo.callstackdict import CallStackDict
from digitalecollectie.erfgeo.erfgeoenrichmentfromsummary import ErfGeoEnrichmentFromSummary
from digitalecollectie.erfgeo.erfgeoquery import ErfGeoQuery
from digitalecollectie.erfgeo.namespaces import xpath, namespaces
from digitalecollectie.erfgeo.oaisetsharvester import OaiSetsHarvester
from digitalecollectie.erfgeo.pittoannotation import PitToAnnotation
from digitalecollectie.erfgeo.repositorysetsselection import RepositorySetsSelection
from digitalecollectie.erfgeo.summaryforrecordid import SummaryForRecordId
from digitalecollectie.erfgeo.summarytoerfgeoenrichment import SummaryToErfGeoEnrichment
from digitalecollectie.erfgeo.utils import getitem


workingPath = dirname(abspath(__file__))

htmlPath = join(workingPath, 'html')
dynamicHtmlFilePath = join(htmlPath, 'dynamic')
staticHtmlFilePath = join(htmlPath, 'static')

IP_ADDRESS = gethostbyname(gethostname())

def staticFileExists(filepath):
    if '/..' in filepath:
        return False
    return isfile(staticHtmlFilePath + filepath)

additionalGlobals = {
    'getitem': getitem,
    'lxmltostring': lxmltostring,
    'staticFileExists': staticFileExists,
}

ERFGEO_ANNOTATION_METADATA_FORMAT = ('erfGeoEnrichment', '', namespaces.rdf)

def createUploadHelix(oaiJazz, storage, erfGeoEnrichmentFromSummary):
    return \
        (Transparent(),
            (FilterMessages(allowed=['delete']),
                (SummaryToErfGeoEnrichment(),
                    (oaiJazz,),
                    (AddDeleteToMultiSequential(),
                        (storage,),
                    )
                )
            ),
            (FilterMessages(allowed=['add']),
                (CallStackDict({
                    'setSpecs':
                    lambda lxmlNode, **kwargs: \
                        set(xpath(lxmlNode, "oai:header/oai:setSpec/text()"))}),
                    (SummaryToErfGeoEnrichment(),
                        (erfGeoEnrichmentFromSummary,),
                        (XmlPrintLxml(fromKwarg='lxmlNode', toKwarg='data'),
                            (AddDeleteToMultiSequential(),
                                (storage,),
                            )
                        ),
                        (OaiAddRecordWithDefaults(metadataFormats=lambda **kwargs: [ERFGEO_ANNOTATION_METADATA_FORMAT]),
                            (AdoptOaiSetSpecs(),
                                (oaiJazz,)
                            )
                        ),
                    )
                )
            )
        )

class SeecrOaiWatermark(object):
    def oaiWatermark(self):
        yield r"""
<!-- Crafted by Seecr, http://seecr.nl -->
"""


def dna(reactor, config, statePath, out=stdout):
    digitaleCollectieHost = config.get('digitaleCollectie.host', '127.0.0.1')
    digitaleCollectiePort = int(config['digitaleCollectie.port'])
    additionalGlobals['port'] = portNumber = int(config['portNumber'])
    searchApiBaseUrl = config.get('erfgeo.searchApiBaseUrl', 'https://api.histograph.io/search')

    erfGeoRepositorySetsSelection = RepositorySetsSelection(join(statePath, 'erfgeo_repository_sets.json'))

    oaiRepositoryName = config['oaiRepositoryName']
    oaiAdminEmail = config['oaiAdminEmail']
    oaiPath = join(statePath, 'oai')
    periodicdownload_period = float(config.get('global.debug.periodicdownload.period', 0.5))

    observableHttpServer = ObservableHttpServer(reactor, portNumber, prio=1)

    oaiJazz = OaiJazz(oaiPath)
    erfGeoEnrichmentStorage = MultiSequentialStorage(join(statePath, 'storage'))

    oaiSetsHarvester = OaiSetsHarvester(
        reactor=reactor,
        hostName=digitaleCollectieHost,
        portNumber=digitaleCollectiePort,
        path='/oai',
        interval=periodicdownload_period,
        workingDirectory=join(statePath, 'harvest')
    )

    erfGeoEnrichmentFromSummary = be(
        (ErfGeoEnrichmentFromSummary(),
            (ErfGeoQuery(searchApiBaseUrl=searchApiBaseUrl),),
            (PitToAnnotation(searchApiBaseUrl=searchApiBaseUrl),),
        )
    )

    uploadHelix = createUploadHelix(
        oaiJazz=oaiJazz,
        storage=erfGeoEnrichmentStorage,
        erfGeoEnrichmentFromSummary=erfGeoEnrichmentFromSummary,
    )

    return \
        (Observable(),
            (oaiSetsHarvester,
                (erfGeoRepositorySetsSelection,),
                uploadHelix
            ),
            (observableHttpServer,
                (Deproxy(deproxyForIps=['127.0.0.1', IP_ADDRESS]),
                    (ApacheLogger(out),
                        (PathFilter('/about'),
                            (About(digitaleCollectieHost=digitaleCollectieHost, digitaleCollectiePort=digitaleCollectiePort),
                                (erfGeoEnrichmentStorage,)
                            )
                        ),
                        (PathFilter('/oai'),
                            (OaiPmh(
                                    repositoryName=oaiRepositoryName,
                                    adminEmail=oaiAdminEmail),
                                (SeecrOaiWatermark(),),
                                (oaiJazz,),
                                (erfGeoEnrichmentStorage,),
                            )
                        ),
                        (PathFilter('/static'),
                            (PathRename(lambda path: path[len('/static'):]),
                                (FileServer(staticHtmlFilePath),)
                            )
                        ),
                        (PathFilter('/info/version'),
                            (StringServer(VERSION_STRING, ContentTypePlainText),)
                        ),
                        (PathFilter('/', excluding=['/about', '/static', '/info', '/oai']),
                            (DynamicHtml([dynamicHtmlFilePath], reactor=reactor, indexPage='/index', additionalGlobals=additionalGlobals),
                                (SummaryForRecordId(digitaleCollectieHost=digitaleCollectieHost, digitaleCollectiePort=digitaleCollectiePort),),
                                (erfGeoEnrichmentFromSummary,)
                            ),
                        )
                    )
                )
            )
        )

def startServer(configFile, stateDir):
    setSignalHandlers()
    statePath = abspath(stateDir)
    config = readConfig(configFile)
    reactor = Reactor()

    server = be(dna(reactor=reactor, config=config, statePath=statePath))
    consume(server.once.observer_init())
    registerShutdownHandler(statePath=statePath, server=server, reactor=reactor)

    print "Server listening on port", config['portNumber']
    print "   - local state:", statePath
    stdout.flush()
    reactor.loop()
