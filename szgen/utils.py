from __future__ import print_function, unicode_literals

import json
import re
from collections import namedtuple

from szgen.errors import InvalidModelDefinition

__author__ = 'danishabdullah'
TYPE_INFO_REGEX = re.compile('(^\w+)((\(|\[).*(\]|\))|)?(\w+)?$')
PartialsCollector = namedtuple('PartialsCollector', ['api_schema', 'data_schema', 'authorization_privileges'])


def separate_type_info_and_params(string):
    for match in TYPE_INFO_REGEX.finditer(string):
        name, params, _, _, last_bit = match.groups()
        if last_bit:
            name = (' ').join([name, last_bit])
        return (name if name else '', params if params else '')

    return (string, '')


def enrich_models(model_defs):
    pass


def check_values(node, node_name, value_list):
    node_val, val_args = separate_type_info_and_params(node)
    if not value_list:
        raise ValueError('Cannot check values without provision of a value_list')
    if node_val not in value_list:
        raise InvalidModelDefinition(
            ("Invalid value '{}' for '{}'. Values for node '{}' should be one of {}").format(node_val, node_name,
                                                                                             node_name, value_list))


def get_path(model_def, path, prefix='>'):
    keys = path.split('.')
    el = model_def
    for idx, key in enumerate(keys):
        key_type = type(el)
        if key_type == list:
            for sub_el in el:
                new_path = ('.').join(keys[idx:])
                new_prefix = prefix + ('.').join(keys[:idx])
                yield from get_path(sub_el, new_path, new_prefix)

        else:
            el = el.get(key, None)
            full_path = ('.').join([prefix, path])
            if not el:
                raise InvalidModelDefinition(('{} must exit').format(full_path))
            if idx == len(keys) - 1:
                yield (
                    full_path, el)


def check_nodes(model_name, model, path='column.name', value_list=None):
    prefix = model_name + '>'
    for pair in get_path(model, path, prefix):
        node_name, node = pair
        if value_list:
            check_values(node, node_name, value_list)


def get_json_from_dict(dictionary, prettified=False, commented_out_sql=False):
    dump_params = {'indent': 0, 'sort_keys': True}
    if not prettified:
        dump_params = {'indent': 4,
                       'sort_keys': True}
    res = json.dumps(dictionary, **dump_params)
    if commented_out_sql:
        res = res.split('\n')
        res = ['--' + line for line in res]
        res = ('\n').join(res)
    return res
