from typing import *

import click

from ..commands.errors import ContractDeploymentError, ContractAlreadyDeployedError, W3ConnectionError
from ..project.config import ProjectConfig
from ..commands.deploy import deploy_contract as _deploy_contract, deploy_all


@click.command()
@click.option("-u", "--account", default=None, help="blockchain account address")
@click.option("-p", "--private-key", "private_key", default=None, help="Private Key required for transactions")
@click.option("-s", "--solc-version", default=None, help="Sol compiler version")
@click.option("-n", "--network", "network_name", default="dev", help="Name of network to use")
@click.argument("contract", required=False)
@click.pass_context
def deploy_contract(ctx, account: str, private_key: str, network_name: str, solc_version: str, contract: str):
    solbinder_config = ProjectConfig.load_project_config(ctx.obj['project_path'])
    if solc_version is None:
        solc_version = solbinder_config.solc_version
    if contract is None:
        deploy_all(account=account,
                   private_key=private_key,
                   solc_version=solc_version,
                   solbinder_config=solbinder_config,
                   on_already_deployed=lambda p: click.secho(f"Contract already deployed!", fg="green"))
    else:
        _try_deploy_contract(account=account,
                             private_key=private_key,
                             solc_version=solc_version,
                             solbinder_config=solbinder_config,
                             verbose=ctx.obj['verbose'],
                             contract_name=contract)


def _try_deploy_contract(*args, **kwargs):
    try:
        return _deploy_contract(*args, **kwargs)
    except W3ConnectionError:
        click.secho(f"Error connecting to W3 network", fg="red")
    except ContractAlreadyDeployedError:
        click.secho(f"Contract already deployed!", fg="green")
    except ContractDeploymentError as e:
        click.secho(f"Contract deployment failed: {e}", fg="red")
