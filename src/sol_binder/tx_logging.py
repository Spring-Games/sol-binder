from json import JSONDecodeError
from typing import *
import json
from abc import ABC
from copy import deepcopy
from pathlib import Path

from pymongo import MongoClient

_Preprocessor = Callable[[str, str, List], Dict]


class TransactionLoggerPreprocessors:
    """Holds methods that can inject extra data into the DB per transaction."""
    __singleton: ClassVar["TransactionLoggerPreprocessors"] = None
    __preprocessors: List[_Preprocessor]
    __can_spawn = False

    def __init__(self):
        if not self.__can_spawn:
            raise RuntimeError("Do not instantiate directly, use get_singleton() instead.")
        self.__preprocessors = []

    @classmethod
    def get_singleton(cls) -> "TransactionLoggerPreprocessors":
        if not cls.__singleton:
            cls.__can_spawn = True
            cls.__singleton = cls()
            cls.__can_spawn = False
        return cls.__singleton

    def add_preprocessor(self, preprocessor: _Preprocessor):
        self.__preprocessors.append(preprocessor)

    def run_preprocessors(self, tx_hash: str, function: str, params: List) -> Dict:
        result = {}
        for p in self.__preprocessors:
            result.update(p(tx_hash, function, params))
        return result

    def reset_preprocessors(self):
        self.__preprocessors = []


class BaseTransactionLogger(ABC):
    def log_transaction(self, tx_hash: str, function: str, params: List):
        args = locals()
        args.pop('self')
        extra = TransactionLoggerPreprocessors.get_singleton().run_preprocessors(tx_hash, function, params)
        args.update(extra)
        self._log_transaction(args)

    def _log_transaction(self, tx: Dict) -> Dict:
        raise NotImplementedError

    def get_transaction(self, tx_hash):
        raise NotImplementedError

    def get_all(self):
        raise NotImplementedError


class InMemoryTransactionLogger(BaseTransactionLogger):
    def __init__(self):
        self._transactions = {}

    def _log_transaction(self, tx: Dict):
        self._transactions[tx['tx_hash']] = tx

    def get_transaction(self, tx_hash):
        return self._transactions[tx_hash]

    def get_all(self):
        return deepcopy(list(self._transactions.values()))


class FileTransactionLogger(BaseTransactionLogger):
    def __init__(self, filename: Path):
        self._filename = filename

    def _log_transaction(self, tx: Dict):
        with open(self._filename, 'r') as f:
            try:
                trans = json.load(f)
            except JSONDecodeError:
                trans = {}

        trans[tx['tx_hash']] = tx
        with open(self._filename, 'w') as f:
            json.dump(trans, f)

    def get_transaction(self, tx_hash):
        with open(self._filename, 'r') as f:
            trans = json.load(f)
        return trans[tx_hash]

    def get_all(self):
        with open(self._filename, 'r') as f:
            trans = json.load(f)
        return list(trans.values())


class MongoTransactionLog(BaseTransactionLogger):
    def __init__(self, mongo_uri: str, contract_name: str) -> None:
        db_name = mongo_uri.split('/')[-1]
        host = mongo_uri[0:-len(db_name) - 1]
        self._collection = MongoClient(host)[db_name][f"{contract_name}_transactions"]

    def _log_transaction(self, tx: Dict):
        self._collection.insert_one(tx)

    def get_transaction(self, tx_hash):
        return self._collection.find_one({tx_hash: tx_hash})

    def get_all(self):
        return self._collection.find()
