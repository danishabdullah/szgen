from __future__ import print_function, unicode_literals

from string import Template

__author__ = "danishabdullah"

__all__ = ('user_role',)

user_role = Template("""\echo # Creating user_role type for user
\echo # Creating user_role type for user
create type user_role as enum (
    $enum_options
    );
""")
