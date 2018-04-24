# uncompyle6 version 3.1.3
# Python bytecode 3.6 (3379)
# Decompiled from: Python 3.6.5 |Anaconda, Inc.| (default, Mar 29 2018, 13:32:41) [MSC v.1900 64 bit (AMD64)]
# Embedded file name: c:\users\danishabdullah\onedrive\code\explorations\szgen\szgen\consts.py
# Compiled at: 2018-04-24 01:39:22
# Size of source mod 2**32: 2905 bytes
from __future__ import print_function, unicode_literals

from pathlib import Path

__author__ = 'danishabdullah'
__all__ = ('POSTGRES_TYPES', 'POSTGRES_TYPES_WITH_PARAMS', 'INDEX_METHODS', 'POSTGREST_ROLES',
           'GRANTABLES', 'MINIMUM_USER_COLUMNS', 'MINIMUM_USER_ROLES', 'POSTGRES_TYPES_WITH_PARAMS_MIDWAY',
           'DATA_PATH', 'API_PATH', 'PRIVILEGES_PATH', 'AUTH_LIB_USER_DATA_PATH',
           'AUTH_LIB_API_PATH', 'AUTH_LIB_API_RPC_PATH', 'TAB', 'AUTH_LIB_API_TYPES_PATH',
           'API_RPC_PATH', 'POSTGRES_SERIAL_TYPES', 'AUTH_LIB_DATA_PATH', 'AUTH_LIB_BASE')
POSTGRES_TYPES = ('bigint', 'bigserial', 'bit', 'bit varying', 'boolean', 'box', 'bytea',
                  'character', 'character varying', 'cidr', 'circle', 'date', 'double precision',
                  'inet', 'integer', 'interval', 'json', 'jsonb', 'line', 'lseg',
                  'macaddr', 'macaddr8', 'money', 'numeric', 'path', 'pg_lsn', 'point',
                  'polygon', 'real', 'smallint', 'smallserial', 'serial', 'text',
                  'time', 'time with time zone', 'timestamp', 'timestamp with time zone',
                  'tsquery', 'tsvector', 'txid_snapshot', 'uuid', 'xml', 'int8',
                  'serial8', 'varbit', 'bool', 'char', 'varchar', 'float8', 'int4',
                  'decimal', 'float4', 'int2', 'serial2', 'serial4', 'timetz', 'timestamptz',
                  'smallint', 'array')
POSTGRES_TYPES_WITH_PARAMS = ('bit', 'bit varying', 'character', 'char', 'character varying',
                              'varchar', 'decimal', 'interval', 'numeric', 'time',
                              'time with timezone', 'timestamp', 'timestamp with timezone',
                              'array')
POSTGRES_TYPES_WITH_PARAMS_MIDWAY = ('time with timezone', 'timestamp with timezone')
POSTGRES_SERIAL_TYPES = ('bigserial', 'smallserial', 'serial2', 'serial4', 'serial')
INDEX_METHODS = ('btree', 'hash', 'gist', 'spgist', 'gin', 'brin')
POSTGREST_ROLES = ('authenticaor', 'webuser', 'anonymous', 'api')
POSTGRES_NUMERIC_TYPES = ('smallint', 'integer', 'bigint', 'decimal', 'numeric', 'real',
                          'double precision', 'smallserial', 'serial', 'bigserial',
                          'int8', 'serial8', 'float8', 'int4', 'float4', 'int2',
                          'serial2', 'serial4')
POSTGRES_BOOLEAN_TYPES = ('boolean', 'bool')
POSTGRES_OBJECT_TYPES = ('json', 'jsonb', 'hstore')
POSTGRES_LIST_TYPES = ('ARRAY',)
GRANTABLES = ('select', 'insert', 'update', 'delete')
MINIMUM_USER_COLUMNS = ('id', 'email', 'password', 'role')
MINIMUM_USER_ROLES = ('webuser', 'anonymous')
DATA_PATH = Path('data')
API_PATH = Path('api')
API_RPC_PATH = API_PATH / 'rpc'
PRIVILEGES_PATH = Path('authorization')
AUTH_LIB_BASE = Path('lib/auth/')
AUTH_LIB_DATA_PATH = AUTH_LIB_BASE / 'data'
AUTH_LIB_USER_DATA_PATH = AUTH_LIB_DATA_PATH / 'user'
AUTH_LIB_API_PATH = AUTH_LIB_BASE / 'api'
AUTH_LIB_API_RPC_PATH = AUTH_LIB_API_PATH / 'rpc'
AUTH_LIB_API_TYPES_PATH = AUTH_LIB_API_PATH / 'types'
TAB = '    '
