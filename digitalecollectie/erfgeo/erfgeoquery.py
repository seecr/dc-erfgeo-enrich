#!/usr/bin/env python2.6
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

from decimal import Decimal
from time import time

from urllib import urlencode

from lxml.etree import XML
from simplejson import loads

from weightless.io.utils import asProcess
from weightless.http import httpget

from meresco.core import Observable
from meresco.components import lxmltostring, parseAbsoluteUrl

from digitalecollectie.erfgeo.utils import getitem
from digitalecollectie.erfgeo.geometry import Geometry


class ErfGeoQuery(Observable):
    def __init__(self, searchApiBaseUrl='https://api.erfgeo.nl/search', **kwargs):
        Observable.__init__(self, **kwargs)
        parsedUrl = parseAbsoluteUrl(searchApiBaseUrl)
        self._host = parsedUrl.host
        self._port = parsedUrl.port
        self._path = parsedUrl.path
        self._ssl = (parsedUrl.scheme == 'https')

    def queryErfGeoApi(self, s, expectedType=None):
        queryDict = dict(q=s)
        if not expectedType is None:
            queryDict['type'] = expectedType
        response = yield httpget(host=self._host, port=self._port, request=self._path + '?' + urlencode(queryDict), ssl=self._ssl)
        header, body = response.split('\r\n\r\n')
        results = self.parseQueryResponse(body)
        raise StopIteration(results)

    def parseQueryResponse(self, body):
        parsed = loads(body, parse_float=Decimal)
        base = parsed['@context']['@base']
        results = []
        for feature in parsed['features']:
            geometries = feature['geometry']['geometries']
            properties = feature['properties']
            pits = []
            for pit in properties['pits']:
                pit['@base'] = base
                pit['@id'] = base + pit['@id']
                pit['hgid'] = base + pit['hgid']
                pit['source'] = base + pit['source']
                geometryIndex = pit['geometryIndex']
                pit['geometry'] = Geometry.fromGeoDict(geometries[geometryIndex]) if geometryIndex > -1 else None
                pits.append(pit)
            results.append((properties['type'], pits))
        return results
