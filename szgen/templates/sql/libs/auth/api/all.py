from __future__ import print_function, unicode_literals

from string import Template

__author__ = "danishabdullah"

__all__ = ("all")

all = Template("""\echo Importing all types and rpcs necessary for authentication
\ir types/session.sql
\ir rpc/me.sql
\ir rpc/login.sql
\ir rpc/refresh_token.sql
\ir rpc/signup.sql
""")
