from Globals import package_home
from Products.CMFCore import utils as cmfutils
from Products.CMFCore.DirectoryView import registerDirectory
from os.path import dirname
import eea.versions.catalog


ppath = cmfutils.ProductsPath
cmfutils.ProductsPath.append(dirname(package_home(globals())))
registerDirectory('skins', globals())
cmfutils.ProductsPath = ppath


def initialize(context):
    """initialize product (called by zope)"""

