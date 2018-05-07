from __future__ import print_function, unicode_literals

from string import Template

__author__ = "danishabdullah"

__all__ = ('relay',)

relay = Template("""\echo # Installing relay_id($table_name)
create or replace function relay_id(data.$table_name) returns text as $$$$
select encode(convert_to('$table_name:' || $$1.$primary_key::text, 'utf-8'), 'base64')
$$$$ immutable language sql;
create index on data.$table_name (relay_id(data.$table_name.*)); 
""")
