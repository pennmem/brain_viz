#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
from brainviewer import __version__

with open('README.md') as readme_file:
    readme = readme_file.read()

requirements = []
setup_requirements = []


setup(
    name='brainviewer',
    version=__version__,
    description="Pipeline for generating 3D brain visualizations in Blender",
    long_description=readme,
    author="Penn Computational Memory Lab",
    url='https://github.com/pennmem/brain_viz',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    keywords='brainview'
)
