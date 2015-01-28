#!/usr/bin/env python2
#coding=utf-8

try:
    from setuptools import setup

    install_requires = [
        'selenium >= 2.43.0',
        'xvfbwrapper',
        'python-magic',
        'oauth2client',
        'gdata',
        'pdfminer == 20140328',
        'python-docx',  # good for text, bad for metadata
        'openxmllib',  # good for metadata, bad for text
        'pytesseract',
        'argcomplete',
        'pyOpenSSL',  # required, in practice, by oauth2client
        'boto',
        'elasticsearch',
        'numpy',  # for nltk. Not *actually* needed.
        'nltk',
        'beautifulsoup4',
        'html5lib',
        'html2text',
        'rtf2xml',
        'httplib2 == 0.8',  # Known to work. Some 0.9 versions have problems with p12 certs
        'python-dateutil',
        'dropbox'  # For Dropbox storage or import
    ]

    try:
        import argparse
    except ImportError:
        install_requires.append('argparse')

    kws = {'install_requires': install_requires}
except ImportError:
    from distutils.core import setup
    kws = {}

setup(name='protokollen',
      version='0.1',
      description='This package contains the ProtoCollection Python tools',
      url='https://github.com/rotsee/protokollen',
      license='MIT',
      **kws
      )
