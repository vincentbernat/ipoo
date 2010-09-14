"""
Network plugin.

This plugin will try to give some information about networks, like
IPcalc is doing.
"""

from twisted.plugin import IPlugin
from zope.interface import implements

from netaddr import IPNetwork

from ipoo.collector.icollector import ICollector
from ipoo.collector import helper

class Network:
    """
    Give back results about a network in CIDR notation.
    """
    implements(ICollector, IPlugin)

    name = "network"
    description = "network characteristics"

    @helper.handleNetwork
    def handle(self, cfg, query):
        return False

    def process(self, cfg, query):
        query = IPNetwork(query)
        result = {
            'netmask': str(query.netmask),
            'network': "%s/%s" % (query.network, query.prefixlen),
            'wildcard': str(query.hostmask)
            }
        if len(query) == 1:
            result['nb'] = 1
        else:
            if len(query) == 2:
                result['nb'] = 2
                result['max'] = str(query[-1])
            else:
                result['nb'] = len(query) - 2
                result['broadcast'] = str(query[-1])
                result['max'] = str(query[-2])
            result['min'] = str(query[0])
        return result

network = Network()
