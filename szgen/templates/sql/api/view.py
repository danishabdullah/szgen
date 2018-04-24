from __future__ import print_function, unicode_literals

from string import Template

__author__ = "danishabdullah"

__all__ = ('view',)

view = Template("""\echo # Creating $view_name view
create or replace view $view_name as
select 
    data.relay_id(t.*) as id,
    $primary_key as row_id,
    $column_names
from data.$table_name t;
alter view $view_name owner to api; -- it is important to set the correct owner to the RLS policy kicks in
""")
