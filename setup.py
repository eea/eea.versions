"""setup
"""
import os
from setuptools import setup, find_packages

name = 'eea.versions'
path = name.split('.') + ['version.txt']
version = open(os.path.join(*path)).read().strip()

setup(name=name,
      version=version,
      description="EEA versions",
      long_description=open("README.txt").read() + "\n" +
                       open(os.path.join("docs", "HISTORY.txt")).read(),
      classifiers=[
          "Framework :: Zope2",
          "Framework :: Zope3",
          "Framework :: Plone",
          "Framework :: Plone :: 4.0",
          "Framework :: Plone :: 4.1",
          "Framework :: Plone :: 4.2",
          "Programming Language :: Zope",
          "Programming Language :: Python",
          "Topic :: Software Development :: Libraries :: Python Modules",
          "License :: OSI Approved :: GNU General Public License (GPL)",
          "License :: OSI Approved :: Mozilla Public License 1.0 (MPL)",
        ],
      keywords='eea versions',
      author='European Environment Agency',
      author_email="webadmin@eea.europa.eu",
      maintainer='Tiberiu Ichim (Eau de Web)',
      maintainer_email='tiberiu.ichim@eaudeweb.ro',
      download_url="http://pypi.python.org/pypi/eea.versions",
      url='http://eea.github.com/docs/eea.versions',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['eea'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'eea.rdfmarshaller',
          #'collective.indexing',
      ],
      extras_require={
          'test': [
              'plone.app.testing',
          ]
      },
      entry_points="""
      [z3c.autoinclude.plugin]
      target = plone
      """
      )
