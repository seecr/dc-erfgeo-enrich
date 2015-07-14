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
# Copyright (C) 2011-2012, 2015 Netherlands Institute for Sound and Vision http://instituut.beeldengeluid.nl/
# Copyright (C) 2011-2012, 2015 Seecr (Seek You Too B.V.) http://seecr.nl
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

from weightless.core import local

from meresco.core import Observable


class CallStackDict(Observable):
    def __init__(self, keyValueFunctions=None):
        Observable.__init__(self)
        self._keyValueFunctions = keyValueFunctions or {}

    def all_unknown(self, message, *args, **kwargs):
        try:
            __callstack_dict__ = local('__callstack_dict__')
        except AttributeError:
            __callstack_dict__ = {}
        for key, valueFunction in self._keyValueFunctions.items():
            __callstack_dict__[key] = valueFunction(**kwargs)
        yield self.all.unknown(message, *args, **kwargs)


def callStackDictGet(key, *args, **kwargs):
    try:
        d = local('__callstack_dict__')
        return d[key]
    except (AttributeError, KeyError):
        if args or 'default' in kwargs:
            default = args[0] if args else kwargs['default']
            return default
        else:
            raise

