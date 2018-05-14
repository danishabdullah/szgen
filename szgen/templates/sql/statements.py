from string import Template

__author__ = "danishabdullah"

__all__ = ('insert_into', 'column_definition', 'column_check', 'foreign_key', 'updated_at_trigger',
           'create_extension', 'index_definition', 'where_clause', 'grant_definition', 'table_import',
           'table_type_import', 'relay_import', 'view_import', 'data_table_import', 'data_table_import',
           'api_schema_import', 'api_rpc_import', 'sql_file_import', 'enum_option', 'column_modifiers', 'rls_self',
           'rls_all', 'rls_statement', 'privileges_file_import', 'serial_pkey_index_name', 'pkey_index_name',
           'encrypt_password_trigger', 'send_data_to_rabbit_mq_trigger', 'relay_col')

insert_into = Template("""insert into $table_name ($table_columns)
values
    ($column_types);""")
column_definition = Template("""$column_name $column_type$column_modifiers""")
column_modifiers = Template(""" $given_modifiers $primary_key_modifier $null_modifier $default_modifier""")
column_check = Template("""check ($check_statement)""")
foreign_key = Template(
    """$column_name $column_type references "$reference_table"("$reference_column") $column_modifiers""")
updated_at_trigger = Template("""create trigger updated_at_mdt
    before update on "$table_name"
    for each row
    execute procedure moddatetime (updated_at);
""")
create_extension = Template("CREATE EXTENSION IF NOT EXISTS $extention_name WITH SCHEMA $schema_name;")
index_definition = Template(
    """CREATE $is_unique INDEX IF NOT EXISTS $index_name ON $table_name USING $method ($column_name) $where_clause;""")

where_clause = Template("WHERE $condition")

grant_definition = Template("""grant $privilege_name on $table_name to $roles;""")

table_import = Template("""\ir $table_name_lowercased/$table_name_lowercased.sql""")

table_type_import = Template("""\ir $table_name_lowercased/types/all.sql""")

relay_import = Template("\ir relay/${table_name_lowercased}_id.sql")
view_import = Template("""-- $table_name
\ir $table_name_lowercased/${view_name}.sql
""")

data_table_import = Template("""-- $table_name_titlecased
$table_type_imports
$table_import
$relay_import
""")
api_schema_import = Template("""$view_import
$api_rpc_import
""")

api_rpc_import = Template("""\ir rpc/${view_name}.sql""")

sql_file_import = Template("""\ir $filename.sql""")

relay_col = Template("""data.relay_id(t.*) as id,""")

enum_option = Template("""'$enum_option'""")

rls_self = "(request.user_role() = 'webuser' and request.user_id() = owner_id)"
rls_all = "(request.user_role() = 'webuser')"

rls_statement = Template("""alter table data.$table_name enable row level security;
create policy ${table_name}_access_policy on data.$table_name to api 
using (
    -- who can view row
    $read_permission
)
with check (
    -- who can alter row
    $alter_permission
);""")

privileges_file_import = Template("""\ir ${table_name}.sql""")
serial_pkey_index_name = Template("${table_name}_${primary_key}_seq")
pkey_index_name = Template("${table_name}_pkey")

encrypt_password_trigger = Template("""create trigger user_encrypt_pass_trigger
    before insert or update on "user"
    for each row
    execute procedure auth.encrypt_pass();
""")

send_data_to_rabbit_mq_trigger = Template("""-- attach the trigger to send events to rabbitmq
-- there is a 8000 bytes hard limit on the message payload size (PG NOTIFY) so it's better not to send data that is not used
-- on_row_change call can take the following forms
-- on_row_change() - send all columns
-- on_row_change('{"include":["id"]}'::json) - send only the listed columns
-- on_row_change('{"exclude":["bigcolumn"]}'::json) - exclude listed columns from the payload

create trigger send_change_event
    after insert or update or delete on "$table_name"
    for each row execute procedure rabbitmq.on_row_change('{"include":[$rabbitmq_columns]}');
""")