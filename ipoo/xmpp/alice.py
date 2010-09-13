"""
Interface to ALICE bot.
"""

import urllib
import hashlib
from xml.dom import minidom

from twisted.internet import defer
from twisted.web import client

class AliceError(Exception):
    pass

class Alice:

    def __init__(self, botid='f5d922d97e345aa1'):
        self.botid = botid

    @defer.inlineCallbacks
    def ask(self, source, question):
        """Ask a question.

        @param source: who is asking the question
        @param question: question asked
        @return: deferred answer
        """
        custid = hashlib.sha1("IPOO+%s" % source).hexdigest()
        xml = yield client.getPage(
            'http://www.pandorabots.com/pandora/talk-xml?%s' % urllib.urlencode(
                {'botid': self.botid,
                 'custid': custid,
                 'input': question}),
            method='GET')

        # Got XML, try to parse it
        try:
            dom = minidom.parseString(xml)
        except:
            raise AliceError, "Unable to parse XML"
        result = dom.getElementsByTagName("result")
        if not result:
            raise AliceError, "Invalid answer"
        if result[0].getAttribute('status') != u'0':
            raise AliceError, "Invalid status"
        answer = result[0].getElementsByTagName("that")
        if not answer:
            raise AliceError, "No answer"

        # Tweak a bit the answer and return back
        answer = answer[0].firstChild.data
        for rep in (("<br>", ""), ("ALICE", "IPoo")):
            answer = answer.replace(rep[0], rep[1])
        defer.returnValue([answer])

if __name__ == "__main__":
    import sys
    from twisted.internet import reactor

    a = Alice()
    d = a.ask("Vince", sys.argv[1])
    d.addCallback(lambda x: sys.stdout.write("%s\n" % x))
    d.addBoth(lambda _: reactor.stop())
    reactor.run()
