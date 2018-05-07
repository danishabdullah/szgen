from __future__ import print_function, unicode_literals

from string import Template

__author__ = "danishabdullah"

__all__ = ('schema',)

schema = Template("""\echo Creating the api schema
drop schema if exists api cascade;
create schema api;
set search_path = api, public;

-- this role will be used as the owner of the views in the api schema
-- it is needed for the definition of the RLS policies
drop role if exists api;
create role api;
grant api to current_user; -- this is a workaround for RDS where the master user does not have SUPERUSER priviliges  

-- redefine this type to control the user properties returned by auth endpoints
\ir ../libs/auth/api/types/user.sql
-- include all auth endpoints
\ir ../libs/auth/api/all.sql

-- our endpoints
$api_view_imports
""")
