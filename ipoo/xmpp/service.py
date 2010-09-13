"""
XMPP service module
"""

from twisted.application import service
from twisted.internet import reactor
from twisted.python import log

from twisted.application import service
from twisted.words.protocols.jabber.jid import JID
from wokkel import client, xmppim
from wokkel.ping import PingHandler

from ipoo.xmpp.presence import PresenceClientProtocol
from ipoo.xmpp.message import MessageProtocol

class XmppService(client.XMPPClient):

    def __init__(self, config, collector):
        self.config = config
        self.collector = collector
        self.setName("XMPP service")
        client.XMPPClient.__init__(self, 
                                   JID(self.config['login']),
                                   self.config['password'])
        self.logTraffic = True
        self.presence = None

    def startService(self):
        # Set protocol handler
        ping = PingHandler()
        ping.setHandlerParent(self)
        roster = xmppim.RosterClientProtocol()
        roster.setHandlerParent(self)
        self.presence = PresenceClientProtocol(roster)
        self.presence.setHandlerParent(self)
        message = MessageProtocol(self.collector)
        message.setHandlerParent(self)
        # Start client
        client.XMPPClient.startService(self)

    def stopService(self):
        if self.presence is not None:
            self.presence.unavailable()
        client.XMPPClient.stopService(self)
