"""
Greasemonkey related stuff
"""

import base64

from twisted.python import util
from nevow import rend, inevow, static, loaders
from nevow import tags as T

class RequestUserJs(rend.Page):
    """
    Request a greasemonkey script. This script will be provided
    through a javascript redirect. Data to generate this script are
    saved in a session.
    """

    docFactory = loaders.xmlfile(util.sibpath(__file__, "greasemonkey.xhtml"))
    addSlash = True

    def __init__(self, config):
        self.config = config
        rend.Page.__init__(self)

    def render_save(self, ctx, data):
        # If we have arguments, we remember them in a session and
        # provide a redirect page
        session = inevow.ISession(ctx)
        request = inevow.IRequest(ctx)
        if 'included' in request.args and 'location' in request.args:
            session.included = request.args['included'][0]
            session.location = request.args['location'][0]
            return ctx.tag
        return T.p["Get back at the main page to generate your user script."]

    def child_userjs(self, ctx):
        return UserJs(self.config)

setattr(RequestUserJs, "child_ipoo.user.js", RequestUserJs.child_userjs)

class UserJs(rend.Page):
    """Return a ipoo.user.js greasemonkey script to the user."""

    def __init__(self, config):
        self.config = config
        rend.Page.__init__(self)

    def renderHTTP(self, ctx):
        session = inevow.ISession(ctx)
        request = inevow.IRequest(ctx)
        ipoojs = file(util.sibpath(__file__,
                                   "static/ipoo.js")).read()
        icon = base64.b64encode(file(
                util.sibpath(__file__,
                             "static/ipoo-round.png")).read())
        answer = """// IPoo Greasemonkey script

// ==UserScript==
// @name           IPoo
// @namespace      http://www.luffy.cx/
// @description    Interface to IPoo web service
%(included)s
// ==/UserScript==

// Don't run on iframes
if(top != self) return;

// ipoo.js (begin)
%(ipoojs)s
// ipoo.js (end)

console.info("Running IPoo for " + document.location.href);
ipoo.config.ws = "%(service)s";
ipoo.config.icon = "data:image/png;base64,%(icon)s";
ipoo.config.greasemonkey = true;

ipoo.setup();

"""
        answer = answer % {'included': "\n".join(["// @include        %s" % x
                                                  for x
                                                  in session.included.split("\n")]),
                           'service': session.location,
                           'ipoojs': ipoojs,
                           'icon': icon
                           }
        request.setHeader("content-type",  "text/javascript; charset=utf-8")
        request.setHeader("content-length", len(answer))
        return answer
