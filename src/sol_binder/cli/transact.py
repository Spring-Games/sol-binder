from typing import List, Optional

import click

from ..cli.utils import parse_arguments
from ..contracts.instance import ContractInstance
from ..project.config import ProjectConfig


@click.command()
@click.option("-u", "--account", "account", default=None, help="Account Address")
@click.option("-p", "--private-key", "private_key", default=None, help="Private Key required for transactions")
@click.option("-v", "--value", "value", default=0, help="Transaction Value")
@click.option("-N", "--nonce", "nonce", default=None, help="Specify nonce value manually")
@click.option("-n", "--network", "network_name", default="dev", help="Name of network to use")
@click.argument("contract_name")
@click.argument("function")
@click.argument("arguments", required=False, nargs=-1)
@click.pass_context
def transact(ctx, account: str, private_key: str, value: int,
             contract_name: str, network_name: str,
             function: str, arguments: List[str],
             nonce: Optional[int]):
    solbinder_config = ProjectConfig.load_project_config(ctx.obj['project_path'])
    try:
        deployment_data = solbinder_config.get_deployment_data(contract_name)
    except FileNotFoundError:
        click.secho(f"Contract '{contract_name}' not found", fg="red")
        exit(1)
    else:
        contract_instance = ContractInstance.from_deployment_data(deployment_data, None, private_key)
        w3 = contract_instance.web3
        args = parse_arguments(arguments)
        if account is None:
            account = w3.eth.accounts[0]
        tx_hash = contract_instance.transact(function, func_args=args,
                                             tx_params={'from': account, 'value': value, 'nonce': nonce})
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        gas_used = w3.fromWei(
            tx_receipt['gasUsed'] * w3.eth.gas_price,
            'ether'
        )
        click.echo(f"gas used in ETH: {gas_used}")
