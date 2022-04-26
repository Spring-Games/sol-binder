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

    @contextmanager
    def _lock(self):
        if self._locked:
            raise RuntimeError
        self._locked = True
        try:
            yield
        finally:
            self._locked = False

    def _get(self, account: HexAddress):
        if not self._nonces.get(account):
            self._sync_from_chain(account)
        return self._nonces[account]

    def _get_and_increment(self, account: HexAddress) -> Nonce:
        if not self._nonces.get(account):
            self._sync_from_chain(account)
        nonce = self._nonces[account]
        self._nonces[account] = nonce + 1
        return nonce

    def _set(self, account: HexAddress, nonce: Nonce):
        self._nonces[account] = nonce
