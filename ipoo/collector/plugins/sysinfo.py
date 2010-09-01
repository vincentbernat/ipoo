"""
Sysinfo plugin.

Given an IP, return the list of names known for this IP. When not
given an IP, return the list of IP known for this name. All
informations are extracted from the sysinfo database.
"""

import socket
import struct

from twisted.internet import defer
from twisted.plugin import IPlugin
from twisted.web import client
from zope.interface import implements

from ipoo.collector.icollector import ICollector
from ipoo.collector import helper

SYSINFO_URL="http://sysinfo.oih.p.fti.net/data/host_ip.dat"

class Sysinfo:
    """
    Collect data from sysinfo database about an IP or a name.
    """
    implements(ICollector, IPlugin)

    name = "sysinfo"
    description = "Data from sysinfo database"

    @helper.handleIP
    @helper.handleFQDN
    def handle(self, cfg, query):
        return False

    @helper.cache(maxtime=120, maxsize=200)
    @defer.inlineCallbacks
    def process(self, cfg, query):
        sysinfo = yield self.sysdb()
        try:
            query = socket.inet_ntoa(socket.inet_aton(query))
        except:
            # Not an IP
            result = dict([(ip, 1) for name, ip in sysinfo if name == query]).keys()
            result.sort()
        else:
            # An IP
            result = dict([(name, 1) for name, ip in sysinfo if ip == query]).keys()
            result.sort(key=lambda x: struct.unpack("!L", socket.inet_aton(x))[0])
        defer.returnValue(result)

    @helper.cache(maxtime=600)
    @defer.inlineCallbacks
    def sysdb(self):
        """
        Get sysinfo database.

        @return: a deferred list of (name, ip) tuples
        """
        results = []
        sysinfo = yield client.getPage(SYSINFO_URL)
        for line in sysinfo.split("\n"):
            line = line.split()
            if len(line) == 2:
                results.append(tuple(line))
        defer.returnValue(results)

sysinfo = Sysinfo()
