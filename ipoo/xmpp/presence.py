"""
XMPP presence module.

Handle subscription and unsubscription.
"""

import os
import base64
import hashlib

from twisted.python import log, util
from twisted.internet import defer
from twisted.words.xish import domish

from wokkel import xmppim
from wokkel.compat import IQ

NS_VCARD_TEMP = 'vcard-temp'
NS_VCARD_UPDATE = 'vcard-temp:x:update'

class PresenceClientProtocol(xmppim.PresenceClientProtocol):

    def __init__(self, parent, roster):
        self.parent = parent
        self.roster = roster
        self.photo = util.sibpath(__file__,
                                  os.path.join("..", "web", "static",
                                               "ipoo.png"))
        xmppim.PresenceClientProtocol.__init__(self)

    @defer.inlineCallbacks
    def connectionInitialized(self):
        xmppim.PresenceClientProtocol.connectionInitialized(self)
        # First, we need to get the roster before being available
        roster = yield self.roster.getRoster()
        # We become available
        yield self.sendVCard()
        yield self.available()
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

    def available(self):
        """Tell that we are available.

        We also update the photo to use in vCard.
        """
        a = xmppim.AvailablePresence(None, None, {None: "Just ask me!"}, 0)
        # Add the vcard to use
        x = a.addElement((NS_VCARD_UPDATE, "x"))
        x.addElement("photo",
                     content=hashlib.sha1(file(self.photo).read()).hexdigest())
        return self.send(a)

    def sendVCard(self):
        """Send vCard to the server"""
        iq = IQ(self.xmlstream, 'set')
        vcard = iq.addElement((NS_VCARD_TEMP, 'vCard'))
        vcard.addElement("FN", content="IPoo")
        vcard.addElement("DESC", content="IP lookup utility")
        photo = vcard.addElement('PHOTO')
        photo.addElement("TYPE", content="image/png")
        photo.addElement("BINVAL",
                         content=base64.encodestring(
                file(self.photo).read()).replace("\n", ""))
        return iq.send()

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
