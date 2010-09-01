"""
Interface for collectors
"""

from zope.interface import Interface, Attribute

class ICollector(Interface):
    """Interface for a collector plugin.

    Each plugin should be able to handle several queries in an unique
    instance.
    """

    name = Attribute("plugin name (case insensitive)")
    description = Attribute("informative description of the plugin")

    def handle(cfg, query):
        """
        Return C{True} if this plugin can handle the given query.

        @param cfg: collector configuration
        @param query: query to handle
        @return: C{True} if the query is handled by the plugin,
           C{False} otherwise
        """

    def process(cfg, query):
        """
        Process a given query.

        @param cfg: collector configuration
        @param query: query to process
        @return: The results of the processed query. Can be deferred.
        """
