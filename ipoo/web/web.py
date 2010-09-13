"""
Web service main module
"""

from twisted.python import util
from nevow import rend, appserver, loaders, page, static, inevow
from nevow import tags as T

from ipoo.web.api import ApiResource
from ipoo.web.greasemonkey import RequestUserJs

class MainPage(rend.Page):

    docFactory = loaders.xmlfile(util.sibpath(__file__, "main.xhtml"))

    def __init__(self, config, collector, xmpp):
        self.config = config
        self.collector = collector
        self.xmpp = xmpp
        rend.Page.__init__(self)

    # Children

    def child_api(self, ctx):
        # The API can be used with XSS. The web client is a regular client for us.
        inevow.IRequest(ctx).setHeader("Access-Control-Allow-Origin",
                                       "*")
        return ApiResource(self.config, self.collector)

    def child_static(self, ctx):
        # The web client will try to fetch some static files
        inevow.IRequest(ctx).setHeader("Access-Control-Allow-Origin",
                                       "*")
        return static.File(util.sibpath(__file__, "static"))

    def child_greasemonkey(self, ctx):
        return RequestUserJs(self.config)

    # Main page rendering

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

    def render_xmppenabled(self, ctx, data):
        if self.xmpp is not None:
            return ctx.tag
        return ""

    def render_xmppjid(self, ctx, data):
        if self.xmpp is not None:
            return ctx.tag(href="xmpp:%s" % self.xmpp.config['login'])[
                self.xmpp.config['login']]
        return ""

    def render_xmppprotected(self, ctx, data):
        if self.xmpp is not None:
            password = self.xmpp.getPassword()
            if password:
                return ctx.tag
        return ""

    def render_xmpppassword(self, ctx, data):
        if self.xmpp:
            password = self.xmpp.getPassword()
            if password:
                return ctx.tag[password]
        return ""
