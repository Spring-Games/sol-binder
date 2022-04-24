from typing import Union

import os

from .base import BaseRetriever


class LocalFileRetriever(BaseRetriever):
    def __init__(self, parent_dir: str):
        self.parent_dir = parent_dir

    def can_supply(self, import_path: str) -> bool:
        return True

    def get_source(self, import_path: str) -> str:
        file_path = os.path.join(self.parent_dir, self.get_local_path(import_path))
        with open(file_path) as fh:
            return fh.read()

    def get_dep_context(self, import_path: str) -> Union[str, None]:
        return None

    def get_local_path(self, import_path: str) -> str:
        return import_path
