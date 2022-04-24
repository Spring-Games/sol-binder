class W3ConnectionError(Exception):
    pass


class ContractDeploymentError(Exception):
    pass


class ContractAlreadyDeployedError(ContractDeploymentError):
    pass
