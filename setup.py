try:
    from setuptools import setup

    install_requires = ['selenium >= 2.4.0', 'xvfbwrapper', 'python-magic']

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
		description='This package contains the protokollen harvester',
		url='https://github.com/rotsee/protokollen',
		license='MIT',
		**kws
	)