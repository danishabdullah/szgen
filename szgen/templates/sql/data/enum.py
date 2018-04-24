from __future__ import print_function, unicode_literals

from string import Template

__author__ = "danishabdullah"

__all__ = ('enum',)

enum = Template("""\echo # Creating $enum_name type for $table_name
create type attitude as enum (
    $enum_options
);

insert into data.uisetup ($enum_name, details)
values
    ('$enum_name', '$enum_json_min'::jsonb)
    ;

-- prettified json structure is as follows
$enum_json_pretty_commented_out

""")
