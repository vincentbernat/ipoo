"""
XMPP presence module.

Handle subscription and unsubscription.
"""

from twisted.python import log
from twisted.internet import defer
from twisted.words.xish import domish

from wokkel import xmppim

class PresenceClientProtocol(xmppim.PresenceClientProtocol):

    def __init__(self, parent, roster):
        self.parent = parent
        self.roster = roster
        xmppim.PresenceClientProtocol.__init__(self)

    @defer.inlineCallbacks
    def connectionInitialized(self):
        xmppim.PresenceClientProtocol.connectionInitialized(self)
        # First, we need to get the roster before being available
        roster = yield self.roster.getRoster()
        # We become available
        self.available(statuses={None: "Just ask me!"})
        # We enroll existing subscriptions
        for item in roster:
            if roster[item].subscriptionTo:
                log.msg("JID %s is authorized to access the service (%s, %s, %s)" %
                        (item, roster[item].subscriptionFrom,
                         roster[item].subscriptionTo, roster[item].ask))
                self.parent.authorized.append(item)
                # Force mutual auth
                self.subscribe(roster[item].jid)
                self.subscribed(roster[item].jid)

    def subscribeReceived(self, jid):
        if self.parent.getPassword() is not None and \
                jid.userhost() not in self.parent.authorized:
            reply = domish.Element((None, "message"))
            reply["to"] = jid.full()
            reply["type"] = 'chat'
            reply.addElement("body", content="Before I speak to you, I need the password.")
            self.send(reply)
        else:
            log.msg("JID %s is authorized to subscribe" % jid.userhost())
            self.subscribed(jid)
            self.subscribe(jid)

    def unsubscribeReceived(self, jid):
        self.unsubscribed(jid)
        self.unsubscribe(jid)
        self.parent.authorized.remove(jid.userhost())
