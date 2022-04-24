from typing import *
from logging import Logger

from eth_typing import HexAddress
from web3 import Web3
from web3.types import Nonce

from ..solbinder_logging import get_solbinder_logger


class AbstractNonceManager(object):
    """
    Manages the 'nonce', a sequential transaction index that is used for transaction orderign and security by the
    blockchain

    The nonce must reflect the correct sequence when sending a transaction.
    The nonce only advances when transactions are formed into blocks, which may take time.
    But you are expected to deliver the correct nonce for transactions, even if you have previous transactions waiting
    to join a block

    Example/Explanation
    -------------------
            Blockchain says your nonce is 5
            so you send a transaction (A) with nonce=5
            The blockchain still says your nonce is 5, because (A) is not committed to a block yet
            However, the next transaction (B) is expected to come with a nonce=6
            So it is up to us to manage the nonce ourselves

    This abstract class can be implemented in various ways. The simplest being an in-memory counter.
    However, if we have several distributed services sending transcations we can implement a redis-based variation
    if this class that uses an atomic redis counter, allowing multiple processes to coordinate transactions with a
    correct nonce
    """

    @classmethod
    def name(cls):
        raise NotImplementedError("Unnamed nonce manager")

    @classmethod
    def create(cls, w3: Web3, project_root: str,
               args: Union[str, dict, list, None]) -> "AbstractNonceManager":
        raise NotImplementedError("nonce manager does not implement class method 'create'")

    def __init__(self, w3: Web3):
        self.__w3 = w3

    @classmethod
    def _get_logger(cls) -> Logger:
        return get_solbinder_logger()

    def _tracked_accounts(self) -> List[HexAddress]:
        raise NotImplementedError

    def sync_from_chain(self, new_accounts: List[HexAddress] = tuple()):
        for account in self._tracked_accounts() + list(new_accounts):
            self._sync_from_chain(account)

    def _sync_from_chain(self, account: HexAddress):
        return self._set(account, self.__w3.eth.get_transaction_count(account))

    def get_and_increment(self, account: HexAddress) -> Nonce:
        nonce = self._get_and_increment(account)
        self._get_logger().debug(f"Nonce for {account}: {nonce}")
        return nonce

    def _get_and_increment(self, account: HexAddress) -> Nonce:
        raise NotImplementedError()

    def _set(self, account: HexAddress, nonce: Nonce):
        raise NotImplementedError()
