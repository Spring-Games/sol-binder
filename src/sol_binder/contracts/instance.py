from collections import defaultdict
from logging import Logger
from typing import *
from warnings import warn

from eth_typing import HexAddress
from hexbytes import HexBytes
from web3 import Web3
from web3.contract import Contract, ContractEvents, ContractFunction, ContractEvent, ContractFunctions
from web3.types import Nonce, TxParams, EventData

from ..solbinder_logging import get_solbinder_logger
from ..nonce.base import AbstractNonceManager
from ..project.config import ProjectConfig, ContractDeploymentData
from ..contracts.event import BaseEventGroup
from ..tx_logging import BaseTransactionLogger

ToBlock = NewType('ToBlock', Union[int, Literal["latest"]])


class ContractInstancingError(Exception):
    pass


class CannotDetermineNonceError(Exception):
    pass


class TransactionBuildError(Exception):
    def __init__(self, inner_ex: Exception):
        self.ex = inner_ex


class TransactionExecutionError(Exception):
    def __init__(self, inner_ex: Exception):
        self.ex = inner_ex


E = TypeVar('E', bound=BaseEventGroup)


class ContractInstance(Generic[E]):
    CONTRACT_NAME: Optional[str] = None
    events: E = None

    def __init__(self, nonce_manager: AbstractNonceManager, contract: "Contract", creator_account: HexAddress,
                 private_key: str = None, account: str = None,  # put these in a single arg, call it default_tx_creds
                 tx_logger: BaseTransactionLogger = None
                 ):
        self.__w3: Web3 = contract.web3
        self.__nonce_manager: AbstractNonceManager = nonce_manager
        self._contract: "Contract" = contract

        self.__creator_account: HexAddress = creator_account

        self.__private_key = private_key
        self.__default_account = account or creator_account
        self.__tx_logger = tx_logger

        try:
            event_group_class = self.__get_event_group_class()
        except NotImplementedError:
            pass
        else:
            self.events: E = event_group_class(self)

    @classmethod
    def from_project(cls, project_config: ProjectConfig = None, contract_name: str = None, network_name: str = None,
                     private_key: str = None) -> "ContractInstance":
        if project_config is None:
            project_config = ProjectConfig.load_project_config()
        if contract_name is None:
            if cls.CONTRACT_NAME is None:
                raise ContractInstancingError("Either specify `contract_name` or override cls.CONTRACT_NAME")
            contract_name = cls.CONTRACT_NAME
        deployment_data = project_config.get_deployment_data(contract_name)
        nonce = project_config.get_nonce_manager(network_name)
        tx_logger = project_config.create_tx_logger(contract_name)

        return cls.from_deployment_data(deployment_data, nonce, tx_logger, private_key)

    @classmethod
    def from_deployment_data(cls, config: ContractDeploymentData, nonce_manager: AbstractNonceManager = None,
                             tx_logger=None, private_key=None) -> "ContractInstance":

        w3 = ProjectConfig.load_project_config().get_w3()
        hashed_address = Web3.toChecksumAddress(config.contract_address)
        raw_contract = w3.eth.contract(address=hashed_address, abi=config.abi)

        return cls(nonce_manager, raw_contract, config.account, private_key, tx_logger=tx_logger)

    @property
    def address(self):
        return self._contract.address

    @property
    def creator_account(self) -> HexAddress:
        """Account who ran the transaction that created this contract"""
        return self.__creator_account

    @property
    def web3(self):
        return self.__w3

    def get_receipt_events(self, tx_hash: HexBytes) -> List[EventData]:
        """
        Generate a list of all events that have been fired by this transaction

        :raise Exception: If the transaction isn't done (no receipt) or if the transaction isn't from this contract.
        """
        receipt = self.__w3.eth.get_transaction_receipt(tx_hash)
        logs: List[EventData] = []
        for event_class in self._contract.events:
            event: ContractEvent = event_class()
            i: EventData
            logs += [i for i in event.processReceipt(receipt)]

        return logs

    def iter_events(
            self, event_name: str, from_block: int, to_block: "ToBlock") -> Iterable[EventData]:
        """Get all log entries for events of the given name fired by this contract."""
        event_filter = self._contract.events[event_name].createFilter(fromBlock=from_block, toBlock=to_block)
        for event_data in sorted(event_filter.get_all_entries(), key=lambda x: x['blockNumber']):
            yield event_data

    def call(self, func_name, *args) -> Any:
        # not clear why casting is required. Without the cast, Pycharm thinks func is of type ABIFunction
        func: ContractFunction = cast(ContractFunction, self._contract.functions[func_name])
        return func(*args).call()

    def transact(self, func_name: str, func_args, tx_args: TxParams = defaultdict()) -> Optional[HexBytes]:
        """
        :param func_name:
        :param func_args:
        :param tx_args: from=0xaddr, to=0xaddr, value=1000
               value is in wei
        :return:
        """
        if not tx_args.get('from'):
            tx_args['from'] = self.__default_account
        func: ContractFunction = cast(ContractFunction, self._contract.functions[func_name])
        nonce = self.__get_nonce_for_transact(tx_args)
        tx_args.update({"nonce": nonce, })

        try:
            tx = func(*func_args).buildTransaction(tx_args)
        except Exception as e:
            raise TransactionBuildError(e)

        logger: Optional[Logger] = self._get_logger()
        msg = f"Doing transaction {func_name} on contract {self.address}. Function arguments: {func_args}" \
              f"Transaction arguments: {tx_args}"
        logger.info(msg)

        try:
            if self.__private_key is None:
                # Assume its an 'unlocked test account' if we don't have a private key
                tx_hash = self.__w3.eth.send_transaction(tx)
            else:
                signed_trans = self.__w3.eth.account.sign_transaction(tx, private_key=self.__private_key)
                tx_hash = self.__w3.eth.send_raw_transaction(signed_trans.rawTransaction)
        except Exception as e:
            raise TransactionExecutionError(e)
        if self.__tx_logger:
            self.__tx_logger.log_transaction(tx_hash, func_name, func_args)
        return tx_hash

    def __get_nonce_for_transact(self, params: TxParams) -> Nonce:
        manual_nonce = params.pop('nonce', None)
        account: HexAddress = cast(HexAddress, params.get('from', self.creator_account))

        if manual_nonce:
            return manual_nonce
        elif not self.__nonce_manager:
            warn("Bypassing nonce-manager")
            # todo: deprecate this flow. If we have no nonce and no manager we should fail.
            return self.__w3.eth.get_transaction_count(account)
        else:
            return self.__nonce_manager.get_and_increment(account)

    def _get_logger(self) -> Optional[Logger]:
        return get_solbinder_logger()

    @classmethod
    def __get_event_group_class(cls) -> Type[E]:
        """
        :raises NotImplementedError: If the generic hasn't been fixed
        """
        kls = get_args(cls.__orig_bases__[0])[0]
        if type(kls) == TypeVar:
            raise NotImplementedError
        else:
            return kls


__all__ = ["TransactionBuildError", "TransactionExecutionError", "ContractInstance", "CannotDetermineNonceError"]
