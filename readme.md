### szgen
A generation tool to bootstrap postgrest open-resty a la subzero cloud.

#### CLI Tool
```bash
$ szgen --help
Usage: szgen [OPTIONS] YAML

Options:
  -d, --destination PATH    Destination directory. Default will assume
                            'output_directory' directory inside the current
                            working directory
  -r, --relay / --no-relay  Make `relay` columns and functions. Turned off by
                            default
  --help                    Show this message and exit.
```


#### File Specification
```yaml
---------------------------------------------------------------------------------

table_name:
  enums?: # enums used in this table
    - name: string
      options: comma,separated,values
      display_names?: comma,separated,values,in,same,order,as,options
  domains?:
    - name: string
      type: 'bigint' | 'bigserial' | 'bit' | 'bit varying' | 'boolean' | 'box' | 'bytea' |
            'character' | 'character varying' | 'cidr' | 'circle' | 'date' | 'double precision' |
            'inet' | 'integer' | 'interval' | 'json' | 'jsonb' | 'line' | 'lseg' |
            'macaddr' | 'macaddr8' | 'money' | 'numeric' | 'path' | 'pg_lsn' | 'point' |
            'polygon' | 'real' | 'smallint' | 'smallserial' | 'serial' | 'text' |
            'time' | 'time with time zone' | 'timestamp' | 'timestamp with time zone' |
            'tsquery' | 'tsvector' | 'txid_snapshot' | 'uuid' | 'xml' | 'int8' |
            'serial8' | 'varbit' | 'bool' | 'char' | 'varchar' | 'float8' | 'int4' |
            'decimal' | 'float4' | 'int2' | 'serial2' | 'serial4' | 'timetz' | 'timestamptz' |
            'smallint' | 'array' | 'enum defined above'
      check: check_constraint_string
  columns:
    - name: string
      type: 'bigint' | 'bigserial' | 'bit' | 'bit varying' | 'boolean' | 'box' | 'bytea' |
            'character' | 'character varying' | 'cidr' | 'circle' | 'date' | 'double precision' |
            'inet' | 'integer' | 'interval' | 'json' | 'jsonb' | 'line' | 'lseg' |
            'macaddr' | 'macaddr8' | 'money' | 'numeric' | 'path' | 'pg_lsn' | 'point' |
            'polygon' | 'real' | 'smallint' | 'smallserial' | 'serial' | 'text' |
            'time' | 'time with time zone' | 'timestamp' | 'timestamp with time zone' |
            'tsquery' | 'tsvector' | 'txid_snapshot' | 'uuid' | 'xml' | 'int8' |
            'serial8' | 'varbit' | 'bool' | 'char' | 'varchar' | 'float8' | 'int4' |
            'decimal' | 'float4' | 'int2' | 'serial2' | 'serial4' | 'timetz' | 'timestamptz' |
            'smallint' | 'array' | 'enum defined above' | 'domain defined above'
      nullable?: false | true
      primary_key?: true | false
      default?: sql_string
      check?: check_constraint_string
      modifiers?: sql_string
  foreign_keys?:
    - name: string
      type: 'bigint' | 'bigserial' | 'bit' | 'bit varying' | 'boolean' | 'box' | 'bytea' |
            'character' | 'character varying' | 'cidr' | 'circle' | 'date' | 'double precision' |
            'inet' | 'integer' | 'interval' | 'json' | 'jsonb' | 'line' | 'lseg' |
            'macaddr' | 'macaddr8' | 'money' | 'numeric' | 'path' | 'pg_lsn' | 'point' |
            'polygon' | 'real' | 'smallint' | 'smallserial' | 'serial' | 'text' |
            'time' | 'time with time zone' | 'timestamp' | 'timestamp with time zone' |
            'tsquery' | 'tsvector' | 'txid_snapshot' | 'uuid' | 'xml' | 'int8' |
            'serial8' | 'varbit' | 'bool' | 'char' | 'varchar' | 'float8' | 'int4' |
            'decimal' | 'float4' | 'int2' | 'serial2' | 'serial4' | 'timetz' | 'timestamptz' |
            'smallint' | 'array' | 'enum defined above'
      nullable?: false | true
      primary_key?: true | false
      default?: sql_string
      check?: check_constraint_string
      modifiers?: sql_string
      references:
        table: name_of_table
        column: name_of_column
  rls:
    # row level security is automatically turned off if both read and alter are set to 'all'
    # row level security is automatically turned off if alter is 'none'
    # rls `self` depends on `owner_id` column please provide an explicit condition if you reference the user table differently
    read: "all" | "self" | sql_condition # assumed 'all' if absent
    alter: "all" | "self" | "none"  | sql_condition # assumed 'all' if absent
  api:
    exclude: comma,separated,names,of,columns # these columns will not be available to the api from this table
  include:
    created_at?: true | false # assumed true if absent
    updated_at?: true | false # assumed true if absent, also sets an automatic trigger based on extension moddate
  rabbitmq:
    include: comma,separated,list,of,columns # on every update of row, these columns will be sent in the rabbitmq stream

----------------------------------------------------------------------------------

```