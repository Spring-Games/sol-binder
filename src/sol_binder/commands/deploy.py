import base64
import hashlib
import json
import os
from typing import *

import click
from hexbytes import HexBytes
from web3.exceptions import TransactionNotFound

from ..binder import SolBinder
from ..commands.errors import W3ConnectionError, ContractAlreadyDeployedError, ContractDeploymentError
from ..contract_tool import ContractTool
from ..project.config import ProjectConfig, ContractDeploymentData


def deploy_all(*args, solbinder_config: ProjectConfig = None,
               on_already_deployed: Callable = None, **kwargs):
    if solbinder_config is None:
        solbinder_config = ProjectConfig.load_project_config()
    for deployment_plan in solbinder_config.iter_deployment_plans():
        try:
            deploy_contract(deployment_plan.name, *args, **kwargs)
        except ContractAlreadyDeployedError:
            if not on_already_deployed:
                raise
            on_already_deployed(deployment_plan)


def deploy_contract(contract_name: str, account: str, private_key: str, solc_version: str,
                    solbinder_config: ProjectConfig = None,
                    verbose: bool = False, force: bool = False):
    if solbinder_config is None:
        solbinder_config = ProjectConfig.load_project_config()
    deployment_cache_path = solbinder_config.deploy_cache_dir
    if not os.path.isdir(deployment_cache_path):
        os.makedirs(deployment_cache_path)
        # Build the constructor arguments

    binder = SolBinder(verbose=verbose, import_path=solbinder_config.imports_cache_dir)
    w3 = solbinder_config.get_w3()
    chain_id = solbinder_config.get_network_info()["network_id"]
    deployment_plan = solbinder_config.get_deployment_plan(contract_name)
    contract_args = deployment_plan.args
    if not w3.isConnected():
        raise W3ConnectionError("Error connecting to w3")
    contract_tool = ContractTool(w3, binder.import_path, chain_id)
    with open(deployment_plan.filepath) as contract_handle:
        source = contract_handle.read()
    processed_source = binder.bind(source)

    source_hash = ContractTool.hash_source(processed_source)

    try:
        deployment_data = solbinder_config.get_deployment_data(contract_name)
        tx_hash = HexBytes(base64.b64decode(deployment_data.tx_hash))
        w3.eth.get_transaction_receipt(tx_hash)
        if source_hash == deployment_data.source_hash and not force:
            raise ContractAlreadyDeployedError(f"Contract '{contract_name}' already deployed!")
    except FileNotFoundError:
        pass
    except TransactionNotFound:
        pass

    if account is None:
        account = w3.eth.accounts[0]
    try:
        deployed_contract: ContractDeploymentData = contract_tool.deploys(
            processed_source, account, private_key, solc_version=solc_version, args=contract_args)
    except TypeError as e:
        raise ContractDeploymentError(e)
    click.secho(f"gas used in ETH: {w3.fromWei(deployed_contract.deployment_cost_wei, 'ether')}", fg="yellow")

    deployed_contract.save(
        solbinder_config.get_deployment_filepath(contract_name)
    )

    click.secho(f"Deployed contract address: {deployed_contract.contract_address}", fg="green")
    return deployed_contract
