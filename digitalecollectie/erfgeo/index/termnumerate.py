from meresco.core import Observable
from meresco.components.http.utils import CRLF


class TermNumerate(Observable):
    def __init__(self, host, port):
        Observable.__init__(self)
        self._host = host
        self._port = port

    def numerateTerm(self, term):
        response = yield self.any.httprequest(host=self._host, port=self._port, method='POST', request='/numerate', body=term)
        header, body = response.split(CRLF * 2, 1)
        raise StopIteration(int(body))
        yield
