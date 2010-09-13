"""
XMPP message module.

Receive messages and handles them
"""

from twisted.python import log
from twisted.internet import defer
from twisted.words.protocols.jabber.xmlstream import toResponse
from wokkel import xmppim
from twisted.words.xish import domish
from twisted.words.protocols.jabber.jid import JID

from ipoo.xmpp.alice import Alice
from ipoo.xmpp.collector import Collector

class MessageProtocol(xmppim.MessageProtocol):

    def __init__(self, parent, collector):
        self.bots = [Collector(collector), Alice()]
        self.parent = parent
        xmppim.MessageProtocol.__init__(self)

    @defer.inlineCallbacks
    def onMessage(self, message):
        # Ignore empty messages
        if not message.body or not unicode(message.body):
            return
        if message["type"] != 'chat':
            return

        jid = message["from"].split("/")[0]
        if jid not in self.parent.authorized:
            # User is not authorized! Is it telling us the password?
            if unicode(message.body).strip() == self.parent.getPassword():
                self.parent.authorized.append(jid)
                answer = "Welcome!"
                log.msg("Accepting JID %s with the right password" % jid)
                self.parent.presence.subscribed(JID(jid))
                self.parent.presence.subscribe(JID(jid))
            else:
                answer = "Tell me the password or I won't speak to you."
            response = toResponse(message, 'chat')
            response.addElement('body',
                                content=unicode(answer))
            self.send(response)
            return

        # Tell the user we are building an answer
        response = toResponse(message, 'chat')
        response.addElement('composing').attributes["xmlns"] = \
            'http://jabber.org/protocol/chatstates'
        self.send(response)

        # Get an answer from the first one able to answer
        answers = None
        for bot in self.bots:
            try:
                answers = yield bot.ask(message['from'],
                                        unicode(message.body).encode('ascii', 'ignore'))
            except Exception as e:
                log.msg("Catch exception for bot %r: %s" % (bot, e))
                continue
            if answers:
                break
        if not answers:
            answers = ["Seven amazing hamsters make your day!"]

        for answer in answers:
            response = toResponse(message, message['type'])
            response.addElement('body', content=unicode(answer))
            yield self.send(response)
