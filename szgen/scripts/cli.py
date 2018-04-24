from __future__ import print_function, unicode_literals

import errno
from os import getcwd, path, makedirs

import click
import yaml

from szgen.compilers import SQLCompiler, compile_collected_partials
from szgen.consts import POSTGRES_TYPES
from szgen.errors import DirectoryCreationException, FileNotFound
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
        check_nodes(model_name, model, 'rls.read', ['all', 'self'])
        check_nodes(model_name, model, 'rls.alter', ['all', 'self'])

    return model_defs


def get_model_defs(yaml):
    model_defs = parse_yaml(yaml)
    return model_defs


@click.command()
@click.option('--destination', '-d', help="Destination directory. Default will assume 'output_directory' "
                                          "directory inside the current working directory",
              type=click.Path(exists=True))
@click.argument('yaml', type=click.File('r'))
def cli(yaml, destination):
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

    partials_collector = PartialsCollector([], [], [])
    files_collector = {}
    for name, model in model_defs.items():
        click.echo('Compiling model "{}"'.format(name))
        sql = SQLCompiler(name, model)
        sql_partials = sql.compiled_sql_partials
        partials_collector.api_schema.append(sql_partials['api.schema'])
        partials_collector.data_schema.append(sql_partials['data.schema'])
        partials_collector.authorization_privileges.append(sql_partials['authorization.privileges'])
        files_collector.update(sql.compiled_files)

    compiled_partials = compile_collected_partials(partials_collector)
    files_collector.update(compiled_partials)
    click.echo("Writing {} files".format(len(files_collector.items())))
    for fpath, content in files_collector.items():
        full_fpath = ('{}').format(destination) / fpath
        if not path.exists(path.dirname(full_fpath)):
            try:
                makedirs(path.dirname(full_fpath))
            except OSError as exc:
                if exc.errno != errno.EEXIST:
                    raise
        try:
            click.echo(('Writing file at {}').format(full_fpath))
            full_fpath.write_text(content)
        except IOError:
            click.echo(('A failure occured while writing to {}').format(full_fpath))


if __name__ == '__main__':
    cli()
