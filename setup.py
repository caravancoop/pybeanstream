#!/usr/bin/env python

try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

setup(name='beanstream',
      version='0.1',
      description='Payment module to talk with the Beanstream API',
      author='Benoit C. Sirois',
      author_email='benoitcsirois@gmail.com',
      namespace_packages=['beanstream',], 
      packages=find_packages(),
      install_requires=['suds',],
     )
