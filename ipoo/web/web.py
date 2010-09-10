"""
Web service main module
"""

from twisted.python import util
from nevow import rend, appserver, loaders, page, static
from nevow import tags as T

from ipoo.web.api import ApiResource
from ipoo.web.greasemonkey import UserJs

class MainPage(rend.Page):

    docFactory = loaders.xmlfile(util.sibpath(__file__, "main.xhtml"))

    def __init__(self, config, collector):
        self.config = config
        self.collector = collector
        rend.Page.__init__(self)

    def child_api(self, ctx):
        return ApiResource(self.config, self.collector)

    def child_static(self, ctx):
        return static.File(util.sibpath(__file__, "static"))

    def child_userjs(self, ctx):
        return UserJs(self.config)

    def render_included(self, ctx, data):
        return ctx.tag["\n".join(self.config.get("included",["http://*"]))]

    def render_restrictdomains(self, ctx, data):
        if 'domains' in self.collector.config:
            return ctx.tag
        return ""

    def render_domains(self, ctx, data):
        return ctx.tag[[T.li[x] for x in self.collector.config['domains']]]

    def render_showexamples(self, ctx, data):
        if 'examples' in self.config:
            return ctx.tag
        return ""

    def render_examples(self, ctx, data):
        return ", ".join(self.config['examples'])

setattr(MainPage, "child_ipoo.user.js", MainPage.child_userjs)
