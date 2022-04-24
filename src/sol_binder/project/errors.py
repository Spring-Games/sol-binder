class ProjectConfigError(Exception):
    pass


class ProjectConfigLocationError(ProjectConfigError):
    pass


class ProjectConfigLoadError(ProjectConfigError):
    pass


class NoContractsFoundError(ProjectConfigError):
    pass


class UnknownNonceManagerType(ProjectConfigError):
    pass
