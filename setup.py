import sys
import twisted
from distutils.core import setup, Extension
from ipoo import VERSION

if __name__ == "__main__":
    setup(name="ipoo",
          version=VERSION,
          classifiers = [
            'Development Status :: 4 - Beta',
            'Environment :: No Input/Output (Daemon)',
            'Environment :: Web Environment',
            'Framework :: Twisted',
            'Intended Audience :: System Administrators',
            'License :: OSI Approved :: GNU General Public License (GPL)',
            'Operating System :: POSIX',
            'Programming Language :: Python',
            'Topic :: System :: Networking',
            ],
          url='https://trac.luffy.cx/ipoo/',
          description='IP lookup utility',
          author='Vincent Bernat',
          author_email="bernat@luffy.cx",
          ext_modules= [
            Extension('ipoo.collector.snmp',
                      libraries = ['netsnmp', 'crypto'],
                      sources= ['ipoo/collector/snmp.c']),
            ],
          packages=["ipoo",
                    "ipoo.collector",
                    "ipoo.collector.plugins",
                    "ipoo.core",
                    "ipoo.web",
                    "ipoo.xmpp",
                    "twisted.plugins"],
          package_data={'twisted': ['plugins/ipoo_plugin.py']}
          )
