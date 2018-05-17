from __future__ import print_function, unicode_literals

from string import Template

__author__ = "danishabdullah"

__all__ = ('ui_interfaces',)

ui_interfaces = Template("""interface Option {
  [index: string]: string;
}

export interface UIOption {
  options: Option;
}

export interface UIOptions {
  [index: string]: UIOption;
}

""")
