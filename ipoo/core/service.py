"""
IPoo service
"""

import yaml

from twisted.application import service, internet
from twisted.internet import reactor
from twisted.python import log
from nevow import appserver

from ipoo.collector.service import CollectorService
from ipoo.web.web import MainPage
from ipoo.xmpp.service import XmppService

def makeService(config):
    configfile = yaml.load(file(config['config'], 'rb').read())
    application = service.MultiService()

    # Collector
    collector = CollectorService(configfile.get('collector', {}))
    collector.setServiceParent(application)

    # XMPP
    xmpp = None
    xmppconfig = configfile.get('xmpp', {})
    if xmppconfig:
        xmpp = XmppService(xmppconfig, collector)
        xmpp.setServiceParent(application)

    # Web service
    webconfig = configfile.get('web', {})
    web = internet.TCPServer(webconfig.get('port', 8096),
                             appserver.NevowSite(MainPage(webconfig, collector, xmpp)),
                             interface=webconfig.get('interface', '127.0.0.1'))
    web.setServiceParent(application)

    return application
