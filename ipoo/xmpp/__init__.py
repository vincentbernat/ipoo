"""
XMPP module
"""

class MixedMessage:
    """Message with both plain version and HTML"""
    def __init__(self, plain, html):
        self.plain = plain
        self.html = html
