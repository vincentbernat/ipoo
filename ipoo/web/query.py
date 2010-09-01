"""
Query related pages
"""

from nevow import rend, tags as T, loaders

from ipoo.web.json import JsonPage

class QueryResource(rend.Page):
    """Handle a generic query.

    Such a resource will return the available plugins for the given
    query. Each plugin can be requested using its name as a child for
    this resource.

    Some examples::
       /q/127.0.0.1/
       /q/127.0.0.1/dns/
    """
    addSlash = True
    docFactory = loaders.stan(T.html [ T.body [ T.p [ "Nothing here" ] ] ])

    def __init__(self, config, collector):
        self.config = config
        self.collector = collector
        rend.Page.__init__(self)

    def childFactory(self, ctx, query):
        return QueryOneResource(self.config, self.collector, query)


class QueryOneResource(JsonPage):
    """Handle one query"""
    def __init__(self, config, collector, query):
        self.config = config
        self.collector = collector
        self.query = query
        JsonPage.__init__(self)

    def data_json(self, ctx, data):
        return self.collector.available(self.query)

    def childFactory(self, ctx, plugin):
        return QueryPluginResource(self.config, self.collector,
                                   plugin, self.query)

class QueryPluginResource(JsonPage):
    """Handle one query for a given plugin"""
    def __init__(self, config, collector, plugin, query):
        self.config = config
        self.collector = collector
        self.plugin = plugin
        self.query = query

    def data_json(self, ctx, data):
        if self.plugin not in self.collector.available(self.query):
            return None
        return self.collector.query(self.plugin, self.query)
