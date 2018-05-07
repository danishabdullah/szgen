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

$encrypt_password_trigger
$send_data_to_rabbitmq_trigger
$updated_at_trigger
""")
