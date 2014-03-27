# -*- coding:utf-8 -*-
#
# Copyright 2012 NAMD-EMAP-FGV
#
# This file is part of PyPLN. You can get more information at: http://pypln.org/.
#
# PyPLN is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PyPLN is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with PyPLN.  If not, see <http://www.gnu.org/licenses/>.

from setuptools import setup, find_packages


def get_requirements():
    with open('requirements/production.txt') as requirements_fp:
        requirements = requirements_fp.readlines()
    packages = []
    for package in requirements:
        package = package.split('#')[0].strip()
        if '==' in package:
            package = package.split('==')[0].strip()
        if package:
            packages.append(package)
    return packages

setup(name='pypln.web',
      version='0.1.0d',
      author=('Álvaro Justen <alvarojusten@gmail.com>',
              'Flávio Amieiro <flavioamieiro@gmail.com>',
              'Flávio Codeço Coelho <fccoelho@gmail.com>',
              'Renato Rocha Souza <rsouza.fgv@gmail.com>'),
      author_email='pypln@googlegroups.com',
      url='https://github.com/NAMD/pypln.web',
      description='Distributed natural language processing pipeline - Web interface',
      zip_safe=False,
      packages=find_packages(),
      include_package_data=True,
      namespace_packages=["pypln"],
      install_requires=get_requirements(),
      test_suite='nose.collector',
      license='GPL3',
)
