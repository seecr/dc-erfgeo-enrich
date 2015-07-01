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

from os.path import join

from seecr.test import SeecrTestCase

from digitalecollectie.erfgeo.repositorysetsselection import RepositorySetsSelection


class RepositorySetsSelectionTest(SeecrTestCase):
    def testSelectedSetSpecs(self):
        selectionPath = join(self.tempdir, 'subdir', 'repository_sets_selection.json')
        repositorySetsSelection = RepositorySetsSelection(selectionPath)
        self.assertEquals([], list(repositorySetsSelection.selectedSetSpecs()))

        repositorySetsSelection.addToSelection('kb')
        repositorySetsSelection.addToSelection('beng')
        repositorySetsSelection.addToSelection('nationaal_archief')
        repositorySetsSelection.addToSelection('open_beelden', 'beeldengeluid')
        self.assertEquals([('beng', '*'), ('kb', '*'), ('nationaal_archief', '*'), ('open_beelden', 'beeldengeluid')], list(repositorySetsSelection.selectedSetSpecs()))
        self.assertTrue(repositorySetsSelection.isSelected('kb'))
        self.assertTrue(repositorySetsSelection.isSelected('open_beelden', 'beeldengeluid'))
        self.assertFalse(repositorySetsSelection.isSelected('kb', 'aSet'))

        repositorySetsSelection = RepositorySetsSelection(selectionPath)
        self.assertEquals([('beng', '*'), ('kb', '*'), ('nationaal_archief', '*'), ('open_beelden', 'beeldengeluid')], list(repositorySetsSelection.selectedSetSpecs()))

        self.assertEquals([('open_beelden', 'beeldengeluid')], list(repositorySetsSelection.selectedSetSpecs('open_beelden')))

        self.assertEquals([('nationaal_archief', '*')], list(repositorySetsSelection.selectedSetSpecs('nationaal_archief')))
        self.assertEquals([], list(repositorySetsSelection.selectedSetSpecs('unknown_repository')))

        repositorySetsSelection.addToSelection('open_beelden', 'openimages')
        self.assertEqualsWS("""{
  "setsSelection": [
    {
      "repositoryId": "beng",
      "sets": [
        "*"
      ]
    },
    {
      "repositoryId": "kb",
      "sets": [
        "*"
      ]
    },
    {
      "repositoryId": "nationaal_archief",
      "sets": [
        "*"
      ]
    },
    {
      "repositoryId": "open_beelden",
      "sets": [
        "openimages",
        "beeldengeluid"
      ]
    }
  ]
}""", open(selectionPath).read())

        repositorySetsSelection.addToSelection('open_beelden')
        self.assertEqualsWS("""{
  "setsSelection": [
    {
      "repositoryId": "beng",
      "sets": [
        "*"
      ]
    },
    {
      "repositoryId": "kb",
      "sets": [
        "*"
      ]
    },
    {
      "repositoryId": "nationaal_archief",
      "sets": [
        "*"
      ]
    },
    {
      "repositoryId": "open_beelden",
      "sets": [
        "*"
      ]
    }
  ]
}""", open(selectionPath).read())

        repositorySetsSelection.addToSelection('open_beelden', 'xyz')
        self.assertEqualsWS("""{
  "setsSelection": [
    {
      "repositoryId": "beng",
      "sets": [
        "*"
      ]
    },
    {
      "repositoryId": "kb",
      "sets": [
        "*"
      ]
    },
    {
      "repositoryId": "nationaal_archief",
      "sets": [
        "*"
      ]
    },
    {
      "repositoryId": "open_beelden",
      "sets": [
        "*"
      ]
    }
  ]
}""", open(selectionPath).read())
