from __future__ import print_function, unicode_literals

from string import Template

__author__ = "danishabdullah"

privilege_file = Template("""\echo setting privileges for $table_name
-- grant appropriate $table_name permissions
$rls_statement
---- give access to the view owner
grant $api_permissions on data.$table_name to api;
-- give access to user groups
grant $api_permissions on api.$view_name to webuser;
$anonymous_user_permissions
""")
