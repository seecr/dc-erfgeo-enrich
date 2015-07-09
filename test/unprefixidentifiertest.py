from seecr.test import SeecrTestCase, CallTrace

from weightless.core import be, consume
from meresco.core import Observable

from digitalecollectie.erfgeo.unprefixidentifier import UnprefixIdentifier


class UnprefixIdentifierTest(SeecrTestCase):
    def testUnprefixIdentifier(self):
        observer = CallTrace('observer')
        top = be(
            (Observable(),
                (UnprefixIdentifier(prefix='prefix:'),
                    (observer,)
                )
            )
        )
        consume(top.all.aMessage(identifier='prefix:xyz', otherKwarg='123'))
        consume(top.all.aMessage(identifier='nomatch:xyz', otherKwarg='456'))
        self.assertEquals(['aMessage', 'aMessage'], observer.calledMethodNames())
        self.assertEquals(dict(identifier='xyz', otherKwarg='123'), observer.calledMethods[0].kwargs)
        self.assertEquals(dict(identifier='nomatch:xyz', otherKwarg='456'), observer.calledMethods[1].kwargs)
