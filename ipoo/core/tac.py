"""
IPoo service (as a TAC file)

This module should only be used with Twisted < 2.5
"""

from twisted.application import service
from ipoo.core import service as ws

application = service.Application('IPoo')
ws.makeService({"config": "/etc/ipoo/ipoo.cfg"}).setServiceParent(
    service.IServiceCollection(application))
