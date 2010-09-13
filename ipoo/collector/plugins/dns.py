"""
DNS plugin.

Given an IP, return the list of names known for this IP from DNS. When
not given an IP, return the list of IP known for this name. All
informations are extracted from the DNS
"""

import socket
import struct

from netaddr import IPAddress

from twisted.internet import defer
from twisted.plugin import IPlugin
from twisted.names import client, error, dns as tdns
from zope.interface import implements

from ipoo.collector.icollector import ICollector
from ipoo.collector import helper

class Dns:
    """
    Collect data from DNS about an IP or a name.
    """
    implements(ICollector, IPlugin)

    name = "dns"
    description = "data from DNS"

    @helper.handleIP
    @helper.handleFQDN
    def handle(self, cfg, query):
        return False

    @helper.cache(maxtime=120, maxsize=200)
    @defer.inlineCallbacks
    def process(self, cfg, query):
        try:
            query = socket.inet_ntoa(socket.inet_aton(query))
        except:
            # Not an IP
            methods = [client.lookupAddress, client.lookupCanonicalName]
        else:
            # An IP
            query = IPAddress(query).reverse_dns
            methods = [ client.lookupPointer ]
        answers = []
        for method in methods:
            try:
                a, _, _ = yield method(query)
            except error.DomainError:
                a = []
            answers.extend(a)
        results = { 'PTR': [], 'A': [], 'CNAME': []}
        for answer in answers:
            if answer.type == tdns.PTR:
                results['PTR'].append((str(answer.payload.name), 1))
            if answer.type == tdns.CNAME:
                results['CNAME'].append((str(answer.payload.name), 1))
            elif answer.type == tdns.A:
                results['A'].append((str(answer.payload.dottedQuad()), 1))
        for key in results.keys()[:]:
            if not results[key]:
                del results[key]
            else:
                results[key] = dict(results[key]).keys()
        defer.returnValue(results)

dns = Dns()
