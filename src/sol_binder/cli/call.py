from typing import List

import click

from ..contracts.instance import ContractInstance
from ..cli.utils import parse_arguments
from ..project.config import ProjectConfig


@click.command()
@click.option("-n", "--network", "network_name", default="dev", help="Name of network to use")
@click.argument("contract_name")
@click.argument("function")
@click.argument("arguments", required=False, nargs=-1)
@click.pass_context
def call(ctx, network_name: str, contract_name: str, function: str, arguments: List[str]):
    solbinder_config = ProjectConfig.load_project_config(ctx.obj['project_path'])
    network_info = solbinder_config.get_network_info(network_name)
    try:
        deployment_data = solbinder_config.get_deployment_data(contract_name)
    except FileNotFoundError:
        click.secho(f"Contract '{contract_name}' not found", fg="red")
        exit(1)

    contract_instance = ContractInstance.from_deployment_data(deployment_data, None)

    args = parse_arguments(arguments)
    result = contract_instance.call(function, *args)
    click.echo(result)
