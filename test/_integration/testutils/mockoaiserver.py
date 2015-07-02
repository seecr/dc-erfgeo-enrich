#!/usr/bin/env python
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
# Copyright (C) 2012-2015 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2012-2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
# Copyright (C) 2015 Koninklijke Bibliotheek (KB) http://www.kb.nl
# Copyright (C) 2015 Netherlands Institute for Sound and Vision http://instituut.beeldengeluid.nl/
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
from os.path import join

from tempfile import mkdtemp
from shutil import rmtree
from time import sleep

from escaping import escapeFilename

from weightless.core import compose, be
from weightless.io import Reactor

from meresco.core import Observable
from meresco.core.processtools import setSignalHandlers, registerShutdownHandler

from meresco.components.log import LogComponent
from meresco.components.http import ObservableHttpServer, PathFilter, StringServer
from meresco.components.http.utils import ContentTypePlainText
from meresco.oai import OaiJazz, OaiPmh
from meresco.oai.oaijazz import DEFAULT_BATCH_SIZE


def iterOaiData(dataDir):
    for line in open(join(dataDir, 'oai.ids')):
        action, filename, setSpecsRaw = line.strip().split(' ', 2)
        yield action, filename, [setSpec for setSpec in setSpecsRaw.split('|') if setSpec.strip()]

def allSets(dataDir):
    return set(setSpec for _,_,setSpecs in iterOaiData(dataDir) for setSpec in setSpecs)

def dna(reactor, portNumber, dataDirs, tempDir, batchSize):
    print 'DATADIRS', dataDirs
    oaiJazz = OaiJazz(tempDir)
    oaiJazzOperations = {
        'ADD': oaiJazz.addOaiRecord,
        'DEL': oaiJazz.deleteOaiRecord
    }
    storage = DataStorage()
    for dataDir in dataDirs:
        for action, filename, setSpecs in iterOaiData(dataDir):
            identifier, metadataPrefix = filename.rsplit('.', 1)
            oaiJazzOperations[action](
                identifier=identifier,
                setSpecs=setSpecs,
                metadataPrefixes=[metadataPrefix],
            )
            storage.addFile(filename, join(dataDir, escapeFilename(filename)))
            sleep(0.000001)
    oaiJazz.commit()

    return \
        (Observable(),
            (ObservableHttpServer(reactor, portNumber),
                (PathFilter('/', excluding=['/ready']),
                    (IllegalFromFix(),
                        (OaiPmh(repositoryName='Mock', adminEmail='no@example.org', supportXWait=True, batchSize=batchSize),
                            (LogComponent('OaiPmh'),),
                            (oaiJazz,),
                            (storage,),
                        )
                    )
                ),
                (PathFilter("/ready"),
                    (StringServer('yes', ContentTypePlainText),)
                )
            )
        )


class IllegalFromFix(Observable):
    def handleRequest(self, arguments, **kwargs):
        if 'from' in arguments:
            f = arguments['from']
            arguments['from'] = ['1970-01-01'] if f == ['0000'] else f
        yield self.all.handleRequest(arguments=arguments, **kwargs)


class DataStorage(object):
    def __init__(self):
        self.filepathFor = {}

    def addFile(self, filename, filepath):
        self.filepathFor[filename] = filepath

    def getData(self, identifier, name):
        yield open(self.filepathFor.get('%s.%s' % (identifier, name))).read()


def startServer(port, dataDir, dataDirFirst=None, dataDirLast=None, batchSize=None):
    batchSize = batchSize or DEFAULT_BATCH_SIZE
    setSignalHandlers()
    tempDir = mkdtemp(prefix='mockoai-')
    try:
        reactor = Reactor()
        server = be(dna(reactor, port, dataDirs=[d for d in [dataDirFirst, dataDir, dataDirLast] if d], tempDir=tempDir, batchSize=batchSize))
        print 'Ready to rumble the mock plein server at', port
        list(compose(server.once.observer_init()))
        registerShutdownHandler(statePath=tempDir, server=server, reactor=reactor)
        stdout.flush()
        reactor.loop()
    finally:
        rmtree(tempDir)
