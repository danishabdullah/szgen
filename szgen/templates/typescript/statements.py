from __future__ import print_function, unicode_literals

from string import Template

__author__ = "danishabdullah"

__all__ = ('ui_default_definition',)

ui_default_definition = Template("""export let $enum_name_capitalized: UIOption = {
  'options': $enum_json
};
""")

column_def = Template("""$column_name: $column_js_type""")

enum_type_def = Template("""type $enum_name = $enum_options_or_operand_separated;""")
