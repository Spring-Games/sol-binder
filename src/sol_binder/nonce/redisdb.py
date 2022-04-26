from contextlib import contextmanager
from typing import *

from eth_typing import HexAddress
from redis.client import Redis
from web3 import Web3
from web3.types import Nonce

from .base import AbstractNonceManager


class RedisNonceManager(AbstractNonceManager):
    __key_base: str = "nonce_mgr:nonce_of:"
    __lock_key = "nonce_mgr:lock"

    @classmethod
    def name(cls):
        return "redis"

    @classmethod
    def create(cls, w3: Web3, project_root: str,
               args: str) -> "AbstractNonceManager":
        redis_uri = args
        redis = Redis.from_url(redis_uri)
        return cls(redis, w3, )

    def _account_key(self, account: HexAddress) -> str:
        return f"{self.__key_base}{account}"

    def __init__(self, redis: "Redis", w3: Web3):
        super().__init__(w3)
        self.__redis: Redis = redis

    @contextmanager
    def _lock(self):
        if self.__redis.get(self.__lock_key):
            raise RuntimeError
        self.__redis.set(self.__lock_key, 1)
        try:
            yield
        finally:
            self.__redis.delete(self.__lock_key)

    def _get(self, account: HexAddress):
        cached: bool = len(self.__redis.keys(self._account_key(account))) >= 1
        if not cached:
            self._sync_from_chain(account)
        return Nonce(int(self.__redis.get(self._account_key(account))))

    def _get_and_increment(self, account: HexAddress) -> Nonce:
        cached: bool = len(self.__redis.keys(self._account_key(account))) >= 1
        if not cached:
            self._sync_from_chain(account)
        return Nonce(self.__redis.incr(self._account_key(account), 1) - 1)

    def _set(self, account: HexAddress, nonce: Nonce):
        self.__redis.set(self._account_key(account), nonce)

    def _tracked_accounts(self) -> List[HexAddress]:
        keys = self.__redis.keys(f"{self.__key_base}*")
        return [cast(HexAddress, k.decode().split(':')[-1]) for k in keys]
