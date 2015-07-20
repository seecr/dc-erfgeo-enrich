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

from unittest import TestCase

from seecr.test import CallTrace

from weightless.core import local, be, compose
from meresco.core import Observable, asyncreturn

from digitalecollectie.erfgeo.callstackdict import CallStackDict, callStackDictGet


class CallStackDictTest(TestCase):
    def testCallStackDict(self):
        observer = CallTrace(emptyGeneratorMethods=['someMethod'])
        monitor = CallStackDictMonitor('part2')
        observable = be((Observable(),
            (CallStackDict(
                    {'part2': lambda **kwargs: kwargs['someString'].partition('|')[2]}),
                (observer,),
                (monitor,)
            )
        ))

        list(compose(observable.all.someMethod(42, someString="abc|value")))
        self.assertEquals(["someMethod(42, someString='abc|value')"], [str(m) for m in observer.calledMethods])
        self.assertEquals(['value'], monitor.fieldValues)

    def testCallStackDictScoping(self):
        observer = CallTrace(emptyGeneratorMethods=['someMethod'])
        monitor = CallStackDictMonitor('part2')
        observable = be((Observable(),
            (monitor,),
            (CallStackDict(),
                (monitor,),
                (CallStackDict(
                        {'part2': lambda **kwargs: kwargs['someString'].partition('|')[2]}),
                    (observer,),
                ),
                (monitor,)
            )
        ))

        list(compose(observable.all.someMethod(42, someString="abc|value")))
        self.assertEquals(["someMethod(42, someString='abc|value')"], [str(m) for m in observer.calledMethods])
        self.assertEquals([NOT_FOUND, {}, {'part2': 'value'}], monitor.dicts)
        self.assertEquals([NOT_FOUND, NOT_FOUND, 'value'], monitor.fieldValues)


NOT_FOUND = object()

class CallStackDictMonitor(Observable):
    def __init__(self, field=None):
        Observable.__init__(self)
        self._field = field
        self.dicts = []
        self.fieldValues = []

    @asyncreturn
    def all_unknown(self, message, *args, **kwargs):
        if self._field:
            value = callStackDictGet(self._field, NOT_FOUND)
            self.fieldValues.append(value)
        try:
            callstack_dict = local('__callstack_dict__')
            self.dicts.append(dict(callstack_dict))
        except AttributeError:
            self.dicts.append(NOT_FOUND)

