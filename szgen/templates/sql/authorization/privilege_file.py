from __future__ import print_function, unicode_literals

from string import Template

__author__ = "danishabdullah"

privilege_file = Template("""-- grant appropriate $table_name permissions
$rls_statement
---- give access to the view owner
grant usage on data.$pkey_index_name to webuser;
grant select, insert, update, delete on data.$table_name to api;
""")
