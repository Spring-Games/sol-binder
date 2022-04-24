import os
import re
import requests

from .base import BaseRetriever


class GitHubRetriever(BaseRetriever):
    GITHUB_NON_RAW_URL_RE = r"https?://github.com/([^/]+)/([^/]+)/blob/(.+)"
    GITHUB_RAW_CONTENT_URL_BASE = r"https://raw.githubusercontent.com"

    def can_supply(self, import_path: str) -> bool:
        return self.__is_non_raw_url(import_path)

    def get_source(self, import_path: str) -> str:
        raw_url = self.__get_raw_url(import_path)
        return requests.get(raw_url).content.decode()

    def get_local_path(self, import_path: str) -> str:
        m = re.search(self.GITHUB_NON_RAW_URL_RE, import_path)
        account_name, repo_name, relative_path = m.groups()
        return relative_path

    def get_dep_context(self, import_path: str) -> str:
        return os.path.dirname(import_path)

    @classmethod
    def __is_non_raw_url(cls, url) -> bool:
        return re.search(cls.GITHUB_NON_RAW_URL_RE, url) is not None

    @classmethod
    def __get_raw_url(cls, url) -> str:
        m = re.search(cls.GITHUB_NON_RAW_URL_RE, url)
        account_name, repo_name, relative_path = m.groups()
        return f"{cls.GITHUB_RAW_CONTENT_URL_BASE}/{account_name}/{repo_name}/{relative_path}"
