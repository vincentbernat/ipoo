"""
Greasemonkey related stuff
"""

from nevow import rend, inevow

class UserJs(rend.Page):
    """Return a ipoo.user.js greasemonkey script to the user."""

    def __init__(self, config):
        self.config = config
        rend.Page.__init__(self)

    def renderHTTP(self, ctx):
        session = inevow.ISession(ctx)
        request = inevow.IRequest(ctx)
        # If we have arguments, we remember them in a session and
        # reload the page
        if 'included' in request.args and 'location' in request.args:
            session.included = request.args['included'][0]
            session.location = request.args['location'][0]
            request.redirect(request.path)
            return ''
        # Without arguments, we build the script
        answer = """// IPoo Greasemonkey script

// ==UserScript==
// @name           IPoo
// @namespace      http://www.luffy.cx/
// @description    Interface to IPoo web service
// @require        %(service)sstatic/ipoo.js
// @resource  icon %(service)sstatic/ipoo-round.png
%(included)s
// ==/UserScript==

// Don't run on iframes
if(top != self) return;

console.info("Running IPoo for " + document.location.href);
ipoo.config.ws = "%(service)s";
ipoo.config.icon = GM_getResourceURL("icon");

ipoo.setup();

"""
        answer = answer % {'included': "\n".join(["// @include        %s" % x
                                                  for x
                                                  in session.included.split("\n")]),
                           'service': session.location
                           }
        request.setHeader("content-type",  "text/javascript; charset=utf-8")
        request.setHeader("content-length", len(answer))
        return answer
