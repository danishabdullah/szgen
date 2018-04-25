# uncompyle6 version 3.1.3
# Python bytecode 3.6 (3379)
# Decompiled from: Python 3.6.5 |Anaconda, Inc.| (default, Mar 29 2018, 13:32:41) [MSC v.1900 64 bit (AMD64)]
# Embedded file name: c:\users\danishabdullah\onedrive\code\explorations\szgen\szgen\compilers.py
# Compiled at: 2018-04-24 01:52:18
# Size of source mod 2**32: 19793 bytes
from __future__ import print_function, unicode_literals

from szgen.consts import POSTGRES_TYPES, DATA_PATH, API_PATH, API_RPC_PATH, PRIVILEGES_PATH, POSTGRES_SERIAL_TYPES, \
    AUTH_LIB_API_TYPES_PATH, AUTH_LIB_API_RPC_PATH, AUTH_LIB_DATA_PATH, AUTH_LIB_BASE, TAB
from szgen.errors import InvalidModelDefinition
from szgen.templates import sql
from szgen.utils import separate_type_info_and_params, get_json_from_dict, remove_extra_white_space

__author__ = 'danishabdullah'
__all__ = ('SQLCompiler',)


def compile_collected_partials(partials_collector):
    data_path = DATA_PATH / 'schema.sql'
    data_string = sql.data.schema.substitute(data_table_imports=('\n').join(partials_collector.data_schema))
    api_path = API_PATH / 'schema.sql'
    api_string = sql.api.schema.substitute(api_view_imports=('\n').join(partials_collector.api_schema))
    authorization_path = PRIVILEGES_PATH / 'schema.sql'
    authorization_string = sql.authorization.privileges.substitute(
        import_privilege_files=(';\n').join(partials_collector.authorization_privileges))
    return {data_path: data_string,
            api_path: api_string,
            authorization_path: authorization_string}


class SQLCompiler(object):
    """
    Class for compiling and producing a Sql Alchemy model from user provided definition.
    
    Everything is implemented as a property for rapid development without any  thought
    for speed.
    """

    def __init__(self, name, tb_spec):
        if not isinstance(tb_spec, dict):
            raise AssertionError
        self.table_name = name
        self._model_def = {name: tb_spec}
        self.column_definitions = tb_spec['columns']
        self.enum_definitions = tb_spec.get('enums', [])
        self.include_created_at = tb_spec.get('include', {}).get('created_at', True)
        self.include_updated_at = tb_spec.get('include', {}).get('updated_at', True)
        if self.include_updated_at:
            self.column_definitions.append({
                'name': 'updated_at',
                'type': 'timestamp with time zone',
                'default': 'current_timestamp',
                'nullable': False
            })
        if self.include_created_at:
            self.column_definitions.append({
                'name': 'created_at',
                'type': 'timestamp with time zone',
                'default': 'current_timestamp',
                'nullable': False
            })
        self.foreign_key_definitions = tb_spec.get('foreign_keys', [])
        self.rls_read = tb_spec.get('rls', {}).get('read', 'all')
        self.rls_alter = tb_spec.get('rls', {}).get('alter', 'all')
        self.api_definition = tb_spec.get('api', {})
        self.rabbitmq_definition = tb_spec.get('rabbitmq', {})
        self.index_definitions = tb_spec.get('indices')
        self.data_path = DATA_PATH / self.table_name if name != 'user' else AUTH_LIB_DATA_PATH
        self.api_path = API_PATH / self.table_name
        self.enforce_postgres_types()
        print("Following columns will be created for table '{}':\n{}{}".format(self.table_name, TAB,
                                                                               self.all_columns))

    @property
    def all_columns_defs(self):
        all_cols = self.column_definitions.copy()
        all_cols.extend(self.foreign_key_definitions)
        return all_cols

    @property
    def longest_column_name(self):
        return max(self.all_columns, key=len)

    def get_padding(self, name):
        max_len = len(self.longest_column_name)
        desired_len = max_len + 8 - len(name)
        return ''.ljust(desired_len)


    @property
    def required_columns(self):
        res = []
        for column in self.all_columns_defs:
            nullable = column.get('nullable', True)
            modifiers = column.get('modifiers')
            if not nullable or 'not null' in modifiers:
                res.append(column)

        return res

    @property
    def enum_names(self):
        return [enum['name'] for enum in self.enum_definitions]

    @property
    def view_name(self):
        """Pluralises the table_name using utterly simple algo and returns as table_name"""
        if not self.table_name:
            raise ValueError
        else:
            table_name = self.table_name
        last_letter = table_name[-1]
        if last_letter in ('y',):
            return ('{}ies').format(table_name[:-1])
        elif last_letter in ('s',):
            return ('{}es').format(table_name)
        else:
            return ('{}s').format(table_name)

    @staticmethod
    def get_column_type(string):
        return separate_type_info_and_params(string)[0]

    @staticmethod
    def get_type_params(string):
        return separate_type_info_and_params(string)[1]

    @property
    def types(self):
        """All the unique types found in user supplied model"""
        res = []
        for column in self.all_columns_defs:
            tmp = column.get('type', None)
            res.append(SQLCompiler.get_column_type(tmp)) if tmp else False

        res = list(set(res))
        return res

    def enforce_postgres_types(self):
        """Returns known postgres only types referenced in user supplied model"""
        all_types = self.enum_names.copy()
        all_types.extend(POSTGRES_TYPES)
        for n in self.types:
            try:
                if not n in all_types:
                    raise AssertionError
            except AssertionError as e:
                raise InvalidModelDefinition(
                    ("Column type '{}' not allowed. Columns can only be of one of {}").format(n, all_types))

    @property
    def primary_keys(self):
        res = []
        for column in self.column_definitions:
            if 'primary_key' in column.keys():
                tmp = column.get('primary_key', None)
                res.append(column) if tmp else False

        return res

    @property
    def primary_key_names(self):
        """Returns the primary keys referenced in user supplied model"""
        return [column['name'] for column in self.primary_keys]

    @property
    def all_compiled_columns(self):
        """Returns compiled column definitions"""

        def get_null_modifier(column_def):
            nullable = column_def.get('nullable', True)
            if nullable:
                modifier = ''
            else:
                modifier = 'not null'
            return modifier

        def get_default_modifier(column_def):
            default = column_def.get('default', None)
            if not default:
                modifier = ''
            else:
                modifier = ('default {}').format(default)
            return modifier

        def get_primary_key_modifier(column_def):
            primary_key = column_def.get('primary_key', None)
            if not primary_key:
                modifier = ''
            else:
                modifier = 'primary key'
            return modifier

        res = ([], # columns
               [], # references
               []) # checks

        for column in self.all_columns_defs:
            # figure out the modifiers
            null_modifier = get_null_modifier(column)
            default_modifier = get_default_modifier(column)
            given_modifiers = column.get('modifiers', '')
            primary_key_modifier = get_primary_key_modifier(column)
            modifiers = sql.statements.column_modifiers.substitute(given_modifiers=given_modifiers,
                                                                   null_modifier=null_modifier,
                                                                   default_modifier=default_modifier,
                                                                   primary_key_modifier=primary_key_modifier)
            # cleanup lingering whitespace
            modifiers = remove_extra_white_space(modifiers)

            # prettify and make it easier on the eyes to read long tables
            column_name = column.get('name')
            column_type = column.get('type')
            padding = self.get_padding(column_name)
            column_type = "{padding}{column_type}".format(padding=padding, column_type=column_type)

            # make reference work
            reference = column.get('references', {})
            if reference:
                res[1].append(sql.statements.foreign_key.substitute(column_name=column_name, column_type=column_type,
                                                                    column_modifiers=modifiers,
                                                                    reference_table=reference['table'],
                                                                    reference_column=reference['column']))
            else:
                res[0].append(
                    sql.statements.column_definition.substitute(column_name=column_name, column_type=column_type,
                                                                column_modifiers=modifiers))
            check = column.get('check', '')
            if check:
                res[2].append(sql.statements.column_check.substitute(check_statement=check))

        join_string = (',\n{}').format(TAB)
        return (
            join_string.join(res[0]), # columns
            join_string.join(res[1]), # references
            join_string.join(res[2])) # checks

    @property
    def all_columns(self):
        """Return names of all the columns referenced in user supplied model"""
        return [col['name'] for col in self.all_columns_defs]

    @property
    def compiled_table(self):
        """Returns compiled table sql"""

        def get_rabbitmq_columns(column_string):
            res = [('"{}"').format(column_name) for column_name in column_string.split(',')]
            return (', ').join(res)

        column_defs, reference_column_defs, check_defs = self.all_compiled_columns
        print(reference_column_defs)
        rabbitmq_columns = get_rabbitmq_columns(self.rabbitmq_definition.get('columns', ''))
        filename = self.data_path / ('{}.sql').format(self.table_name)
        updated_at_trigger = (
            sql.statements.updated_at_trigger.substitute(table_name=self.table_name)) if self.include_updated_at else ''
        string = sql.data.table.substitute(table_name=self.table_name, column_defs=column_defs,
                                           reference_column_defs=reference_column_defs,
                                           check_defs=check_defs,
                                           rabbitmq_columns=rabbitmq_columns,
                                           updated_at_trigger=updated_at_trigger)
        return {filename: string}

    @property
    def compiled_view(self):
        """Returns compiled view sql"""
        view_name = self.view_name
        table_name = self.table_name
        excluded = self.api_definition.get('exclude', [])
        view_columns = [column for column in self.all_columns if
                        column not in excluded or column not in self.primary_key_names]
        primary_key = self.primary_key_names[0]
        filename = self.api_path / ('{}.sql').format(view_name)
        join_string = (',\n{}').format(TAB)
        string = sql.api.view.substitute(view_name=view_name, primary_key=primary_key, table_name=table_name,
                                         column_names=join_string.join(view_columns))
        return {filename: string}

    @property
    def compiled_privilege_file(self):
        """Returns compiled privilege files sql"""

        def get_rls_statemet(privilege_for='all'):
            if privilege_for == 'all':
                return sql.statements.rls_all
            if privilege_for == 'self':
                return sql.statements.rls_self
            raise InvalidModelDefinition((
                                             "RLS privileges can be one of ['all', 'self.]. '{}' is provided for table '{}' and is invalid.").format(
                privilege_for, self.table_name))

        filename = PRIVILEGES_PATH / ('{}.sql').format(self.table_name)
        no_rls = self.rls_alter == self.rls_read == 'all'
        pkey_col = self.primary_keys[0]
        if pkey_col['type'] in POSTGRES_SERIAL_TYPES:
            pkey_index_name = sql.statements.serial_pkey_index_name.substitute(table_name=self.table_name,
                                                                               primary_key=pkey_col['name'])
        else:
            pkey_index_name = sql.statements.pkey_index_name.substitute(table_name=self.table_name)
        if no_rls:
            rls_statement = ''
        else:
            rls_statement = sql.statements.rls_statement.substitute(read_permission=get_rls_statemet(self.rls_read),
                                                                    alter_permission=get_rls_statemet(self.rls_alter),
                                                                    table_name=self.table_name)
        string = sql.authorization.privilege_file.substitute(table_name=self.table_name, rls_statement=rls_statement,
                                                             pkey_index_name=pkey_index_name)
        return {filename: string}

    @property
    def compiled_privilege_partial(self):
        """Returns compiled privileges sql"""
        return {
            'authorization.privileges': sql.statements.privileges_file_import.substitute(table_name=self.table_name)}

    @property
    def compiled_relay(self):
        """"Returns compiled relay_id sql"""
        primary_key = self.primary_key_names[0]
        res = sql.data.relay.substitute(table_name=self.table_name, primary_key=primary_key)
        fpath = self.data_path / ('../relay/{}_id.sql').format(self.table_name)
        return {fpath: res}

    @property
    def compiled_enums(self):
        """Returns compiled enums sql files"""

        def compiled_options(enum_options):
            res = []
            for x in enum_options:
                res.append(sql.statements.enum_option.substitute(enum_option=x))

            return (', ').join(res)

        imports = []
        res = {}
        for enum in self.enum_definitions:
            filename = ('{}.sql').format(enum['name'])
            enum_name = enum['name']
            enum_options = [x.strip() for x in enum['options'].split(',') if x]
            compiled_enum_options = compiled_options(enum_options)
            enum_json_dict = {x.title(): x for x in enum_options}
            minified_json = get_json_from_dict(enum_json_dict)
            pretty_json_commented_out = get_json_from_dict(enum_json_dict, prettified=True, commented_out_sql=True)
            enum_file_path = ('types/{}').format(filename)
            imports.append(sql.statements.sql_file_import.substitute(filename=filename))
            file_name = self.data_path / enum_file_path
            res[file_name] = sql.data.enum.substitute(table_name=self.table_name, enum_options=compiled_enum_options,
                                                      enum_name=enum_name,
                                                      enum_json_min=minified_json,
                                                      enum_json_pretty_commented_out=pretty_json_commented_out)

        imports = ('\n').join(imports)
        res[self.data_path / 'types/all.sql'] = sql.data.all_types.substitute(table_name=self.table_name,
                                                                              type_imports=imports)
        return res

    @property
    def compiled_data_schema_import_partial(self):
        """Returns compiled data schema sql"""
        table_type_import = sql.statements.table_type_import.substitute(table_name_lowercased=self.table_name)
        relay_import = sql.statements.relay_import.substitute(table_name_lowercased=self.table_name)
        table_import = sql.statements.table_import.substitute(table_name=self.table_name,
                                                              table_name_lowercased=self.table_name)
        res = sql.statements.data_table_import.substitute(table_type_imports=table_type_import,
                                                          table_import=table_import,
                                                          relay_import=relay_import)
        return {'data.schema': res}

    @property
    def compiled_authorization_schema(self):
        """Returns compiled auth schema sql"""
        fpath = PRIVILEGES_PATH / 'schema.sql'
        string = sql.authorization.schema.substitute()
        return {fpath: string}

    @property
    def compiled_authorization_roles(self):
        """Returns compiled auth schema sql"""
        fpath = PRIVILEGES_PATH / 'roles.sql'
        string = sql.authorization.roles.substitute()
        return {fpath: string}

    @property
    def compiled_authorization_files(self):
        """Returns compiled auth schema sql"""
        res = {}
        res.update(self.compiled_privilege_file)
        res.update(self.compiled_authorization_roles)
        res.update(self.compiled_authorization_schema)
        return res

    @property
    def compiled_api_rpc(self):
        """Returns compiled api rpc search sql"""
        filename = API_RPC_PATH / ('{}.sql').format(self.view_name)
        string = sql.api.search.substitute(view_name=self.view_name, primary_key=self.primary_key_names[0])
        return {filename: string}

    @property
    def compiled_api_schema_partial(self):
        """Returns compiled api schema sql"""
        view_import = sql.statements.view_import.substitute(table_name=self.table_name,
                                                            table_name_lowercased=self.table_name,
                                                            view_name=self.view_name)
        api_rpc_import = sql.statements.api_rpc_import.substitute(view_name=self.view_name)
        return {'api.schema': sql.statements.api_schema_import.substitute(view_import=view_import,
                                                                          api_rpc_import=api_rpc_import)}

    @property
    def compiled_auth_lib_session_type(self):
        """Returns compiled auth lib session type sql"""
        filepath = AUTH_LIB_API_TYPES_PATH / 'session.sql'
        string = sql.libs.auth.api.types.session.substitute()
        return {filepath: string}

    @property
    def compiled_auth_lib_schema(self):
        """Returns compiled auth lib data schema sql"""
        fpath = AUTH_LIB_BASE / 'schema.sql'
        string = sql.libs.auth.schema.substitute()
        return {fpath: string}

    @property
    def compiled_auth_lib_user_type(self):
        """Returns compiled auth lib user type sql"""
        filepath = AUTH_LIB_API_TYPES_PATH / 'user.sql'
        string = sql.libs.auth.api.types.user.substitute()
        return {filepath: string}

    @property
    def compiled_auth_lib_api_rpcs(self):
        """Returns compiled auth lib api rpcs sql"""
        login_path = AUTH_LIB_API_RPC_PATH / 'login.sql'
        login_string = sql.libs.auth.api.rpc.login.substitute()
        me_path = AUTH_LIB_API_RPC_PATH / 'me.sql'
        me_string = sql.libs.auth.api.rpc.me.substitute()
        refresh_token_path = AUTH_LIB_API_RPC_PATH / 'refresh_token.sql'
        refresh_token_string = sql.libs.auth.api.rpc.refresh_token.substitute()
        signup_path = AUTH_LIB_API_RPC_PATH / 'signup_token.sql'
        signup_string = sql.libs.auth.api.rpc.signup.substitute()
        return {login_path: login_string,
                me_path: me_string,
                refresh_token_path: refresh_token_string,
                signup_path: signup_string}

    @property
    def compiled_files(self):
        """Returns all the compiled sql files referenced through their paths"""
        res = {}
        res.update(self.compiled_privilege_file)
        res.update(self.compiled_enums)
        res.update(self.compiled_authorization_schema)
        res.update(self.compiled_api_rpc)
        res.update(self.compiled_table)
        res.update(self.compiled_relay)
        res.update(self.compiled_view)
        res.update(self.compiled_authorization_roles)
        res.update(self.compiled_authorization_schema)
        if self.table_name == 'user':
            res.update(self.compiled_auth_lib_api_rpcs)
            res.update(self.compiled_auth_lib_schema)
            res.update(self.compiled_auth_lib_session_type)
            res.update(self.compiled_auth_lib_user_type)
        return res

    @property
    def compiled_sql_partials(self):
        """Returns all the compiled sql partials to be stitched according to their keys"""
        res = {}
        res.update(self.compiled_api_schema_partial)
        res.update(self.compiled_data_schema_import_partial)
        res.update(self.compiled_privilege_partial)
        return res
