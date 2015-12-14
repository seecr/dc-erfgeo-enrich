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
# Copyright (C) 2011-2012, 2014-2015 Netherlands Institute for Sound and Vision http://instituut.beeldengeluid.nl/
# Copyright (C) 2011-2012, 2014-2015 Seecr (Seek You Too B.V.) http://seecr.nl
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

from os import makedirs
from os.path import join, isdir

from weightless.core import be

from meresco.core import Transparent
from meresco.components import PeriodicDownload, Schedule, XmlParseLxml
from meresco.oai import OaiDownloadProcessor, UpdateAdapterFromOaiDownloadProcessor

from digitalecollectie.erfgeo.callstackdict import CallStackDict
from digitalecollectie.erfgeo.setsselection import WILDCARD
from digitalecollectie.erfgeo.annotationprofiles import SUMMARY_PROFILE


class InsideOutObservable(object):
    def __init__(self):
        self.internalObserverTreeRoot = Transparent()
        self.outside = Transparent()
        self.addObserver = self.outside.addObserver
        self.addStrand = self.outside.addStrand
        self.call = self.outside.call
        self.do = self.outside.do
        self.all = self.outside.all
        self.any = self.outside.any


class OaiSetsHarvester(InsideOutObservable):
    def __init__(self, reactor, hostName, portNumber, path, interval, workingDirectory, metadataPrefix=SUMMARY_PROFILE.prefix):
        InsideOutObservable.__init__(self)
        self._reactor = reactor
        self._hostName = hostName
        self._portNumber = portNumber
        self._path = path
        self._interval = interval
        self._workingDirectory = workingDirectory
        self._periodicDownloaders = {}
        self._metadataPrefix = metadataPrefix

        self._adaptToOutside = be(
            (UpdateAdapterFromOaiDownloadProcessor(),
                (self.outside,)
            )
        )

    def observer_init(self):
        yield self.outside.once.observer_init()
        for setSpec in self.call.selectedSetSpecs():
            self._addSetHarvest(setSpec)

    def handleShutdown(self):
        yield self.internalObserverTreeRoot.once.handleShutdown()

    def addSetHarvest(self, setSpec=WILDCARD):
        self.do.addToSelection(setSpec=setSpec)
        self._addSetHarvest(setSpec=setSpec)

    def _addSetHarvest(self, setSpec):
        if setSpec == WILDCARD:
            setSpec = None
        if WILDCARD in self._periodicDownloaders.keys():
            return
        setWorkingDirectory = join(self._workingDirectory, setSpec or '')
        isdir(setWorkingDirectory) or makedirs(setWorkingDirectory)
        self._periodicDownloaders[setSpec or WILDCARD] = periodicDownload = PeriodicDownload(
            reactor=self._reactor,
            host=self._hostName,
            port=self._portNumber,
            schedule=Schedule(period=self._interval)
        )
        setHarvestTree = be(
            (Transparent(name=setSpec or WILDCARD),
                (periodicDownload,
                    (XmlParseLxml(fromKwarg="data", toKwarg="lxmlNode"),
                        (OaiDownloadProcessor(
                                path=self._path,
                                metadataPrefix=self._metadataPrefix,
                                set=setSpec,
                                workingDirectory=setWorkingDirectory,
                                xWait=True),
                            (CallStackDict(dict(
                                    harvestedMetadataPrefix=lambda **kwargs: self._metadataPrefix,
                                    harvestedSet=lambda **kwargs: setSpec
                                )),
                                (self._adaptToOutside,)
                            )
                        )
                    )
                )
            )
        )
        self.internalObserverTreeRoot.addObserver(setHarvestTree)
        periodicDownload.observer_init()
