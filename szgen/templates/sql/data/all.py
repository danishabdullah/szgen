from __future__ import print_function, unicode_literals

from string import Template

__author__ = "danishabdullah"

__all__ = ("all_types",)

all_types = Template("""\echo # Loading all the types necessary for $table_name data.
$type_imports
""")
