from __future__ import print_function, unicode_literals

from string import Template

__author__ = "danishabdullah"

__all__ = ('view',)

view = Template("""\echo # Creating $view_name view
set search_path = api, public;
create or replace view $view_name as
select 
    $relay_col
    $primary_key as $pkey_name,
    $column_names
from data.$table_name t;
alter view $view_name owner to api; -- it is important to set the correct owner to the RLS policy kicks in
""")
