from typing import List
from pathlib import Path

import os
import json

from ..project.config import ProjectConfig


def get_sol_cache_path():
    return Path(os.path.dirname(ProjectConfig.find_project_config_path())) / ".solbinder"


def parse_argument(arg: str):
    try:
        return json.loads(arg)
    except ValueError:
        return arg


def parse_arguments(args: List[str]):
    return [parse_argument(arg) for arg in args]


def try_load_default_deployment_file(contract_address: str):
    deployment_cache_path = get_sol_cache_path() / "deployments"
    deployment_filename = f"{contract_address}.json"
    deployment_filepath = os.path.join(deployment_cache_path, deployment_filename)
    return load_deployment_file(deployment_filepath)


def load_deployment_file(filepath: str):
    with open(filepath) as deployment_fh:
        return json.load(deployment_fh)


def try_get_last_deployed_contract_address():
    deployment_cache_path = get_sol_cache_path() / "deployments"
    last_deployed_filepath = os.path.join(deployment_cache_path, "last_deployed.address")
    if not os.path.isfile(last_deployed_filepath):
        return None
    with open(last_deployed_filepath) as fh:
        return fh.read()
