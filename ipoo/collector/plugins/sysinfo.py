"""
Sysinfo plugin.

Given an IP, return the list of names known for this IP. When not
given an IP, return the list of IP known for this name. All
informations are extracted from the sysinfo database.

This plugin requires an URL to be queried in the configuration file::
  collector:
    sysinfo: http://example.com/sysinfo

This returns a file with each line containing a tuple (canonical
hostname, IP). For example::
  hostname1.example.com 1.1.2.3
  hostname1.example.com 1.1.2.4
  hostname1.example.com 1.1.2.5
  hostname2.example.com 1.2.2.5
  hostname2.example.com 1.2.2.5
"""

import socket
import struct

from twisted.internet import defer
from twisted.plugin import IPlugin
from twisted.web import client
from zope.interface import implements

from ipoo.collector.icollector import ICollector
from ipoo.collector import helper

class Sysinfo:
    """
    Collect data from sysinfo database about an IP or a name.
    """
    implements(ICollector, IPlugin)

    name = "sysinfo"
    description = "Data from sysinfo database"

    @helper.requireCfg
    @helper.handleIP
    @helper.handleFQDN
    def handle(self, cfg, query):
        return False

    @helper.cache(maxtime=120, maxsize=200)
    @defer.inlineCallbacks
    def process(self, cfg, query):
        sysinfo = yield self.sysdb(cfg)
        try:
            query = socket.inet_ntoa(socket.inet_aton(query))
        except:
            # Not an IP
            result = dict([(ip, 1) for name, ip in sysinfo if name == query]).keys()
            result.sort(key=lambda x: struct.unpack("!L", socket.inet_aton(x))[0])
        else:
            # An IP
            result = dict([(name, 1) for name, ip in sysinfo if ip == query]).keys()
            result.sort()
        defer.returnValue(result)

    @helper.cache(maxtime=600)
    @defer.inlineCallbacks
    def sysdb(self, cfg):
        """
        Get sysinfo database.

        @return: a deferred list of (name, ip) tuples
        """
        results = []
        sysinfo = yield client.getPage(cfg[self.name])
        for line in sysinfo.split("\n"):
            line = line.split()
            if len(line) == 2:
                results.append(tuple(line))
        defer.returnValue(results)

sysinfo = Sysinfo()
