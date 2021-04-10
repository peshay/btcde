#!/usr/bin/env python
"""Setup to install Bitcoin.de API Python Module."""
from distutils.core import setup
setup(name='btcde',
      version='4.0',
      py_modules=['btcde'],
      install_requires=['requests', 'future'],
      description='API Wrapper for Bitcoin.de Trading API.',
      url='https://github.com/peshay/btcde',
      author='Andreas Hubert',
      author_email='anhubert@gmail.com',
      license='MIT',
      classifiers=['Development Status :: 5 - Production/Stable',
                   'Intended Audience :: Developers',
                   'Topic :: Software Development :: Libraries :: Application '
                   'Frameworks',
                   'License :: OSI Approved :: MIT License',
                   'Programming Language :: Python :: 3.6',
                   'Programming Language :: Python :: 3.8',
                   'Programming Language :: Python :: 3.9', ],
      keywords='bitcoin.de bitcoin btc api',

      )
