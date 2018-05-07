from __future__ import print_function, unicode_literals

from string import Template

__author__ = "danishabdullah"

__all__ = ('domain',)

domain = Template("""\echo # Creating '$domain_name' as a domain type
create domain $domain_name as $domain_type
check ($check_sql)
;
""")
