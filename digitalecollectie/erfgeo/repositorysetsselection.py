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

from os import rename, makedirs
from os.path import isfile, isdir, dirname
from collections import defaultdict

from simplejson import dumps, loads


WILDCARD = '*'

class RepositorySetsSelection(object):
    def __init__(self, filepath):
        self._filepath = filepath
        isdir(dirname(self._filepath)) or makedirs(dirname(self._filepath))
        self._read()

    def selectedSetSpecs(self, repositoryId=None):
        for key in sorted(self._selection.keys()):
            if repositoryId is None or key == repositoryId:
                sets = self._selection[key]
                for setSpec in sorted(sets):
                    yield (key, setSpec)

    def addToSelection(self, repositoryId, setSpec=WILDCARD):
        sets = self._selection[repositoryId]
        sets.append(setSpec)
        if WILDCARD in sets:
            for setSpec in sets[:]:
                if setSpec != WILDCARD:
                    sets.remove(setSpec)
        self._selection[repositoryId] = list(set(sets))
        self._save()

    def isSelected(self, repositoryId, setSpec=WILDCARD):
        try:
            return setSpec in self._selection[repositoryId]
        except KeyError:
            return False

    def _read(self):
        self._selection = defaultdict(list)
        if not isfile(self._filepath):
            self._save()
            return
        jsonDict = loads(open(self._filepath).read())
        for d in jsonDict['setsSelection']:
            self._selection[d['repositoryId']] = d['sets']

    def _save(self):
        jsonDict = {'setsSelection': [
            dict(repositoryId=repositoryId, sets=sets)
            for repositoryId, sets in sorted(self._selection.items())
        ]}
        tmpfile = self._filepath + '~'
        with open(tmpfile, "w") as f:
            f.write(dumps(jsonDict, sort_keys=True, indent=2))
        rename(tmpfile, self._filepath)
