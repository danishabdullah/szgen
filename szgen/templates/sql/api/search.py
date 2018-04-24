from __future__ import print_function, unicode_literals

from string import Template

__author__ = "danishabdullah"

__all__ = ('search',)

search = Template("""\echo # Creating search_${view_name} functionality
create or replace function search_${view_name}(query text) returns setof $view_name as $$$$
select * from $view_name where ${primary_key} like query
$$$$ stable language sql;
""")
