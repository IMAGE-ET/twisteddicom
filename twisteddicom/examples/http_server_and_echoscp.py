#!/usr/bin/python
# Copyright (c) 2012 Bo Eric Rickard Holmberg <rickard@holmberg.info>

# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:

# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from twisteddicom import dimse, dimsemessages
from twisteddicom.utils import get_uid
from twisted.python import log
from twisted.internet import reactor
from twisted.internet.protocol import Factory
from twisted.internet.endpoints import TCP4ServerEndpoint

class EchoSCP(dimse.DIMSEProtocol):
    def __init__(self):
        super(EchoSCP, self).__init__(is_association_requestor = False, 
                                      supported_abstract_syntaxes = [get_uid("Verification SOP Class")])
     
    def C_ECHO_RQ_received(self, presentation_context_id, echo_rq, dimse_data):
        log.msg("received DIMSE command %s on presentation context %i" % (echo_rq, presentation_context_id))
        assert echo_rq.__class__ == dimsemessages.C_ECHO_RQ
        log.msg("replying")
        self.send_DIMSE_command(presentation_context_id, dimsemessages.C_ECHO_RSP(echo_rq.message_id))

class EchoSCPFactory(Factory, object):
    def __init__(self):
        super(EchoSCPFactory, self).__init__()
        self.n_requests = 0
        
    def buildProtocol(self, addr):
        protocol = EchoSCP()
        self.n_requests += 1
        return protocol

def gotProtocol(p):
    log.msg("gotProtocol")
    pass

from twisted.web import server, resource
from twisted.internet import reactor

class EchoWebServer(resource.Resource, object):
    def __init__(self, echoscpfactory):
        super(EchoWebServer, self).__init__()
        self.echoscpfactory = echoscpfactory
    isLeaf = True
    def render_GET(self, request):
        return "<html><body>Hello, world! We have received and answered %s association requests.</body></html>" % (echoscpfactory.n_requests,)

if __name__== '__main__':
    import sys
    log.startLogging(sys.stdout)
    if len(sys.argv) != 3:
        log.msg("Syntax: %s <dicom port> <http port>" % sys.argv[0])
        sys.exit(1)
    endpoint = TCP4ServerEndpoint(reactor, port = int(sys.argv[1]))
    echoscpfactory = EchoSCPFactory()
    endpoint.listen(echoscpfactory)

    site = server.Site(EchoWebServer(echoscpfactory))
    reactor.listenTCP(int(sys.argv[2]), site)
        
    reactor.run()
    log.msg("reactor.run() exited")