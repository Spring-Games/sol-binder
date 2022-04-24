from typing import *
import os
import json

import click

from semantic_version import Version
from solcx import compile_source

from .utils import get_sol_cache_path
from ..binder import SolBinder
from ..project.config import ProjectConfig
from ..utils import extract_abi_from_compiled_contract

__all__ = ['compile_sol']


@click.command()
@click.option("-s", "--solc-version", default=None, help="Sol compiler version")
@click.option("-a", "--abi", "abi_path", default=None, help="Save ABI file")
@click.argument("contract_file")
def compile_sol(solc_version: Optional[str], contract_file, abi_path):
    if not solc_version:
        solc_version = ProjectConfig.load_project_config().solc_version
    project_data_dir = get_sol_cache_path()
    if not os.path.isdir(project_data_dir):
        os.makedirs(project_data_dir)
    binder = SolBinder(import_path=os.path.join(project_data_dir, "import_cache"))
    with open(contract_file) as contract_handle:
        source = contract_handle.read()
    processed_source = binder.bind(source)
    compiled = compile_source(processed_source,
                              solc_version=Version(solc_version),
                              allow_paths=binder.import_path)
    if abi_path:
        abi = extract_abi_from_compiled_contract(compiled)
        with open(abi_path, "w") as abi_fh:
            json.dump(abi, abi_fh)
    return compiled
