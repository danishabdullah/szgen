from __future__ import print_function, unicode_literals

from string import Template

__author__ = "danishabdullah"

__all__ = ("schema",)

schema = Template("""drop schema if exists data cascade;
create schema data;
set search_path = data, public;

select settings.set('auth.data-schema', current_schema);

create extension moddatetime;
create extension cube;
create extension earthdistance;

-- Uisetup
\ir uisetup/types/all.sql
\ir uisetup/uisetup.sql


-- import the type specifying the types of users we have (this is an enum).
\ir ../libs/auth/data/user/types/all.sql
\ir ../libs/auth/data/user/user.sql

-- import our application models

$data_table_imports
""")
