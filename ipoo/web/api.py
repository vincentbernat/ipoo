"""
API related pages
"""

from nevow import rend, tags as T, loaders

from ipoo.web.common import IApiVersion
from ipoo.web.query import QueryResource
from ipoo.web.cfg import CfgResource

class ApiResource(rend.Page):
    """
    Web service for IPoo
    """

    addSlash = True
    versions = [ "1.0" ]        # Valid versions
    docFactory = loaders.stan(T.html [ T.body [ T.p [ "Valid versions are:" ],
                                   T.ul [ [ T.li[v] for v in versions ] ] ] ])

    def __init__(self, *args):
        self.params = args
        rend.Page.__init__(self)

    def childFactory(self, ctx, version):
        if version in ApiResource.versions:
            ctx.remember(version, IApiVersion)
            return ApiVersionedResource(*self.params)
        return None

class ApiVersionedResource(rend.Page):
    """
    Versioned web service for IPoo
    """

    addSlash = True
    docFactory = loaders.stan(T.html [ T.body [ T.p [ "Nothing here" ] ] ])

    def __init__(self, config, collector):
        self.config = config
        self.collector = collector
        rend.Page.__init__(self)

    def child_q(self, ctx):
        return QueryResource(self.config, self.collector)

    def child_cfg(self, ctx):
        return CfgResource(self.config, self.collector)
