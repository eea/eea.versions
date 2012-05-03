"""setup
"""
import os
from os.path import join
from setuptools import setup, find_packages

name = 'eea.versions'
path = name.split('.') + ['version.txt']
version = open(join(*path)).read().strip()

setup(name=name,
      version=version,
      description="EEA versions",
      long_description=open("README.txt").read() + "\n" +
                       open(os.path.join("docs", "HISTORY.txt")).read(),
      classifiers=[
        "Framework :: Plone",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ],
      keywords='eea, dataservice, data, service',
      author='Alec Ghica (Eaudeweb), Tiberiu Ichim (Eaudeweb), '
             'Antonio De Marinis (EEA), European Environment Agency',
      author_email='webadmin@eea.europa.eu',
      url='http://svn.eionet.europa.eu/projects/Zope',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['eea'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          #'p4a.common',
          #'collective.indexing',
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
