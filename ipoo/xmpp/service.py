"""
XMPP service module
"""

import time
import random
import hashlib

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

    _seed1 = object()
    _seed2 = random.randint(0, 1<<32)

    def __init__(self, config, collector):
        self.config = config
        self.collector = collector
        self.setName("XMPP service")
        client.XMPPClient.__init__(self, 
                                   JID(self.config['login']),
                                   self.config['password'])
        self.logTraffic = True
        self.authorized = []    # List of authorized users

    def startService(self):
        # Set protocol handler
        ping = PingHandler()
        ping.setHandlerParent(self)
        roster = xmppim.RosterClientProtocol()
        roster.setHandlerParent(self)
        self.presence = PresenceClientProtocol(self, roster)
        self.presence.setHandlerParent(self)
        message = MessageProtocol(self, self.collector)
        message.setHandlerParent(self)
        # Start client
        client.XMPPClient.startService(self)

    def stopService(self):
        if self.presence is not None:
            self.presence.unavailable()
        client.XMPPClient.stopService(self)

    def getPassword(self):
        """Return the password needed to register"""
        # We want a temporary password that changes every hour
        if self.config.get('protected', False):
            h = hashlib.sha256("%r %d %d" % (self._seed1,
                                             self._seed2,
                                             int(time.time()/60/60)))
            return h.hexdigest()
        return None
