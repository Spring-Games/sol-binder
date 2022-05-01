import click

from ..project.errors import ProjectConfigLocationError


class SolBinderClickGroup(click.Group):
    """Command group that handles generic solbinder errors"""

    def __call__(self, *args, **kwargs):
        try:
            return self.main(*args, **kwargs)
        except ProjectConfigLocationError as e:
            click.secho(str(e), fg="red")
            exit(1)
