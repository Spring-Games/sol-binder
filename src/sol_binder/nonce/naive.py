from collections import defaultdict
from contextlib import contextmanager
from typing import *

from eth_typing import HexAddress
from web3 import Web3
from web3.types import Nonce

from .base import AbstractNonceManager


class NaiveNonceManager(AbstractNonceManager):
    """Nonce manager that always returns the blockchain transaction count, usually good only for testing environments
    with no block-time defined (any transaction is an immediate block)"""
    __nonces: Dict[HexAddress, Nonce]

    def __init__(self, w3: Web3):
        self.__nonces: Dict[HexAddress, Nonce] = defaultdict(lambda: -1)
        super().__init__(w3)

    @classmethod
    def name(cls):
        return "naive"

    def _lock(self):
        pass

    def _unlock(self):
        pass

    def _is_locked(self):
        return False

    def _get(self, account: HexAddress):
        self._sync_from_chain(account)
        return self.__nonces[account]

    @classmethod
    def create(cls, w3: Web3, project_root: str,
               args: Any) -> "AbstractNonceManager":
        return cls(w3)

    def _set(self, account: HexAddress, nonce: Nonce):
        self.__nonces[account] = nonce

    def _tracked_accounts(self) -> List[HexAddress]:
        return list(self.__nonces.keys())
