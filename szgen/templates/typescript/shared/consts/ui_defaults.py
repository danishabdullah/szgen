from __future__ import print_function, unicode_literals

from string import Template

__author__ = "danishabdullah"

__all__ = ('ui_defaults',)

ui_defaults = Template("""import {UIOption} from '../interfaces/ui';
$ui_default_definitions""")