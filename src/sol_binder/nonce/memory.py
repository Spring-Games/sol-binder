from contextlib import contextmanager
from typing import *

from eth_typing import HexAddress
from web3 import Web3
from web3.types import Nonce

from .base import AbstractNonceManager


class MemoryNonceManager(AbstractNonceManager):
    @classmethod
    def name(cls):
        return "local"

    @classmethod
    def create(cls, w3: Web3, project_root: str,
               args: Union[str, dict, list, None]) -> "AbstractNonceManager":
        return cls(w3)

    def __init__(self, w3: Web3):
        super().__init__(w3)
        self._locked = False
        self._nonces: Dict[HexAddress: Nonce] = {}

    def _tracked_accounts(self) -> List[HexAddress]:
        return list(self._nonces.keys())

    def _lock(self):
        self._locked = True

    def _unlock(self):
        self._locked = False

    def _is_locked(self):
        return bool(self._locked)

    def _get(self, account: HexAddress):
        if not self._nonces.get(account):
            self._sync_from_chain(account)
        return self._nonces[account]

    def _set(self, account: HexAddress, nonce: Nonce):
        self._nonces[account] = nonce
