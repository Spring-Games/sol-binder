from .github import GitHubRetriever


class OpenZeppelinRetriever(GitHubRetriever):
    BASE_URL = "https://github.com/OpenZeppelin/openzeppelin-contracts/blob/v4.0.0/"

    def can_supply(self, import_path: str) -> bool:
        return import_path.startswith("@openzeppelin/")

    def get_source(self, import_path: str) -> str:
        github_path = import_path.replace("@openzeppelin/", self.BASE_URL)
        return super().get_source(github_path)

    def get_dep_context(self, import_path: str) -> str:
        github_path = import_path.replace("@openzeppelin/", self.BASE_URL)
        return super().get_dep_context(github_path)
    
    def get_local_path(self, import_path: str) -> str:
        github_path = import_path.replace("@openzeppelin/", self.BASE_URL)
        return super().get_local_path(github_path)
