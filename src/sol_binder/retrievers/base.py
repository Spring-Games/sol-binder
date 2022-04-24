from typing import Union

import abc


class BaseRetriever(abc.ABC):
    def can_supply(self, import_path: str) -> bool:
        raise NotImplementedError()

    def get_source(self, import_path: str) -> str:
        raise NotImplementedError()

    def get_dep_context(self, import_path: str) -> Union[str, None]:
        """

        :param import_path: 
        :return: the prefix for retrieving sub-imports
        """
        raise NotImplementedError()

    def get_local_path(self, import_path: str) -> str:
        raise NotImplementedError()
