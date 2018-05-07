from __future__ import print_function, unicode_literals

from string import Template

__author__ = "danishabdullah"


__all__ = ('table_interface',)

table_interface = Template("""export interface ${table_name_snakecased} {
  readonly $primary_key: 
  $interface_type_defs
};
""")