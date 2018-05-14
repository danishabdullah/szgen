from __future__ import print_function, unicode_literals

from szgen.consts import POSTGRES_TYPES, DATA_PATH, API_PATH, API_RPC_PATH, PRIVILEGES_PATH, POSTGRES_SERIAL_TYPES, \
    AUTH_LIB_API_TYPES_PATH, AUTH_LIB_API_RPC_PATH, AUTH_LIB_DATA_PATH, AUTH_LIB_BASE, TAB, AUTH_LIB_USER_DATA_PATH, \
    QOUTED_ENUM
from szgen.errors import InvalidModelDefinition
from szgen.templates import sql
from szgen.utils import separate_type_info_and_params, get_json_from_dict, remove_extra_white_space

__author__ = 'danishabdullah'
__all__ = ('SQLCompiler',)


def compile_collected_partials(partials_collector, relay_on=False):
    data_path = DATA_PATH / 'schema.sql'
    if relay_on:
        relay_user_import = sql.statements.relay_user_import.substitute()
        relay_uisetups_import = sql.statements.relay_uisetups_import.substitute()
    else:
        relay_uisetups_import = relay_user_import = ''
    data_string = sql.data.schema.substitute(data_table_imports=('\n').join(partials_collector.data_schema),
                                             relay_user_import=relay_user_import,
                                             relay_uisetups_import=relay_uisetups_import)
    api_path = API_PATH / 'schema.sql'
    api_string = sql.api.schema.substitute(api_view_imports=('\n').join(partials_collector.api_schema))
    authorization_path = PRIVILEGES_PATH / 'privileges.sql'
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

    def __init__(self, name, tb_spec, relay_on=False):
        if not isinstance(tb_spec, dict):
            raise AssertionError
        self.relay_on = relay_on
        self.table_name = name
        self._model_def = {name: tb_spec}
        self.column_definitions = tb_spec['columns']
        self.enum_definitions = tb_spec.get('enums', [])
        self.domain_definitions = tb_spec.get('domains', [])
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
        self.rabbitmq_definition = tb_spec.get('rabbitmq', {}).get('include', '')
        self.index_definitions = tb_spec.get('indices')
        self.data_path = DATA_PATH / self.table_name if name != 'user' else AUTH_LIB_USER_DATA_PATH
        self.api_path = API_PATH / self.table_name
        self.enforce_postgres_types()
        self.announce_table_columns()

    def announce_table_columns(self):
        pretty_names = "\n".join(['{}{}'.format(TAB, name) for name in self.all_columns])
        print("Following columns will be created for table '{}':\n{}".format(
            self.table_name, pretty_names))

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
    def pg_domain_names(self):
        return [domain['name'] for domain in self.domain_definitions]

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

    def enforce_domain_and_enums_dont_overlap(self):
        for domain in self.pg_domain_names:
            try:
                assert domain not in self.enum_names
            except AssertionError as e:
                raise InvalidModelDefinition("Domain and Enum share name '{}' for table '{}'".format(domain,
                                                                                                     self.table_name))

    def enforce_postgres_types(self):
        """Returns known postgres only types referenced in user supplied model"""
        all_types = self.enum_names.copy()
        all_types.extend(self.pg_domain_names)
        all_types.extend(POSTGRES_TYPES)
        for n in self.types:
            try:
                if n not in all_types:
                    raise AssertionError
            except AssertionError as e:
                raise InvalidModelDefinition(
                    ("Column type '{}' not allowed for table '{}'. Columns can only be of one of {}").format(n,
                                                                                                             self.table_name,
                                                                                                             all_types))

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
            if nullable or nullable is None:
                modifier = ''
            else:
                modifier = 'not null'
            return modifier

        def get_default_modifier(column_def):
            default = column_def.get('default', None)
            column_type = column_def.get('type')
            if default is None:
                modifier = ''
            elif type(default) != str: # handle booleans/ints/floats gracefully
                modifier = "default {}".format(str(default).lower())
            elif default == 'current_timestamp':
                modifier = "default CURRENT_TIMESTAMP"
            elif str(default).startswith("settings.") or str(default).startswith("request."):
                modifier = "default {}".format(default)
            else:
                modifier = "default '{}'::{}".format(default, column_type)
            return modifier

        def get_primary_key_modifier(column_def):
            primary_key = column_def.get('primary_key', None)
            if not primary_key:
                modifier = ''
            else:
                modifier = 'primary key'
            return modifier

        res = ([],  # columns
               [],  # references
               [])  # checks

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
            modifiers = " " + modifiers if modifiers else ''

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
            join_string.join(res[0]) + "," if (res[0] and (res[1] or res[2])) else join_string.join(res[0]),  # columns
            join_string.join(res[1]) + "," if (res[1] and res[2]) else join_string.join(res[1]),  # references
            join_string.join(res[2]))  # checks

    @property
    def all_columns(self):
        """Return names of all the columns referenced in user supplied model"""
        return [col['name'] for col in self.all_columns_defs]

    @property
    def compiled_table(self):
        """Returns compiled table sql"""


        column_defs, reference_column_defs, check_defs = self.all_compiled_columns
        rabbitmq_columns = self.rabbitmq_definition
        filename = self.data_path / ('{}.sql').format(self.table_name)
        updated_at_trigger = (
            sql.statements.updated_at_trigger.substitute(table_name=self.table_name)) if self.include_updated_at else ''
        if self.table_name == 'user':
            encrypt_pass_trigger = sql.statements.encrypt_password_trigger.substitute()
        else:
            encrypt_pass_trigger = ''
        if rabbitmq_columns:
            rabbitmq_columns = ",".join(['"{}"'.format(col.strip()) for col in rabbitmq_columns.split(',')])
            rabbitmq_trigger = sql.statements.send_data_to_rabbit_mq_trigger.substitute(table_name=self.table_name,
                                                                                        rabbitmq_columns=rabbitmq_columns)
        else:
            rabbitmq_trigger = ''
        string = sql.data.table.substitute(table_name=self.table_name, column_defs=column_defs,
                                           reference_column_defs=reference_column_defs,
                                           check_defs=check_defs,
                                           encrypt_password_trigger=encrypt_pass_trigger,
                                           send_data_to_rabbitmq_trigger=rabbitmq_trigger,
                                           updated_at_trigger=updated_at_trigger)
        return {filename: string}

    @property
    def compiled_view(self):
        """Returns compiled view sql"""
        view_name = self.view_name
        table_name = self.table_name
        excluded = [col.strip() for col in self.api_definition.get('exclude', '').split(',') if col]
        view_columns = [column for column in self.all_columns if
                        (column not in excluded and column not in self.primary_key_names)]
        primary_key = self.primary_key_names[0]
        filename = self.api_path / ('{}.sql').format(view_name)
        join_string = (',\n{}').format(TAB)
        if self.relay_on:
            relay_col = sql.statements.relay_col.substitute()
            pkey_name = 'row_id'
        else:
            relay_col = ''
            pkey_name = primary_key
        string = sql.api.view.substitute(view_name=view_name, primary_key=primary_key, table_name=table_name,
                                         column_names=join_string.join(view_columns), relay_col=relay_col,
                                         pkey_name=pkey_name)
        return {filename: string}

    @property
    def compiled_privilege_file(self):
        """Returns compiled privilege files sql"""

        def get_rls_statemet(privilege_for='all'):
            if privilege_for == 'all':
                return sql.statements.rls_all
            if privilege_for == 'self':
                return sql.statements.rls_self
            if privilege_for == 'none':
                return ''
            if privilege_for:
                return privilege_for
            raise InvalidModelDefinition((
                "RLS privileges can be one of ['all', 'self', sql_str ]. '{}' is provided for table '{}' and is invalid.").format(
                privilege_for, self.table_name))

        def api_user_permissions(alter_grant_type):
            if alter_grant_type == 'none':
                return 'select'
            else:
                return 'select, insert, update, delete'

        filename = PRIVILEGES_PATH / ('{}.sql').format(self.table_name)
        no_rls = (self.rls_alter == self.rls_read == 'all') or (self.rls_alter == 'none')
        api_permissions = api_user_permissions(self.rls_alter)
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
                                                             pkey_index_name=pkey_index_name,
                                                             api_permissions=api_permissions)
        return {filename: string}

    @property
    def compiled_privilege_partial(self):
        """Returns compiled privileges sql"""
        return {
            'authorization.privileges': sql.statements.privileges_file_import.substitute(table_name=self.table_name)}

    @property
    def compiled_relay(self):
        """"Returns compiled relay_id sql"""
        if not self.relay_on:
            return {}
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

        res = {}
        for enum in self.enum_definitions:
            enum_name = enum['name']
            filename = ('{}.sql').format(enum_name)
            _qouted_ = QOUTED_ENUM.findall(enum['options'])
            if _qouted_:
                enum_options = [x[1].strip()+"'" for x in _qouted_ if x]
            else:
                enum_options = [x.strip() for x in enum['options'].split(',') if x]
            _qouted_ = QOUTED_ENUM.findall(enum.get('display_names', ''))
            if _qouted_:
                print(_qouted_)
                enum_display_names = [x[1].strip()+"'" for x in _qouted_ if x]
            else:
                enum_display_names = [x.strip() for x in enum.get('display_names', '').split(',') if x]
            compiled_enum_options = compiled_options(enum_options)
            if not enum_display_names:
                enum_json_dict = {x.title(): x for x in enum_options}
            else:
                try:
                    assert len(enum_options) == len(enum_display_names)
                except AssertionError as e:
                    print(enum.get('display_names', ''))
                    print("These don't match:", enum_options, enum_display_names, sep='\n')
                    raise AssertionError("`options` for {} must correspond to `display_names`.".format(self.table_name))
                enum_json_dict = {display_name: value for display_name, value in zip(enum_display_names, enum_options)}
            minified_json = get_json_from_dict(enum_json_dict)
            pretty_json_commented_out = get_json_from_dict(enum_json_dict, prettified=True, commented_out_sql=True)
            enum_file_path = ('types/{}').format(filename)
            file_name = self.data_path / enum_file_path
            res[file_name] = sql.data.enum.substitute(table_name=self.table_name, enum_options=compiled_enum_options,
                                                      enum_name=enum_name,
                                                      enum_json_min=minified_json,
                                                      enum_json_pretty_commented_out=pretty_json_commented_out)
        return res

    @property
    def compiled_domains(self):
        res = {}
        for domain in self.domain_definitions:
            domain_name = domain['name']
            domain_type = domain['type']
            domain_condition = domain['check']
            domain_file_path = self.data_path / "types/{}.sql".format(domain_name)
            res[domain_file_path] = sql.data.domain.substitute(domain_name=domain_name, domain_type=domain_type,
                                                               check_sql=domain_condition)
        return res

    @property
    def compiled_type_file_imports(self):
        res = {}
        imports = []
        for enum in self.enum_definitions:
            enum_name = enum['name']
            imports.append(sql.statements.sql_file_import.substitute(filename=enum_name))

        for domain in self.domain_definitions:
            domain_name = domain['name']
            imports.append(sql.statements.sql_file_import.substitute(filename=domain_name))

        imports = ('\n').join(imports)
        res[self.data_path / 'types/all.sql'] = sql.data.all_types.substitute(table_name=self.table_name,
                                                                              type_imports=imports)
        return res


    @property
    def compiled_data_schema_import_partial(self):
        """Returns compiled data schema sql"""
        if self.table_name in ('user', 'uisetup'):
            return {}
        table_type_import = sql.statements.table_type_import.substitute(table_name_lowercased=self.table_name)
        if self.relay_on:
            relay_import = sql.statements.relay_import.substitute(table_name_lowercased=self.table_name)
        else:
            relay_import = ''
        table_import = sql.statements.table_import.substitute(table_name_lowercased=self.table_name)
        res = sql.statements.data_table_import.substitute(table_name_titlecased=self.table_name.title(),
                                                          table_type_imports=table_type_import,
                                                          table_import=table_import,
                                                          relay_import=relay_import)
        return {'data.schema': res}

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
        res.update(self.compiled_domains)
        res.update(self.compiled_type_file_imports)
        res.update(self.compiled_api_rpc)
        res.update(self.compiled_table)
        res.update(self.compiled_view)
        res.update(self.compiled_authorization_roles)
        if self.relay_on:
            res.update(self.compiled_relay)
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
