#!/usr/bin/env python2
#coding=utf-8

try:
    from setuptools import setup

    install_requires = [
    'selenium >= 2.4.0',
    'xvfbwrapper',
    'python-magic',
    'oauth2client',
    'gdata',
    'pdfminer == 20110515',#Note that API has changed dramatically in later versions
    'docx', #good for text, bad for metadata
    'openxmllib', #good for metadata, bad for text
    'pytesseract',
    'argcomplete',
    'pyOpenSSL',  # required, in practice, by oauth2client
    'boto'
    ]

    try:
        import argparse
    except ImportError:
        install_requires.append('argparse')

    kws = {'install_requires': install_requires}
except ImportError:
    from distutils.core import setup
    kws = {}

setup(	name='protokollen',
		version='0.1',
		description='This package contains the ProtoCollection Python tools',
		url='https://github.com/rotsee/protokollen',
		license='MIT',
		**kws
	)
