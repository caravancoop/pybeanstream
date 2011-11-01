#!/usr/bin/env python
# setup.py
# This file is part of PyBeanstream.
#
# Copyright(c) 2011 Benoit Clennett-Sirois. All rights reserved.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 3 of the License, or (at your option) any later version.

# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.

# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA 02110-1301  USA

try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

setup(name='PyBeanstream',
      version='0.3.2',
      description='Payment module to talk with the Beanstream API',
      author='Benoit C. Sirois',
      author_email='benoitcsirois@gmail.com',
      packages=find_packages(),
      namespace_packages=['pybeanstream',], 
      classifiers = [
        'Programming Language :: Python',
        'Topic :: Office/Business',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)',
        ],
      install_requires=['suds',],
      url='http://bitbucket.org/benoitcsirois/pybeanstream/',
      license='LICENSE.txt',
      long_description=open('README.txt').read(),
     )
