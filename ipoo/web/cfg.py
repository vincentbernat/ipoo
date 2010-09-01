"""
Configuration related pages
"""

from ipoo.web.json import JsonPage

class CfgResource(JsonPage):
    """Export some configuration items"""

    exported = ["domains"]
    def __init__(self, config, collector):
        self.config = config
        self.collector = collector
        JsonPage.__init__(self)

    def data_json(self, ctx, data):
        results = {}
        for e in self.exported:
            if e in self.collector.config:
                results[e] = self.collector.config[e]
        return results
