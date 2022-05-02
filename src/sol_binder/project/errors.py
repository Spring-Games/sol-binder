class ProjectError(Exception):
    pass


class ProjectConfigAlreadyExistsError(ProjectError):
    pass


class ProjectConfigError(ProjectError):
    pass


class ProjectConfigLocationError(ProjectConfigError):
    pass


class ProjectConfigLoadError(ProjectConfigError):
    pass


class NoContractsFoundError(ProjectConfigError):
    pass


class UnknownNonceManagerType(ProjectConfigError):
    pass
