from __future__ import print_function, unicode_literals

import errno
from os import getcwd, path, makedirs

import click
import yaml

from szgen.compilers import SQLCompiler, compile_collected_partials
from szgen.errors import DirectoryCreationException, FileNotFound, InvalidModelDefinition
from szgen.utils import check_nodes, PartialsCollector

__author__ = 'danishabdullah'


def check_or_create_models_dir(destination=None):
    dir = destination or ('{}/Models').format(getcwd())
    if not path.exists(dir):
        click.echo(("Didn't find {}. Creating now.").format(dir))
        try:
            makedirs(dir)
        except Exception as e:
            raise DirectoryCreationException

        return dir


def parse_yaml(yaml_string):
    model_defs = yaml.load(yaml_string)
    if not isinstance(model_defs, dict):
        raise AssertionError
    for model_name, model in model_defs.items():
        check_nodes(model_name, model, 'columns.name')
        # check_nodes(model_name, model, 'columns.type', POSTGRES_TYPES)
        check_nodes(model_name, model, 'rls.read', ['all', 'self', str])
        check_nodes(model_name, model, 'rls.alter', ['all', 'self', 'none', str])

    return model_defs


def get_model_defs(yaml):
    model_defs = parse_yaml(yaml)
    return model_defs


def get_all_user_defined_types(model_defs):
    enums = []
    domains = []
    for name, defi in model_defs.items():
        enums.extend([item['name'] for item in defi.get('enums', [])])
        domains.extend([item['name'] for item in defi.get('domains', [])])
    return enums, domains


@click.command()
@click.option('--destination', '-d', help="Destination directory. Default will assume 'output_directory' "
                                          "directory inside the current working directory",
              type=click.Path(exists=True))
@click.option('--relay/--no-relay', '-r', help="Make `relay` columns and functions. Turned off by default",
              default=False)
@click.argument('yaml', type=click.File('r', encoding='utf-8'))
def cli(yaml, destination, relay):
    click.echo(('Creating Models with the following options:\n  --yaml:{}').format(yaml.name))
    yaml_string = yaml.read().lower()
    yaml.close()
    destination = destination or "output_directory"
    if destination.endswith('/'):
        destination = destination[:len(destination) - 1]
        click.echo(('Trimmed destination to {}').format(destination))

    click.echo('Destination is {}'.format(destination))
    try:
        model_defs = get_model_defs(yaml=yaml_string)
    except FileNotFound:
        click.echo('The yaml file does not exist. Exiting!')
        return

    enums, domains = get_all_user_defined_types(model_defs)
    common = set(enums).intersection(set(domains))
    try:
        assert len(common) == 0
    except AssertionError as e:
        raise InvalidModelDefinition("Enums and Domains cannot share names. See `{}`".format(common))
    partials_collector = PartialsCollector([], [], [])
    files_collector = {}
    for name, model in model_defs.items():
        click.echo('Compiling model "{}"'.format(name))
        other_enums = [n for n in enums if n not in [item['name'] for item in model.get('enums', [])]]
        other_domains = [n for n in domains if n not in [item['name'] for item in model.get('domains', [])]]
        sql = SQLCompiler(name, model, other_enum_names=other_enums, other_domain_names=other_domains, relay_on=relay)
        sql_partials = sql.compiled_sql_partials
        partials_collector.api_schema.append(sql_partials['api.schema'])
        ds_partial = sql_partials.get('data.schema', None)
        if ds_partial:
            partials_collector.data_schema.append(ds_partial)
        partials_collector.authorization_privileges.append(sql_partials['authorization.privileges'])
        files_collector.update(sql.compiled_files)

    compiled_partials = compile_collected_partials(partials_collector, relay_on=relay)
    files_collector.update(compiled_partials)
    click.echo("Writing {} files".format(len(files_collector.items())))
    for fpath, content in sorted(files_collector.items()):
        full_fpath = ('{}').format(destination) / fpath
        if not path.exists(path.dirname(full_fpath)):
            try:
                makedirs(path.dirname(full_fpath))
            except OSError as exc:
                if exc.errno != errno.EEXIST:
                    raise
        try:
            click.echo(('Writing file at {}').format(full_fpath))
            full_fpath.write_text(content, encoding='utf-8')
        except IOError:
            click.echo(('A failure occured while writing to {}').format(full_fpath))


if __name__ == '__main__':
    cli()
