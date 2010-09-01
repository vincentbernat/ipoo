"""
Web service main module
"""

from nevow import rend, appserver, loaders, page
from nevow import tags as T

from ipoo.web.api import ApiResource

class MainPage(rend.Page):

    docFactory = loaders.stan(T.html [ T.body [ T.p [ "Nothing here (yet)" ] ] ])

    def __init__(self, *args):
        self.params = args
        rend.Page.__init__(self)

    def child_api(self, ctx):
        return ApiResource(*self.params)
