from typing import Optional, Union, List
from pathlib import Path
from filelock import FileLock

import os

from eth_typing import HexAddress
from web3 import Web3
from web3.types import Nonce

from ..nonce.base import AbstractNonceManager


class FileNonceManager(AbstractNonceManager):
    def __init__(self, dir_path: str, w3: Web3):
        super().__init__(w3)
        self.__dir_path = dir_path
        self._lock = FileLock(self._lock_file_path())

    @classmethod
    def create(cls, w3: Web3, project_root: str,
               args: Union[str, dict, list, None]) -> "AbstractNonceManager":
        nonce_dir = os.path.join(project_root, ".nonce")
        if not os.path.exists(nonce_dir):
            os.makedirs(nonce_dir)
        return cls(nonce_dir, w3)

    @classmethod
    def name(cls):
        return "file"

    def _lock_file_path(self):
        return os.path.join(self.__dir_path, "nonce_manager_lock")

    def _lock_blocking(self):
        self._lock.acquire(timeout=self._LOCK_TIMEOUT_SECONDS)

    def _unlock(self):
        self._lock.release(True)

    def _get(self, account: HexAddress):
        nonce = self.__read_nonce_file(account)
        return nonce

    def _set(self, account: HexAddress, nonce: Nonce):
        self.__write_nonce_file(account, nonce)

    def __get_nonce_file_path(self, account: str):
        return os.path.join(self.__dir_path, f"{account}.nonce")

    def __write_nonce_file(self, account: str, nonce: int):
        filepath = self.__get_nonce_file_path(account)
        with open(filepath, "w") as fh:
            fh.write(str(nonce))

    def __read_nonce_file(self, account: str) -> Optional[int]:
        filepath = self.__get_nonce_file_path(account)
        if not os.path.exists(filepath):
            return None
        with open(filepath) as fh:
            return int(fh.read().strip())

    def _tracked_accounts(self) -> List[HexAddress]:
        accounts = []
        for file in Path(self.__dir_path).iterdir():
            accounts.append(file.name.split('.')[0])
        return accounts
