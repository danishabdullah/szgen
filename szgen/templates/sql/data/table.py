from __future__ import print_function, unicode_literals

from string import Template

__author__ = "danishabdullah"

__all__ = ('table',)

table = Template("""\echo # Creating $table_name table
create table "$table_name"(
    -- Columns
    $column_defs
    
    -- References
    $reference_column_defs
    
    -- Checks
    $check_defs
);

create trigger send_change_event
after insert or update or delete on $table_name
for each row execute procedure rabbitmq.on_row_change('{"include":[$rabbitmq_columns]}');

$updated_at_trigger
""")
