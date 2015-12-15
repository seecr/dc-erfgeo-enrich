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

from os import remove
from os.path import join

from lxml.etree import tostring

from seecr.test import SeecrTestCase, CallTrace

from weightless.core import consume

from digitalecollectie.erfgeo.oaisetsharvester import OaiSetsHarvester
from digitalecollectie.erfgeo.setsselection import SetsSelection, WILDCARD

from callstackdicttest import CallStackDictMonitor


class OaiSetsHarvesterTest(SeecrTestCase):
    def setUp(self):
        SeecrTestCase.setUp(self)
        self._setsSelectionFilepath = join(self.tempdir, 'sets_selection.json')
        open(self._setsSelectionFilepath, 'w').write(SETS_SELECTION_JSON)
        self._setsSelection = SetsSelection(self._setsSelectionFilepath)

    def testOaiSetsHarvester(self):
        reactorStub = CallTrace('reactor')
        oaiSetsHarvester = OaiSetsHarvester(
            reactor=reactorStub,
            hostName='localhost',
            portNumber=80,
            path='/oai',
            interval=0.1,
            workingDirectory=join(self.tempdir, 'harvest'),
        )
        oaiSetsHarvester.addObserver(self._setsSelection)
        observer = CallTrace('observer', emptyGeneratorMethods=['add'])
        oaiSetsHarvester.addObserver(observer)
        callStackDictMonitor = CallStackDictMonitor()
        oaiSetsHarvester.addObserver(callStackDictMonitor)

        self.assertEquals(
            set([]),
            set([o._name for o in oaiSetsHarvester.internalObserverTreeRoot._observers])
        )
        self.assertEquals([], reactorStub.calledMethods)
        consume(oaiSetsHarvester.observer_init())
        self.assertEquals(
            set(['kb', 'beng', 'nationaal_archief', 'open_beelden:beeldengeluid']),
            set([o._name for o in oaiSetsHarvester.internalObserverTreeRoot._observers])
        )
        self.assertEquals(4 * ['addTimer'], [m.name for m in reactorStub.calledMethods])

        bengPeriodicDownload = oaiSetsHarvester._periodicDownloaders['beng']
        consume(bengPeriodicDownload.all.handle(data=LISTRECORDS_RESPONSE))

        self.assertEquals(['observer_init', 'add', 'add'], [m.name for m in observer.calledMethods])
        addCalls = observer.calledMethods[1:]
        self.assertEquals(['collect:20000001', 'collect:20000002'], [m.kwargs['identifier'] for m in addCalls])
        self.assertEquals(['record', 'record'], [m.kwargs['partname'] for m in addCalls])
        self.assertEqualsWS(
            """<record xmlns="http://www.openarchives.org/OAI/2.0/">
                    <header>
                        <identifier>collect:20000001</identifier>
                        <datestamp>2011-11-08T12:48:34Z</datestamp>
                    </header>
                    <metadata>
                        <oai_dc:dc xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/">
                            <dc:description xmlns:dc="http://purl.org/dc/elements/1.1/">Exterieur, overzicht voorgevel pand Vrouwenverband</dc:description>
                        </oai_dc:dc>
                    </metadata>
               </record>""",
            tostring(addCalls[0].kwargs['lxmlNode'])
        )
        self.assertEquals([{'harvestedSet': 'beng', 'harvestedMetadataPrefix': 'summary'}, {'harvestedSet': 'beng', 'harvestedMetadataPrefix': 'summary'}], callStackDictMonitor.dicts)

    def testAddSetHarvester(self):
        remove(self._setsSelectionFilepath)
        setsSelection = SetsSelection(self._setsSelectionFilepath)

        reactorStub = CallTrace('reactor')
        oaiSetsHarvester = OaiSetsHarvester(
            reactor=reactorStub,
            hostName='localhost',
            portNumber=80,
            path='/oai',
            interval=0.1,
            workingDirectory=join(self.tempdir, 'harvest'),
        )
        oaiSetsHarvester.addObserver(setsSelection)
        self.assertEquals("""[]""", open(self._setsSelectionFilepath).read())
        observer = CallTrace('observer', emptyGeneratorMethods=['add'])
        oaiSetsHarvester.addObserver(observer)

        self.assertEquals(0, len(oaiSetsHarvester.internalObserverTreeRoot._observers))
        self.assertEquals([], reactorStub.calledMethods)
        self.assertEquals([], observer.calledMethods)

        consume(oaiSetsHarvester.observer_init())
        self.assertEquals([], reactorStub.calledMethods)
        self.assertEquals(['observer_init'], [m.name for m in observer.calledMethods])

        oaiSetsHarvester.addSetHarvest('beng')
        oaiSetsHarvester.addSetHarvest('open_beelden:beeldengeluid')
        self.assertEquals(
            set(['beng', 'open_beelden:beeldengeluid']),
            set([o._name for o in oaiSetsHarvester.internalObserverTreeRoot._observers])
        )
        self.assertEquals(['addTimer', 'addTimer'], [m.name for m in reactorStub.calledMethods])

        bengPeriodicDownload = oaiSetsHarvester._periodicDownloaders['beng']
        consume(bengPeriodicDownload.all.handle(data=LISTRECORDS_RESPONSE))

        self.assertEquals(['observer_init', 'addToSelection', 'addToSelection', 'add', 'add'], [m.name for m in observer.calledMethods])

    def testAddSetHarvesterWildcard(self):
        remove(self._setsSelectionFilepath)
        setsSelection = SetsSelection(self._setsSelectionFilepath)

        reactorStub = CallTrace('reactor')
        oaiSetsHarvester = OaiSetsHarvester(
            reactor=reactorStub,
            hostName='localhost',
            portNumber=80,
            path='/oai',
            interval=0.1,
            workingDirectory=join(self.tempdir, 'harvest'),
        )
        oaiSetsHarvester.addObserver(setsSelection)
        observer = CallTrace('observer', emptyGeneratorMethods=['add'])
        oaiSetsHarvester.addObserver(observer)
        consume(oaiSetsHarvester.observer_init())

        oaiSetsHarvester.addSetHarvest(WILDCARD)
        oaiSetsHarvester.addSetHarvest('open_beelden:beeldengeluid')
        self.assertEquals(
            set([WILDCARD, 'open_beelden:beeldengeluid']),
            set([o._name for o in oaiSetsHarvester.internalObserverTreeRoot._observers])
        )
        self.assertEquals(['addTimer', 'addTimer'], [m.name for m in reactorStub.calledMethods])

        thePeriodicDownload = oaiSetsHarvester._periodicDownloaders[WILDCARD]
        consume(thePeriodicDownload.all.handle(data=LISTRECORDS_RESPONSE))
        self.assertEquals(['observer_init', 'addToSelection', 'addToSelection', 'add', 'add'], [m.name for m in observer.calledMethods])

    def testAddSetHarvesterPersistent(self):
        reactorStub = CallTrace('reactor')
        oaiSetsHarvester = OaiSetsHarvester(
            reactor=reactorStub,
            hostName='localhost',
            portNumber=80,
            path='/oai',
            interval=0.1,
            workingDirectory=join(self.tempdir, 'harvest'),
        )
        oaiSetsHarvester.addObserver(self._setsSelection)
        consume(oaiSetsHarvester.observer_init())

        oaiSetsHarvester.addSetHarvest('rce')
        self.assertEquals(
            set(['kb', 'beng', 'nationaal_archief', 'open_beelden:beeldengeluid', 'rce']),
            set([o._name for o in oaiSetsHarvester.internalObserverTreeRoot._observers])
        )
        self.assertEquals(5 * ['addTimer'], [m.name for m in reactorStub.calledMethods])
        self.assertEqualsWS("""[
  "beng",
  "kb",
  "nationaal_archief",
  "open_beelden:beeldengeluid",
  "rce"
]""", open(self._setsSelectionFilepath).read())

        reactorStub.calledMethods.reset()
        oaiSetsHarvester = OaiSetsHarvester(
            reactor=reactorStub,
            hostName='localhost',
            portNumber=80,
            path='/oai',
            interval=0.1,
            workingDirectory = join(self.tempdir, 'harvest'),
        )
        oaiSetsHarvester.addObserver(SetsSelection(self._setsSelectionFilepath))
        self.assertEquals([], [m.name for m in reactorStub.calledMethods])
        consume(oaiSetsHarvester.observer_init())
        self.assertEquals(
            set(['kb', 'open_beelden:beeldengeluid', 'rce', 'beng', 'nationaal_archief']),
            set([o._name for o in oaiSetsHarvester.internalObserverTreeRoot._observers])
        )
        self.assertEquals(5 * ['addTimer'], [m.name for m in reactorStub.calledMethods])


LISTRECORDS_RESPONSE = """\
<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/">
    <responseDate>2011-11-25T09:39:45Z</responseDate>
    <request verb="ListRecords" metadataPrefix="oai_dc">http://cultureelerfgoed.adlibsoft.com/oaiapi/oai.ashx</request>
    <ListRecords>
        <record>
            <header>
                <identifier>collect:20000001</identifier>
                <datestamp>2011-11-08T12:48:34Z</datestamp>
            </header>
            <metadata>
                <oai_dc:dc xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/">
                    <dc:description xmlns:dc="http://purl.org/dc/elements/1.1/">Exterieur, overzicht voorgevel pand Vrouwenverband</dc:description>
                </oai_dc:dc>
            </metadata>
        </record>
        <record>
            <header>
                <identifier>collect:20000002</identifier>
                <datestamp>2011-09-09T12:40:52Z</datestamp>
            </header>
            <metadata>
                <oai_dc:dc xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/">
                    <dc:description xmlns:dc="http://purl.org/dc/elements/1.1/">Exterieur, overzicht Administratiegebouw, voorgevel Binnengasthuisstraat 9 , kleine gebouw links/midden is wachtkamer/apotheek</dc:description>
                </oai_dc:dc>
            </metadata>
        </record>
    </ListRecords>
</OAI-PMH>"""

LISTIDENTIFIERS_RESPONSE = """\
<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/">
    <responseDate>2011-11-25T09:39:45Z</responseDate>
    <request verb="ListRecords" metadataPrefix="oai_dc">http://cultureelerfgoed.adlibsoft.com/oaiapi/oai.ashx</request>
    <ListIdentifiers>
        <header>
            <identifier>collect:20000001</identifier>
            <datestamp>2011-11-08T12:48:34Z</datestamp>
        </header>
        <header>
            <identifier>collect:20000002</identifier>
            <datestamp>2011-09-09T12:40:52Z</datestamp>
        </header>
    </ListIdentifiers>
</OAI-PMH>"""

SETS_SELECTION_JSON = """\
[
    "kb",
    "beng",
    "nationaal_archief",
    "open_beelden:beeldengeluid"
]"""
