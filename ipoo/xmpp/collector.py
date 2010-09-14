"""
XMPP interface to the collector
"""

import re
import pprint

from twisted.internet import defer
from twisted.words.xish import domish

from ipoo.xmpp import MixedMessage

class Collector:

    REGEX = re.compile(ur'(?:\b|\/)((?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)(?:/[0-9]{1,2})?|(?:(?:[a-zA-Z0-9]|[a-zA-Z0-9][\u200ba-zA-Z0-9\-]*[a-zA-Z0-9])\u200b?\.\u200b?)+(?:[A-Za-z]|[A-Za-z][\u200bA-Za-z0-9\-]*[A-Za-z0-9]))(?:\b|\/|\u200b)')

    def __init__(self, collector):
        self.collector = collector

    def format(self, query, description, answer):
        """Turn query, description and answer into domish node

        The result will be suitable for inclusion into <html> element.
        """

        def simplify(data):
            if type(data) is list:
                if len(data) == 1:
                    return data[0]
                return [simplify(x) for x in data]
            if type(data) is tuple:
                if len(data) == 1:
                    return data[0]
                return tuple([simplify(x) for x in data])
            if type(data) is dict:
                return dict([(x,simplify(y)) for x,y in data.items()])
            return data

        root = domish.Element(('http://www.w3.org/1999/xhtml', 'body'))
        p = root.addElement("p")
        p.addContent("I got some ")
        s = p.addElement("strong", content=description)
        p.addContent(" about ")
        s = p.addElement("strong", content=query)
        p.addContent(":")
        for line in pprint.pformat(simplify(answer)).split("\n"):
            root.addElement("br")
            span = root.addElement("span", content=line)
            span.attributes['style'] = 'font-size: xx-small; font-family: monospace'
        return root

    @defer.inlineCallbacks
    def ask(self, source, question):
        """Ask a question.

        @param source: ignored
        @param question: IP and hostnames
        """
        answers = []
        seen = []
        query = None
        # First, spot any hostname or IP in the question
        for query in Collector.REGEX.findall(question):
            query = query.replace(u"\u200b", "")
            if query in seen:
                continue
            seen.append(query)
            plugins = self.collector.available(query)
            for plugin in plugins:
                answer = yield self.collector.query(plugin, query)
                if answer:
                    answer = MixedMessage("About %s, I got some %s:\n%s" % (
                            query,
                            plugins[plugin],
                            pprint.pformat(answer)),
                                          self.format(query, plugins[plugin],
                                                      answer))
                    answers.append(answer)
        if len(answers) > 3:
            answers.insert(0,
                           "Good news! I've found plenty of answers for your question!")
        elif not answers and query is not None:
            answers.insert(0,
                           "Sorry, I did not find anything useful about this.")
        defer.returnValue(answers)
