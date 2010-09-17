try:
    from twisted.application.service import IServiceMaker
except ImportError:
    pass
else:
    from zope.interface import implements
    from twisted.python import usage
    from twisted.plugin import IPlugin
    from ipoo.core import service

    class Options(usage.Options):
        synopsis = "[options]"
        longdesc = "Make a IPoo server."
        optParameters = [
            ['config', 'c', '/etc/ipoo/ipoo.cfg'],
            ]

    class IPooServiceMaker(object):
        implements(IServiceMaker, IPlugin)

        tapname = "ipoo"
        description = "IPoo server."
        options = Options

        def makeService(self, config):
            return service.makeService(config)

    ipooServer = IPooServiceMaker()
