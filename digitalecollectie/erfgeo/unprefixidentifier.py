from meresco.core import Observable


class UnprefixIdentifier(Observable):
    def __init__(self, prefix='oai:data.digitalecollectie.nl:', **kwargs):
        Observable.__init__(self, **kwargs)
        self._prefix = prefix

    def all_unknown(self, message, identifier, **kwargs):
        if identifier.startswith(self._prefix):
            identifier = identifier[len(self._prefix):]
        yield self.all.unknown(message, identifier=identifier, **kwargs)
