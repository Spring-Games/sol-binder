import base64
import hashlib

from deprecated import deprecated
from pathlib import Path
from typing import *
import os

from web3 import Web3
from solcx import compile_source
from web3.types import TxReceipt

from .project.config import ContractDeploymentData


def contract_folder() -> str:
    """Fully qualified path of folder that holds Solidity contracts"""

    # We don't want to import sol_binder here because it could cause an import loop.
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'contracts')


class ContractTool(object):
    def __init__(self, w3: Web3, import_path: str, chain_id: int):
        self.import_path = import_path
        self.w3 = w3
        self.chain_id = chain_id

    def __get_default_account(self):
        return self.w3.eth.accounts[0]

    def _compiles(self, source, solc_version='latest') -> dict:
        compiled_contract = compile_source(source,
                                           solc_version=solc_version,
                                           allow_paths=self.import_path)
        return compiled_contract

    def _deploy_compiled(self, compiled_contract: dict, account_address: Optional[str] = None,
                         private_key: Optional[str] = None, nonce: Optional[int] = None,
                         *contructor_args, **kwargs) -> TxReceipt:
        """

        :param private_key: 
        :param account_address: 
        :param compiled_contract: 
        :return: Deployed Contract ABI 
        """
        if account_address is None:
            account_address = self.__get_default_account()
        if nonce is None:
            nonce = self.w3.eth.get_transaction_count(account_address)

        contract_id, contract_interface = list(compiled_contract.items())[-1]
        abi = contract_interface['abi']
        contract_bytecode = contract_interface['bin']
        contract_base = self.w3.eth.contract(abi=abi, bytecode=contract_bytecode)

        trans_data = {'gasPrice': self.w3.eth.gas_price, 'chainId': self.chain_id, 'from': account_address,
                      'nonce': nonce}
        if private_key:

            transaction = contract_base.constructor(*contructor_args, **kwargs).buildTransaction(trans_data)
            signed_transaction = self.w3.eth.account.sign_transaction(transaction, private_key=private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_transaction.rawTransaction)
        else:
            tx_hash = contract_base.constructor(*contructor_args, **kwargs).transact(trans_data)
        tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

        return tx_receipt

    def deploy(self, file_path: str, account_address: Optional[str] = None,
               solc_version: str = "latest", *args, **kwargs) -> ContractDeploymentData:
        """

        :param account_address:
        :param solc_version:
        :param file_path:
        :return: Deployed Contract ABI
        """
        with open(file_path, 'r') as f:
            source = f.read()
        return self.deploys(source, account_address, *args, **kwargs)

    def deploys(self, source: str, account_address: Optional[str] = None, private_key: Optional[str] = None,
                solc_version: str = "latest", args: list = None, kwargs: dict = None) -> ContractDeploymentData:

        if kwargs is None:
            kwargs = dict()
        if args is None:
            args = list()
        compiled_contract = self._compiles(source, solc_version=solc_version)
        contract_id, contract_interface = list(compiled_contract.items())[-1]
        abi = contract_interface['abi']
        tx_receipt: TxReceipt = self._deploy_compiled(compiled_contract, account_address, private_key, None, *args,
                                                      **kwargs)

        return ContractDeploymentData(
            abi=abi,
            contract_address=tx_receipt['contractAddress'],
            tx_hash=base64.b64encode(bytes(tx_receipt['transactionHash'])).decode(),
            account=account_address,
            chain_id=self.chain_id,
            w3_url=self.w3.manager.provider.endpoint_uri,
            source_hash=self.hash_source(source),
            deployment_cost_wei=tx_receipt['gasUsed'] * self.w3.eth.gas_price,
        )

    @classmethod
    def hash_source(cls, processed_source: str) -> str:
        return hashlib.md5(processed_source.encode()).hexdigest()
