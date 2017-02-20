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

from os.path import isdir, join, abspath, dirname, basename
from os import listdir, makedirs
from shutil import rmtree
from random import choice
from StringIO import StringIO

from lxml.etree import parse

from meresco.components import readConfig
from meresco.components.http import utils as httputils

from mockserver import MockServer

from seecr.test.integrationtestcase import IntegrationState
from seecr.test.portnumbergenerator import PortNumberGenerator
from seecr.test.utils import postRequest, sleepWheel

from digitalecollectie.erfgeo.namespaces import xpathFirst


mydir = dirname(abspath(__file__))
projectDir = dirname(dirname(mydir))
documentationDir = join(projectDir, "doc")


class ErfGeoIntegrationState(IntegrationState):
    def __init__(self, stateName, tests=None, fastMode=False):
        IntegrationState.__init__(self, stateName, tests=tests, fastMode=fastMode)
        self.JAVA_BIN = "/usr/lib/jvm/java-1.8.0/bin"
        self.testdataDir = join(mydir, 'data')

        self.digitaleCollectiePort = PortNumberGenerator.next()

        self.erfGeoEnrichmentPort = PortNumberGenerator.next()
        self.erfGeoEnrichmentLocalStatePath = join(self.integrationTempdir, 'erfGeoEnrichmentLocal')

        self.erfGeoEnrichmentIndexPort = PortNumberGenerator.next()
        self.erfGeoEnrichmentIndexLocalStatePath = join(self.integrationTempdir, 'erfGeoEnrichmentIndexLocal')
        self.lucenePort = PortNumberGenerator.next()
        self.luceneDir = join(self.integrationTempdir, 'erfGeoEnrichmentIndex-lucene')
        self.numeratePort = PortNumberGenerator.next()
        self.numerateDir = join(self.integrationTempdir, 'erfGeoEnrichmentIndex-numerate')

        erfGeoRepositorySetsSelectionFile = join(self.erfGeoEnrichmentLocalStatePath, 'erfgeo_dc_sets.json')
        if not self.fastMode:
            clearOrCreateDir(self.erfGeoEnrichmentLocalStatePath)
            open(erfGeoRepositorySetsSelectionFile, 'w').write(ERFGEO_SETS_SELECTION_JSON)

        self.erfGeoApiPort = PortNumberGenerator.next()

        self.globalStatePath = join(self.integrationTempdir, 'global')

        self.saharaGetPort = PortNumberGenerator.next()

        self.config = config = readConfig(join(documentationDir, 'examples', 'dc-erfgeo-enrich.config'))

        # test example config has necessary parameters
        def setConfig(config, parameter, value):
            assert config.get(parameter), "key '%s' should only be given a value if it is already declared in source config %s." % (parameter, config)
            print "config[%s] = %s" % (repr(parameter), repr(value))
            config[parameter] = value

        setConfig(config, 'erfgeoEnrich.portNumber', self.erfGeoEnrichmentPort)
        setConfig(config, 'erfgeoEnrich.index.portNumber', self.erfGeoEnrichmentIndexPort)
        setConfig(config, 'erfgeoEnrich.index.lucenePortNumber', self.lucenePort)
        setConfig(config, 'erfgeoEnrich.index.numeratePortNumber', self.numeratePort)
        setConfig(config, 'digitaleCollectie.host', 'localhost')
        setConfig(config, 'digitaleCollectie.port', self.digitaleCollectiePort)
        setConfig(config, 'erfgeo.searchApiBaseUrl', 'http://localhost:%s' % self.erfGeoApiPort)

        config['global.apacheLogStream'] = 'disabled'
        config['global.debug.periodicdownload.period'] = '0.1'

        self.configFile = join(self.integrationTempdir, 'erfgeo.config')
        with open(self.configFile, 'w') as f:
            for item in config.items():
                f.write('%s = %s\n' % item)

    def binDir(self, executable=None):
        binDir = join(projectDir, 'bin')
        if not isdir(binDir):
            binDir = '/usr/bin'
        result = binDir if executable is None else join(binDir, executable)
        return result

    def setUp(self):
        self._startMockErfGeoApi()
        self._startMockDigitaleCollectie()
        self._startErfGeoEnrichmentServer()
        self.startNumerateServer()
        self.startLuceneServer()
        self._startErfGeoEnrichmentIndexServer()
        self._createDatabase()

    def tearDown(self):
        IntegrationState.tearDown(self)
        self.mockErfGeoApi.halt = True

    def _startMockDigitaleCollectie(self):
        self._startServer(
            serviceName='DigitaleCollectie-mock',
            executable=join(mydir, 'testutils/start-mockdc'),
            serviceReadyUrl='http://localhost:%s/ready' % self.digitaleCollectiePort,
            port=self.digitaleCollectiePort,
            dataDir=join(self.testdataDir, 'dc_summaries')
        )

    def _startErfGeoEnrichmentServer(self):
        self._startServer(
            serviceName='erfGeoEnrichment',
            executable=self.binDir('erfgeo-enrichment-server'),
            serviceReadyUrl='http://localhost:%s/info/version' % self.erfGeoEnrichmentPort,
            stateDir=self.erfGeoEnrichmentLocalStatePath,
            configFile=self.configFile)

    def startNumerateServer(self):
        self._startServer(
            serviceName='numerate',
            executable=self.binPath('start-uri-numerate-server'),
            serviceReadyUrl='http://localhost:%s/ready' % self.numeratePort,
            port=self.numeratePort,
            stateDir=self.numerateDir,
            waitForStart=True,
            args=['-Xmx1G'])

    def startLuceneServer(self):
        self._startServer(
            serviceName='lucene',
            executable=self.binPath('start-lucene-server'),
            serviceReadyUrl='http://localhost:%s/info/version' % self.lucenePort,
            port=self.lucenePort,
            stateDir=self.luceneDir,
            waitForStart=True,
            core=['erfGeoEnriched'],
            args=['-Xmx1G'],
            env=dict(JAVA_BIN=self.JAVA_BIN, LANG="en_US.UTF-8"))

    def _startErfGeoEnrichmentIndexServer(self):
        self._startServer(
            serviceName='erfGeoEnrichmentIndex',
            executable=self.binDir('erfgeo-enrichment-index-server'),
            serviceReadyUrl='http://localhost:%s/info/version' % self.erfGeoEnrichmentIndexPort,
            stateDir=self.erfGeoEnrichmentIndexLocalStatePath,
            configFile=self.configFile)

    def _startMockErfGeoApi(self):
        def makeResponse(request):
            for key, value in [
                ('%22Verenigde+Staten%22', 'soestdijk'),
                ('%22Leunseweg%22%2C+%22Leunen%22%2C+%22Venray%22', 'leunseweg-leunen-venray'),
                ('GET', 'utrecht')
            ]:
                if key in request:
                    return httputils.okHtml + open(join(self.testdataDir, 'api.erfgeo.nl/%s.response.json' % value)).read()
        self.mockErfGeoApi = MockServer(self.erfGeoApiPort)
        self.mockErfGeoApi.makeResponse = makeResponse
        self.mockErfGeoApi.start()

    def _createDatabase(self):
        if self.fastMode:
            print "Reusing database in", self.integrationTempdir
            return
        print "Creating database in", self.integrationTempdir
        sleepWheel(28)  # give ErfGeoEnrichment service etc. some time to process and commit

    def _uploadUpdateRequests(self, datadir, uploadPath, uploadPorts, filter=None):
        requests = (join(datadir, r) for r in sorted(listdir(datadir)) if r.endswith('.updateRequest'))
        for filename in requests:
            if filter is None or filter(filename):
                self._uploadUpdateRequest(filename, uploadPath, uploadPorts)

    def _uploadUpdateRequest(self, filename, uploadPath, uploadPorts):
        aPort = choice(uploadPorts)
        print 'http://localhost:%s%s' % (aPort, uploadPath), '<-', basename(filename)[:-len('.updateRequest')]
        updateRequest = open(filename).read()
        lxml = parse(StringIO(updateRequest))
        uploadIdentifier = xpathFirst(lxml, '//ucp:recordIdentifier/text()')
        self.uploaded.append((uploadIdentifier, updateRequest))
        header, body = postRequest(aPort, uploadPath, updateRequest, parse=False, timeOutInSeconds=18.0)
        if '200' not in header.split('\r\n', 1)[0]:
            print 'No 200 response, but:\n', header
            exit(123)
        if "srw:diagnostics" in body:
            print body
            exit(1234)

    def stopServer(self, *args, **kwargs):
        self._stopServer(*args, **kwargs)


ERFGEO_SETS_SELECTION_JSON = """\
[
    "NIOD",
    "limburgs_erfgoed",
    "zeeuwse_bibliotheek",
    "geluidVanNl"
]"""


def clearOrCreateDir(d):
    if isdir(d):
        rmtree(d)
    makedirs(d)
