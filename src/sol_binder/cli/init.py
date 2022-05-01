import os
from typing import *

import click

__all__ = ['init']

from ..project.config import ProjectConfig
from ..project.errors import ProjectConfigAlreadyExistsError


@click.command()
@click.pass_context
def init(ctx):
    """Initialize a new sol-binder project in the current directory"""
    project_config = ProjectConfig()
    try:
        # create initial project config file
        project_config.create(None)
    except ProjectConfigAlreadyExistsError as e:
        click.secho(f"Found existing project file: {str(e)}", fg="red")
        exit(1)
    # Create contracts dir
    if not os.path.exists(project_config.contracts_dir):
        os.makedirs(project_config.contracts_dir)
