from urllib import urlencode

from weightless.http import httpget
from meresco.core import Observable


class Proxy(Observable):
    def __init__(self, rewriteRequest, **kwargs):
        Observable.__init__(self, **kwargs)
        self._rewriteRequest = rewriteRequest

    def handleRequest(self, **kwargs):
        newKwargs = self._rewriteRequest(**kwargs)
        headers = newKwargs.get('Headers')
        host = newKwargs.get('host', 'localhost')
        port = newKwargs.get('port', 80)
        request = newKwargs.get('path', '/')
        arguments = newKwargs.get('arguments')
        if arguments:
            request += '?' + urlencode(arguments, doseq=True)
        result = yield httpget(host=host, port=port, request=request, headers=headers)
        yield result
