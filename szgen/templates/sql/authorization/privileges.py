from __future__ import print_function, unicode_literals

from string import Template

__author__ = "danishabdullah"

__all__ = ('privileges',)

privileges = Template("""\echo # Loading roles privilege

-- this file contains the privileges of all applications roles to each database entity
-- if it gets too long, you can split it one file per entity

-- set default privileges to all the entities created by the auth lib
select auth.set_auth_endpoints_privileges('api', :'anonymous', enum_range(null::data.user_role)::text[]);

-- specify which application roles can access this api (you'll probably list them all)
-- remember to list all the values of user_role type here
grant usage on schema api to anonymous, webuser;

-- grant access to webuser to all the relevant sequences
grant usage on all sequences in schema data to webuser;
-------------------------------------------------------------------------------
-- grant appropriate uisetup permissions
grant select on api.uisetups to webuser;
grant select on api.uisetups to anonymous;
---- give access to the view owner
grant select on data.uisetup to api;
-------------------------------------------------------------------------------
$import_privilege_files
""")
