#!/usr/bin/base_env python
# -*- encoding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function

import io
import re
from glob import glob
from os.path import basename
from os.path import dirname
from os.path import join
from os.path import splitext

from setuptools import find_packages
from setuptools import setup


def read(*names, **kwargs):
    return io.open(
        join(dirname(__file__), *names),
        encoding=kwargs.get('encoding', 'utf8')
    ).read()


setup(name='pugg',
      version='0.0.1',
      license='BSD 2-Clause License',
      install_requires=['click', 'pypandoc', 'sqlalchemy', 'flask', 'beautifulsoup4', 'python-dotfiles'],
      packages=find_packages('src'),
      package_dir={'': 'src'},
      py_modules=[splitext(basename(path))[0] for path in glob('src/*.py')],
      include_package_data=True,
      zip_safe=False,
      entry_points={
        'console_scripts': [
            'pugg = pugg.main:pugg',
        ]
    },
)
