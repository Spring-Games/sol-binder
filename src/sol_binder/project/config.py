import json
import logging
import os
from pathlib import Path
from typing import *
from dataclasses import dataclass, field

from dataclasses import asdict

import click
import yaml
from eth_typing import HexAddress
from web3 import Web3
from web3.contract import Contract

from ..nonce.base import AbstractNonceManager
from ..project.errors import NoContractsFoundError, ProjectConfigLocationError, ProjectConfigLoadError, \
    UnknownNonceManagerType, ProjectConfigAlreadyExistsError
from ..tx_logging import BaseTransactionLogger, FileTransactionLogger, MongoTransactionLog
from ..utils import basename_without_ext

DEFAULT_CONFIG_FILENAME = "solbinder.yaml"
DEFAULT_NONCE_MANAGER_TYPE = "naive"


def _default_networks():
    return {
        "dev": {
            "host": "localhost",
            "port": 8545,
            "network_id": 1337,
        }
    }


if TYPE_CHECKING:
    class NetworkInfo(TypedDict):
        url: str
        network_id: int
        account_address: str


class UnknownDeploymentPlanError(Exception):
    pass


class ProjectContractDeployment(NamedTuple):
    name: str
    filepath: str
    args: List[Any]


@dataclass
class ContractDeploymentData:
    """This is the data we save to file after deploying a contract"""
    abi: List[Dict]
    contract_address: str
    tx_hash: str
    account: HexAddress
    chain_id: int
    w3_url: str
    source_hash: str  # Hashed source-code of the contract
    deployment_cost_wei: int  # How much we paid when we deployed this contract

    def _get_raw_instance(self, w3: "Web3" = None) -> "Contract":
        """TODO: This is for testing only, we should move this to some test_util class later on"""
        if not w3:
            w3 = ProjectConfig.load_project_config().get_w3()
        hashed_address = Web3.toChecksumAddress(self.contract_address)
        return w3.eth.contract(address=hashed_address, abi=self.abi)

    def save(self, filepath):
        with open(filepath, 'w') as f:
            f.write(json.dumps(asdict(self)))


@dataclass
class ProjectConfig(object):
    project_root: str = "."
    networks: Dict[str, Dict[str, Union[str, int]]] = field(default_factory=_default_networks)
    contracts_dir: str = "contracts"
    deploy_cache_dir: str = ".solbinder/deployments"
    transaction_cache_dir: str = ".solbinder/transactions"
    imports_cache_dir: str = ".solbinder/import_cache"
    default_network: str = "dev"
    solc_version: str = "0.8.6"
    tx_logger: Dict = None
    deployments: Optional[Dict[str, Union[str, List[Any], Dict[str, List[Any]]]]] = None
    nonce: Optional[Dict[str, Union[List, Dict, str]]] = None
    __nonce_manager_types = dict()
    __nonce_manager_by_network = dict()
    __cached_w3_instances = dict()

    def __post_init__(self, *args, **kwargs):
        self.__ensure_abs_paths(self.project_root)
        self.__register_default_nonce_managers()

    @classmethod
    def register_nonce_manager_type(cls, nonce_manager_class: Type[AbstractNonceManager]):
        cls.__nonce_manager_types[nonce_manager_class.name()] = nonce_manager_class

    @classmethod
    def __register_default_nonce_managers(cls):
        from ..nonce.file import FileNonceManager
        from ..nonce.memory import MemoryNonceManager
        from ..nonce.naive import NaiveNonceManager
        for nonce_mgr_cls in [FileNonceManager, MemoryNonceManager, NaiveNonceManager]:
            cls.register_nonce_manager_type(nonce_mgr_cls)
        try:
            from ..nonce.redisdb import RedisNonceManager
            cls.register_nonce_manager_type(RedisNonceManager)
        except ImportError:
            logging.info("redis is not installed. redis-based nonce management will not be available")

    def __ensure_abs_paths(self, project_root: Union[Path, str]):
        project_root = str(project_root)
        for attr_name in ["contracts_dir", "deploy_cache_dir", "imports_cache_dir"]:
            current_value = getattr(self, attr_name)
            if not os.path.isabs(current_value):
                setattr(self, attr_name, os.path.join(project_root, current_value))

    def get_w3_url(self, network: Optional[str] = None) -> str:
        if network is None:
            network = self.default_network
        return self.networks[network]['url']

    def get_w3(self, network: Optional[str] = None) -> Web3:
        if network is None:
            network = self.default_network
        if network not in self.__cached_w3_instances:
            web3url = self.get_w3_url(network)
            self.__cached_w3_instances[network] = Web3(Web3.HTTPProvider(web3url))
        return self.__cached_w3_instances[network]

    def get_nonce_manager_args(self) -> Union[list, dict]:
        return self.nonce['args'] if self.nonce else None

    def __get_network_id(self, network: str) -> int:
        return self.networks[network]['network_id']

    def get_account(self, network: str) -> str:
        net_info = self.get_network_info(network)
        account = net_info.get("account")
        if account is None:
            # No account specified use default
            account = self.get_w3(network).eth.accounts[0]
        return account

    def get_nonce_config(self, network: Optional[str] = None):
        net_info = self.get_network_info(network)
        if 'nonce' in net_info:
            return net_info['nonce']
        else:
            return self.nonce

    def create_tx_logger(self, contract: str) -> Optional[BaseTransactionLogger]:
        if self.tx_logger:
            type_ = self.tx_logger.get("type")
            if type_ == 'file':
                path = os.path.normpath(os.path.join(self.transaction_cache_dir, f"{contract}_transactions.yaml"))
                return FileTransactionLogger(Path(path))
            elif type_ == "mongo":
                return MongoTransactionLog(self.tx_logger.get("args"), contract)
            else:
                raise RuntimeError(f"Unrecognized transaction logger: {type_}")

    def get_nonce_manager(self, network: Optional[str] = None) -> AbstractNonceManager:
        nonce_config = self.get_nonce_config(network)
        return self.__get_nonce_manager(network, nonce_config)

    def __get_nonce_manager(self, network: str, nonce_config: dict) -> AbstractNonceManager:
        if network in self.__nonce_manager_by_network:
            return self.__nonce_manager_by_network[network]
        nonce_manager_type: str = nonce_config['type'] if nonce_config else DEFAULT_NONCE_MANAGER_TYPE
        nonce_manager_args: Union[list, dict] = nonce_config['args'] if nonce_config else None
        if len(self.__nonce_manager_types) == 0:
            self.__register_default_nonce_managers()
        if nonce_manager_type not in self.__nonce_manager_types:
            raise UnknownNonceManagerType(nonce_manager_type)
        w3 = self.get_w3(network)
        nonce_manager_cls: AbstractNonceManager = self.__nonce_manager_types[nonce_manager_type]
        nonce_manager = nonce_manager_cls.create(w3, self.project_root, nonce_manager_args)
        self.__nonce_manager_by_network[network] = nonce_manager
        return nonce_manager

    def get_contract_filepath_by_name(self) -> Dict[str, str]:
        return dict(
            [(basename_without_ext(fp), fp) for fp in self.iterate_contract_file_paths()]
        )

    def iterate_contract_file_paths(self) -> Iterator[str]:
        contracts = 0
        for filename in os.listdir(self.contracts_dir):
            if filename.lower().endswith(".sol"):
                yield os.path.normpath(os.path.join(self.contracts_dir, filename))
                contracts += 1
        if contracts == 0:
            raise NoContractsFoundError(f"No contracts found in {self.contracts_dir}")

    def iterate_contract_names(self) -> Iterator[str]:
        return [basename_without_ext(f) for f in self.iterate_contract_file_paths()]

    def get_deployment_filepath(self, contract_name: str) -> str:
        return os.path.normpath(os.path.join(self.deploy_cache_dir, f"{contract_name}.json"))

    def get_deployment_data(self, contract_name: str) -> ContractDeploymentData:
        with open(self.get_deployment_filepath(contract_name)) as fh:
            return ContractDeploymentData(**json.load(fh))

    def get_network_info(self, network_name: Optional[str] = None) -> "NetworkInfo":
        if network_name is None:
            network_name = self.default_network
        return self.networks[network_name]

    def get_deployment_plan(self, contract_name: str) -> ProjectContractDeployment:
        all_deployment_plans_by_name = {
            d.name: d for d in self.iter_deployment_plans()
        }
        try:
            return all_deployment_plans_by_name[contract_name]
        except KeyError:
            raise UnknownDeploymentPlanError(f"Don't know how to deploy {contract_name}")

    def iter_deployment_plans(self) -> Iterator[ProjectContractDeployment]:
        if not self.deployments:
            for name, filepath in self.get_contract_filepath_by_name():
                yield ProjectContractDeployment(filepath, name, [])
            return
        instances: List[ProjectContractDeployment] = []
        for filename, deployment_plan in self.deployments.items():
            full_path = os.path.join(self.contracts_dir, filename)
            if isinstance(deployment_plan, str):
                # Just a rename
                instances.append(ProjectContractDeployment(deployment_plan, full_path, []))
            elif isinstance(deployment_plan, list):
                # Its just the args
                instances.append(ProjectContractDeployment(filename, full_path, deployment_plan))
            elif isinstance(deployment_plan, dict):
                logging.info(deployment_plan)
                # Named instances
                for instance_name, instance_args in deployment_plan.items():
                    instances.append(ProjectContractDeployment(instance_name, full_path, instance_args))
        instance_names: set = set()
        for instance in instances:
            if instance.name in instance_names:
                raise ProjectConfigLoadError(f"Duplicate contract name: {instance.name}")
            instance_names.add(instance.name)
            yield instance

    @staticmethod
    def find_project_config_path(start_path: Union[str, Path] = None) -> Path:
        if start_path is None:
            start_path = os.getcwd()
        curr_path = Path(os.path.abspath(start_path))
        if curr_path.is_file():
            # If this is a file and not a folder, assume it is the config file
            return curr_path
        while True:
            # Test current directory
            if (curr_path / DEFAULT_CONFIG_FILENAME).is_file():
                return curr_path / DEFAULT_CONFIG_FILENAME
            if len(curr_path.parts) == 1:
                raise ProjectConfigLocationError(f"Could not find project config file in {start_path} or its parents")
            # Go up one level in the folder hierarchy and search there
            curr_path = curr_path.parents[0]

    @classmethod
    def load_project_config(cls, *args, **kwargs) -> "ProjectConfig":
        """Deprecated backward-compat method"""
        return cls.load(*args, **kwargs)

    @classmethod
    def load(cls, start_path: Union[str, Path, None] = None) -> "ProjectConfig":
        config_path = cls.find_project_config_path(start_path)
        project_dir = config_path.parents[0]
        with open(config_path) as config_fh:
            loaded_data = yaml.safe_load(config_fh)
            if loaded_data is None:
                config_dict = dict()
            else:
                config_dict = dict(loaded_data)
        try:
            config_dict['project_root'] = project_dir
            config = cls(**config_dict)
        except TypeError as e:
            raise ProjectConfigLoadError(f"Configuration load failed from {config_path}: {e}")
        return config

    def create(self, path: Union[str, Path, None]):
        if path is None:
            path = os.getcwd()
        full_file_path = os.path.abspath(os.path.normpath(os.path.join(path, DEFAULT_CONFIG_FILENAME)))
        click.secho(f"Creating project in {full_file_path}", fg="green")
        if os.path.exists(full_file_path):
            raise ProjectConfigAlreadyExistsError(full_file_path)
        data_dict = asdict(self)
        with open(full_file_path, "w") as fh:
            yaml.safe_dump(data_dict, fh)
