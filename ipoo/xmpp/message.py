"""
XMPP message module.

Receive messages and handles them
"""

from twisted.python import log
from twisted.internet import defer
from twisted.words.protocols.jabber.xmlstream import toResponse
from wokkel import xmppim

from ipoo.xmpp.alice import Alice
from ipoo.xmpp.collector import Collector

class MessageProtocol(xmppim.MessageProtocol):

    def __init__(self, collector):
        self.bots = [Collector(collector), Alice()]
        xmppim.MessageProtocol.__init__(self)

    @defer.inlineCallbacks
    def onMessage(self, message):
        # Ignore errors
        if message.getAttribute('type') == 'error':
            return
        # Ignore empty messages
        if not message.body or not unicode(message.body):
            return

        # Tell the user we are building an answer
        response = toResponse(message, message.getAttribute('type'))
        response.addElement('composing').attributes["xmlns"] = \
            'http://jabber.org/protocol/chatstates'
        self.send(response)

        # Get an answer from the first one able to answer
        answers = None
        for bot in self.bots:
            try:
                answers = yield bot.ask(message.getAttribute('from'),
                                        unicode(message.body).encode('ascii', 'ignore'))
            except Exception as e:
                log.msg("Catch exception for bot %r: %s" % (bot, e))
                continue
            if answers:
                break
        if not answers:
            answers = ["Seven amazing hamsters make your day!"]

        for answer in answers:
            response = toResponse(message, message.getAttribute('type'))
            response.addElement('body', content=unicode(answer))
            yield self.send(response)
