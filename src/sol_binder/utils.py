from dataclasses import dataclass, Field, field
from typing import *

import os
import json
import yaml
import urllib

from pathlib import Path

from solcx import compile_source


def basename_without_ext(filepath: str) -> str:
    return os.path.splitext(os.path.basename(filepath))[0]


def normalize_url_path(url):
    parsed = urllib.parse.urlparse(url)
    path = os.path.normpath(parsed.path)
    parsed._replace(path=path)
    return parsed.geturl()


def extract_abi_from_compiled_contract(compiled_contract: dict):
    root_key = list(compiled_contract.keys())[0]
    return compiled_contract[root_key]['abi']


def compile_contract_and_save_abi(*args, **kwargs):
    abi_path = kwargs.pop("abi_path")
    compiled = compile_source(*args, **kwargs)
    abi = extract_abi_from_compiled_contract(compiled)
    with open(abi_path, "w") as abi_fh:
        json.dump(abi, abi_fh)
    return compiled

