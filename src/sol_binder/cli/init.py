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
        project_config.create(None)
    except ProjectConfigAlreadyExistsError as e:
        click.secho(f"Found existing project file: {str(e)}", fg="red")
