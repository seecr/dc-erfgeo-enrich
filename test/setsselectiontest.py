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

from os.path import join

from seecr.test import SeecrTestCase

from digitalecollectie.erfgeo.setsselection import SetsSelection, WILDCARD


class SetsSelectionTest(SeecrTestCase):
    def testSelectedSetSpecs(self):
        selectionPath = join(self.tempdir, 'subdir', 'repository_sets_selection.json')
        setsSelection = SetsSelection(selectionPath)
        self.assertEquals([], list(setsSelection.selectedSetSpecs()))

        setsSelection.addToSelection('kb')
        setsSelection.addToSelection('beng')
        setsSelection.addToSelection('nationaal_archief')
        setsSelection.addToSelection('open_beelden:beeldengeluid')
        self.assertEquals(['beng', 'kb', 'nationaal_archief', 'open_beelden:beeldengeluid'], list(setsSelection.selectedSetSpecs()))
        self.assertTrue(setsSelection.isSelected('kb'))
        self.assertTrue(setsSelection.isSelected('open_beelden:beeldengeluid'))

        setsSelection = SetsSelection(selectionPath)
        self.assertEquals(['beng', 'kb', 'nationaal_archief', 'open_beelden:beeldengeluid'], list(setsSelection.selectedSetSpecs()))

        setsSelection.addToSelection('open_beelden:openimages')
        self.assertEqualsWS("""[
  "beng",
  "kb",
  "nationaal_archief",
  "open_beelden:beeldengeluid",
  "open_beelden:openimages"
]""", open(selectionPath).read())

        setsSelection.addToSelection('open_beelden')
        self.assertEqualsWS("""[
  "beng",
  "kb",
  "nationaal_archief",
  "open_beelden",
  "open_beelden:beeldengeluid",
  "open_beelden:openimages"
]""", open(selectionPath).read())

    def testWildcard(self):
        selectionPath = join(self.tempdir, 'subdir', 'repository_sets_selection.json')
        setsSelection = SetsSelection(selectionPath)
        self.assertFalse(setsSelection.isSelected('abc'))
        self.assertEquals([], list(setsSelection.selectedSetSpecs()))
        setsSelection.addToSelection(WILDCARD)
        self.assertEquals([WILDCARD], list(setsSelection.selectedSetSpecs()))
        self.assertTrue(setsSelection.isSelected('abc'))

    def testWildcardKeepsSpecificSelectionsForPriorityHarvesting(self):
        selectionPath = join(self.tempdir, 'subdir', 'repository_sets_selection.json')
        setsSelection = SetsSelection(selectionPath)
        self.assertFalse(setsSelection.isSelected('abc'))
        setsSelection.addToSelection('abc')
        setsSelection.addToSelection(WILDCARD)
        setsSelection.addToSelection('def')
        self.assertEquals([WILDCARD, 'abc', 'def'], list(setsSelection.selectedSetSpecs()))
        self.assertTrue(setsSelection.isSelected('abc'))
        self.assertTrue(setsSelection.isSelected('xyz'))
