from __future__ import print_function, unicode_literals

from string import Template

__author__ = "danishabdullah"

__all__ = ("session",)

session = Template("""create type session as (me json, token text);""")
