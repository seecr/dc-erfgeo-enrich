#!/usr/bin/env python2.6
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
# Copyright (C) 2015-2016 Netherlands Institute for Sound and Vision http://instituut.beeldengeluid.nl/
# Copyright (C) 2015-2016 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2015-2016 Stichting DEN http://www.den.nl
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

from os import system
from sys import path
from unittest import main

system('find .. -name "*.pyc" | xargs rm -f')
from glob import glob
for dir in glob('../deps.d/*'):
    path.insert(0, dir)
path.insert(0, "..")

from adoptoaisetspecstest import AdoptOaiSetSpecsTest
from callstackdicttest import CallStackDictTest
from erfgeoenrichmentfromsummarytest import ErfGeoEnrichmentFromSummaryTest
from erfgeoquerytest import ErfGeoQueryTest
from oaisetsharvestertest import OaiSetsHarvesterTest
from pittoannotationtest import PitToAnnotationTest
from rewriteboundingboxfieldstest import RewriteBoundingBoxFieldsTest
from searchjsonresponsetest import SearchJsonResponseTest
from setsselectiontest import SetsSelectionTest
from summarytoerfgeoenrichmenttest import SummaryToErfGeoEnrichmentTest
from unprefixidentifiertest import UnprefixIdentifierTest
from geometrytest import GeometryTest

from index.fieldslisttolucenedocumenttest import FieldsListToLuceneDocumentTest
from index.lxmltofieldslisttest import LxmlToFieldsListTest
from index.dateparsetest import DateParseTest


if __name__ == '__main__':
    main()
