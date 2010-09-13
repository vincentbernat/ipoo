"""
XMPP interface to the collector
"""

import re
import pprint

from twisted.internet import defer

class Collector:

    REGEX = re.compile(ur'(?:\b|\/)(?:((?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?))|((?:(?:[a-zA-Z0-9]|[a-zA-Z0-9][\u200ba-zA-Z0-9\-]*[a-zA-Z0-9])\u200b?\.\u200b?)+(?:[A-Za-z]|[A-Za-z][\u200bA-Za-z0-9\-]*[A-Za-z0-9])))(?:\b|\/|\u200b)')

    def __init__(self, collector):
        self.collector = collector

    @defer.inlineCallbacks
    def ask(self, source, question):
        """Ask a question.

        @param source: ignored
        @param question: IP and hostnames
        """
        answers = []
        # First, spot any hostname or IP in the question
        for ip, hostname in Collector.REGEX.findall(question):
            query = None
            if ip:
                query = ip
            elif hostname:
                # Check if the hostname ends with an authorized domain
                hostname = hostname.replace(u"\u200b", "")
                domains = self.collector.config.get('domains', None)
                if domains is None:
                    query = hostname
                else:
                    for domain in domains:
                        if hostname.endswith(domain):
                            query = hostname
                            break
            if query is not None:
                plugins = self.collector.available(query)
                for plugin in plugins:
                    answer = yield self.collector.query(plugin, query)
                    if answer:
                        answer = "About %s, I got some %s:\n%s" % (query,
                                                                  plugins[plugin],
                                                                  pprint.pformat(answer))
                        answers.append(answer)
        defer.returnValue(answers)
