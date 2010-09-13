"""
XMPP presence module.

Handle subscription and unsubscription.
"""

from twisted.python import log
from twisted.internet import defer

from wokkel import xmppim

class PresenceClientProtocol(xmppim.PresenceClientProtocol):

    def __init__(self, roster):
        self.roster = roster
        xmppim.PresenceClientProtocol.__init__(self)

    @defer.inlineCallbacks
    def connectionInitialized(self):
        xmppim.PresenceClientProtocol.connectionInitialized(self)
        # First, we need to get the roster before being available
        roster = yield self.roster.getRoster()
        # We become available
        self.available(statuses={None: "Just ask me!"})
        # We answer pending subscriptions
        for item in roster:
            if roster[item].ask or (roster[item].subscriptionFrom and
                                   not roster[item].subscriptionTo):
                self.subscribe(roster[item].jid)

    def subscribeReceived(self, jid):
        self.subscribed(jid)
        self.subscribe(jid)

    def unsubscribeReceived(self, jid):
        self.unsubscribed(jid)
        self.unsubscribe(jid)
