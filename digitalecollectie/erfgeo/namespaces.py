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

from functools import partial

from meresco.xml import namespaces as _namespaces
from meresco.xml.utils import createElement, createSubElement


namespaces = _namespaces.copyUpdate(dict(
    dcoa="http://data.digitalecollectie.nl/ns/oa#",
    geo="http://www.w3.org/2003/01/geo/wgs84_pos#",
    geos="http://www.opengis.net/ont/geosparql#",
    hg="http://schema.histograph.io/#",
    oa="http://www.w3.org/ns/oa#",
    vcard="http://www.w3.org/2006/vcard/ns#",
))

def uriFromTag(tag):
    return namespaces.expandNsUri(namespaces.prefixedTag(tag))
namespaces.uriFromTag = uriFromTag

xpath = namespaces.xpath
xpathFirst = namespaces.xpathFirst
expandNsUri = namespaces.expandNsUri
expandNsTag = namespaces.expandNsTag
curieToUri = namespaces.curieToUri
uriToCurie = namespaces.uriToCurie
curieToTag = namespaces.curieToTag
tagToCurie = namespaces.tagToCurie

createElement = partial(createElement, namespaces=namespaces)
createSubElement = partial(createSubElement, namespaces=namespaces)
