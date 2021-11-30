""" EEA VERSIONS
"""
HAS_ARCHETYPES = True
try:
    from Products.Archetypes import atapi
    atapi.listTypes('eea.versions')
except ImportError:
    HAS_ARCHETYPES = False