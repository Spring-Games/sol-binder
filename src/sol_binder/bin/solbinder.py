#!/usr/bin/env python3
import os

import click

from ..cli.call import call
from ..cli.compile import compile_sol
from ..cli.deploy import deploy_contract
from ..cli.transact import transact


@click.group()
@click.option("-v", "--verbose/--silent", default=False)
@click.option("-P", "--project-path", default=os.getcwd(), help="Project path where solbinder.yaml is")
@click.pass_context
def cli(ctx, verbose: bool, project_path: str):
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    ctx.obj['project_path'] = project_path


cli.add_command(compile_sol, name="compile")
cli.add_command(deploy_contract, name="deploy")
cli.add_command(call, name="call")
cli.add_command(transact, name="transact")

if __name__ == '__main__':
    cli()
