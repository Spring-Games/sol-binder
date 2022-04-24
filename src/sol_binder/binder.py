from typing import TYPE_CHECKING, List, Union
from typing import Optional
import os
import re

from .retrievers.localfile import LocalFileRetriever
from .utils import normalize_url_path
from .project.config import ProjectConfig
from .solbinder_logging import get_solbinder_logger

if TYPE_CHECKING:
    from .retrievers.base import BaseRetriever


class SolBinder(object):
    def __init__(self, import_path: Optional[str] = None, verbose: bool = False):
        self.import_path = import_path or self.__get_default_import_path()
        self.retrievers: List["BaseRetriever"] = list()
        self.__register_default_retrievers()
        self.__verbose = verbose

    def bind(self, source: str):
        imp_translations = self.__download_imports(source, self.import_path)
        source = self.__preprocess_source(source, imp_translations)
        return source

    def register_retriever(self, retriever: "BaseRetriever"):
        self.retrievers.append(retriever)

    def __register_default_retrievers(self):
        from .retrievers.github import GitHubRetriever
        from .retrievers.openzeppelin import OpenZeppelinRetriever
        self.register_retriever(OpenZeppelinRetriever())
        self.register_retriever(GitHubRetriever())

    def __detect_retriever(self, import_path: str) -> Union[None, "BaseRetriever"]:
        for retriever in self.retrievers:
            if retriever.can_supply(import_path):
                return retriever
        return LocalFileRetriever(self.import_path)

    @staticmethod
    def __get_default_import_path():
        return os.path.dirname(ProjectConfig.find_project_config_path()) + "/sol_binder_cache"

    @staticmethod
    def __iter_import_urls(source):
        for l in source.splitlines():
            l = l.strip()
            if l.startswith('//'):
                continue
            match = re.search(r'import "([^"]+)"\S*;', l)
            if match is None:
                continue
            sol_import_path = match.group(1)
            yield sol_import_path

    def __download_single_import(self, url):
        url = normalize_url_path(url)
        retriever = self.__detect_retriever(url)
        if retriever is None:
            raise NotImplementedError(f"No suitable retriever for {url}")
        if self.__verbose:
            get_solbinder_logger().info(f"Retrieving '{url}'")
        source = retriever.get_source(url)
        local_path = os.path.normpath(os.path.join(self.import_path, retriever.get_local_path(url)))
        return source, local_path

    def __download_imports(self, source, storage_dir, context_url=None):
        translations = dict()
        storage_dir = os.path.abspath(storage_dir)
        for imp_path in self.__iter_import_urls(source):
            retriever = self.__detect_retriever(imp_path)
            if retriever is None:
                raise NotImplementedError(f"No suitable retriever for {imp_path}")
            sub_context_url = retriever.get_dep_context(imp_path) or context_url
            if context_url is not None:
                absolute_imp_path = normalize_url_path(os.path.join(context_url, imp_path))
            else:
                absolute_imp_path = imp_path
            retriever = self.__detect_retriever(absolute_imp_path)
            local_path = os.path.normpath(os.path.join(self.import_path, retriever.get_local_path(absolute_imp_path)))
            cached = False
            if not os.path.exists(local_path):
                if self.__verbose or True:
                    get_solbinder_logger().info(f"Downloading {local_path}")
                imp_source, local_path = self.__download_single_import(absolute_imp_path)
            else:
                cached = True
                if self.__verbose or True:
                    get_solbinder_logger().info(f"Cached {local_path}")
                imp_source = open(local_path).read()
            translations[imp_path] = local_path
            translations.update(self.__download_imports(imp_source, storage_dir, sub_context_url))
            if not cached:
                dir_name = os.path.dirname(local_path)
                if not os.path.isdir(dir_name):
                    os.makedirs(dir_name)

                if self.__verbose or True:
                    get_solbinder_logger().info(f"Writing {local_path}")
                with open(local_path, "w") as f:
                    # self.preprocess_source(imp_source, translations)
                    f.write(imp_source)
        return translations

    @staticmethod
    def __preprocess_source(source: str, import_translations: dict):
        modified_source = ""
        for l in source.splitlines():
            l = l.strip()
            if l.startswith('//'):
                continue
            match = re.search(r'import "([^"]+)"\S*;', l)
            if match:
                remote_path = match.group(1)
                local_path = import_translations[remote_path]
                new_line = l.replace(remote_path, local_path)
            else:
                new_line = l
            modified_source += new_line + "\n"
        return modified_source
