============
EEA Versions
============
.. image:: https://ci.eionet.europa.eu/buildStatus/icon?job=eea/eea.versions/develop
  :target: https://ci.eionet.europa.eu/job/eea/job/eea.versions/job/develop/display/redirect
  :alt: develop
.. image:: https://ci.eionet.europa.eu/buildStatus/icon?job=eea/eea.versions/master
  :target: https://ci.eionet.europa.eu/job/eea/job/eea.versions/job/master/display/redirect
  :alt: master

EEA Versions is a versioning system based on a version ID to group certains
objects and EffectiveDate to determine version number.

.. note ::

  This add-on doesn't do anything by itself. It needs to be integrated by a
  developer within your own products. For reference you can check
  the `eea.sparql`_ package.


.. contents::


Installation
============

zc.buildout
-----------
If you are using `zc.buildout`_ and the `plone.recipe.zope2instance`_
recipe to manage your project, you can do this:

* Update your buildout.cfg file:

  * Add ``eea.versions`` to the list of eggs to install
  * Tell the `plone.recipe.zope2instance`_ recipe to install a ZCML slug

  ::

    [instance]
    ...
    eggs =
      ...
      eea.versions

    zcml =
      ...
      eea.versions

* Re-run buildout, e.g. with::

  $ ./bin/buildout

You can skip the ZCML slug if you are going to explicitly include the package
from another package's configure.zcml file.

Source code
===========

Latest source code (Plone 4 compatible):
- `Plone Collective on Github <https://github.com/collective/eea.versions>`_
- `EEA on Github <https://github.com/eea/eea.versions>`_

Copyright and license
=====================
The Initial Owner of the Original Code is European Environment Agency (EEA).
All Rights Reserved.

The EEA Versions (the Original Code) is free software;
you can redistribute it and/or modify it under the terms of the GNU
General Public License as published by the Free Software Foundation;
either version 2 of the License, or (at your option) any later
version.

Contributor(s)
--------------

- Tiberiu Ichim (Eau de Web),
- Alec Ghica (Eau de Web),
- Antonio De Marinis (European Environment Agency)

More details under docs/License.txt


Funding
=======

EEA_ - European Enviroment Agency (EU)

.. _EEA: https://www.eea.europa.eu/
.. _`eea.sparql`: https://eea.github.com/docs/eea.sparql
.. _`plone.recipe.zope2instance`: https://pypi.python.org/pypi/plone.recipe.zope2instance
.. _`zc.buildout`: https://pypi.python.org/pypi/zc.buildout
