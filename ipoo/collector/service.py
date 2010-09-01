"""
Main service for collector.
"""

from twisted.internet import defer
from twisted.application import internet, service
from twisted.plugin import getPlugins

from ipoo.collector.icollector import ICollector

import ipoo.collector.plugins

class CollectorService(service.Service):
    """Service to collect various data using plugins"""

    def __init__(self, config):
        self.config = config
        self.setName("Data collector")

    def available(self, query):
        """Return the list of available collectors for a given query"""
        return dict([(plugin.name, plugin.description) for plugin
                     in getPlugins(ICollector, ipoo.collector.plugins)
                     if plugin.handle(self.config, query)])

    def query(self, plugin, query):
        """Let the given plugin handle the given query"""
        for p in getPlugins(ICollector, ipoo.collector.plugins):
            if p.name.upper() == plugin.upper() and p.handle(self.config, query):
                return p.process(self.config, query)
        raise NotImplementedError("%r does not handle %r" % (plugin, query))
