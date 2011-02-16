#!/usr/bin/env python
#
# Copyright(c) 1999 Benoit Clennett-Sirois
#
# Benoit Clennett-Sirois hereby disclaims all copyright interest in
# the program “PyBeanstream”.
#
# This file is part of PyBeanstream.
#
# PyBeanstream is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PyBeanstream is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with PyBeanstream.  If not, see http://www.gnu.org/licenses/

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
