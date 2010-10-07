"""
Router plugin.

Retrieve routes from many routers and show the one that matches the IP
address. We only consider connected routes.
"""

import socket
from netaddr import IPAddress, IPNetwork

from twisted.internet import defer, task
from twisted.plugin import IPlugin
from twisted.python import log
from twisted.names import client, error
from zope.interface import implements

from ipoo.collector.icollector import ICollector
from ipoo.collector import helper
from ipoo.collector.proxy import AgentProxy

class Router:
    """
    Collect data from various routers
    """
    implements(ICollector, IPlugin)

    name = "router"
    description = "data from routers"

    @helper.handleIP
    def handle(self, cfg, query):
        return False

    @helper.cache(maxtime=120, maxsize=500)
    @defer.inlineCallbacks
    def process(self, cfg, query):
        routes = yield self.get_routes(cfg)
        results = {}
        for router in routes:
            for network, interface in routes[router]:
                if IPAddress(query) in network:
                    if router not in results:
                        results[router] = []
                    results[router].append({'network': str(network),
                                            'interface': interface})
        defer.returnValue(results)
                
    @helper.refresh(60)
    @helper.cache(maxtime=30, maxsize=1)
    def get_routes(self, cfg):
        """
        Browse the list of routers to get all connected routes. A
        route is a tuple (network, interface)

        @return: a mapping from routers to a list of connected routes.
        """
        def doWork():
            for router in routers:
                log.msg("browsing %s routes" % router)
                d = defer.maybeDeferred(self.get_routes_router, cfg, router)
                # Try harder
                d.addErrback(lambda x, router:
                                 self.get_routes_router(cfg, router),
                             router)
                d.addErrback(lambda x, router:
                                 self.get_routes_router(cfg, router),
                             router)
                d.addCallbacks(lambda x, router: results.update({router: x}),
                               lambda e, router:
                                   log.msg("unable to browse %s: %s" % (router,
                                                                        e.getErrorMessage())),
                               callbackArgs=(router,),
                               errbackArgs=(router,))
                yield d
        results = {}
        routers = cfg.get('routers', {})
        log.msg("browsing routes for %d routers" % len(routers))
        coop = task.Cooperator()
        work = doWork()
        d = defer.DeferredList([coop.coiterate(work)
                                for i in xrange(cfg.get('parallel', 3)-1)])
        d.addCallback(lambda x: results)
        return d

    @helper.cache(maxtime=6000, maxsize=1000)
    @defer.inlineCallbacks
    def get_routes_router(self, cfg, router):
        """
        Get routes from a router using IP-FORWARD-MIB::ipCidrRouteTable.

        Alternatively, if the table is empty, use
        RFC1213-MIB::ipRouteTable.

        @param cfg: configuration
        @param router: name of the router
        @return: a deferred list of tuples (net, interface)
        """
        results = []
        ip = yield client.getHostByName(router)
        proxy = AgentProxy(ip=ip, community=cfg['routers'][router])
        interfaces = yield self.get_interfaces(cfg, proxy)
        base = '.1.3.6.1.2.1.4.24.4.1.5'
        # IP-FORWARD-MIB::ipCidrRouteIfIndex : route + netmask + gateway + interface
        routes = yield proxy.walk(base)
        if not routes:
            # We use RFC1213-MIB instead
            base = '.1.3.6.1.2.1.4.21.1'
            types = yield proxy.walk("%s.8" % base)
            for oid in types:
                if types[oid] != 3: # Not a direct route
                    continue
                ip = ".".join(oid.split(".")[-4:])
                intoid = "%s.2.%s" % (base, ip)
                maskoid = "%s.11.%s" % (base, ip)
                info = yield proxy.get([intoid, maskoid])
                interface, mask = info[intoid], info[maskoid]
                if not interface:
                    continue
                results.append((IPNetwork("%s/%s" % (ip, mask)),
                                interfaces.get(interface, "unknown")))
            defer.returnValue(results)
        for oid in routes:
            # We use IP-FORWARD-MIB
            # Only keep connected routes
            if not oid.endswith(".0.0.0.0"):
                continue
            interface = routes[oid]
            oid = oid.split(".")
            network = ".".join(oid[-13:-9])
            mask = ".".join(oid[-9:-5])
            results.append((IPNetwork("%s/%s" % (network, mask)),
                            interfaces.get(interface, "unknown")))
        defer.returnValue(results)

    @defer.inlineCallbacks
    def get_interfaces(self, cfg, proxy):
        """
        Get interface list for a router.

        @param proxy: SNMP proxy of the router we should get interfaces
        @return: a mapping from interface index to interface name
        """
        results = {}
        # IF-MIB::ifDescr: index + name
        names = yield proxy.walk('.1.3.6.1.2.1.2.2.1.2')
        for oid in names:
            results[int(oid.split(".")[-1])] = names[oid]
        defer.returnValue(results)

router = Router()
