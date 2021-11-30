""" EEA VERSIONS
"""
HAS_ARCHETYPES = True
try:
    from Products.Archetypes import atapi
except ImportError:
    HAS_ARCHETYPES = False