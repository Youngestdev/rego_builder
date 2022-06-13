import os

import git.exc
from git import Repo

from app.config.config import settings

access_token = settings.GITHUB_ACCESS_TOKEN

COMMIT_MESSAGE = "updates from from application"

default_path = settings.BASE_PATH


class GitHubOperations:
    def __init__(self, repo_url: str):
        self.repo_url = repo_url
        self.repo_name = repo_url.removesuffix(".git").split("/")[-1]
        self.local_repo_path = f"{default_path}/{self.repo_name}"
        self.repo_git_path = ""

    def initialize(self) -> None:
        """
        Check if the remote repository is valid and clone the remote repository.
        """
        # Check if the repo already exists
        if os.path.exists(self.local_repo_path):
            self.repo_git_path = f"{self.local_repo_path}/.git"
            return

        os.mkdir(self.local_repo_path)

        # Clone the repo to the server
        initialized_repo = Repo.clone_from(self.repo_url, self.local_repo_path)
        self.repo_git_path = initialized_repo.git_dir

    def push(self) -> None:
        """
        Push the changes to the remote repository
        """
        try:
            target_url = settings.GITHUB_URL
            repo = Repo(self.repo_git_path)
            repo.git.add(update=True)
            repo.index.add([f"{self.local_repo_path}/auth.rego"])
            repo.index.commit(COMMIT_MESSAGE)
            remotes = repo.remotes
            if not remotes:
                repo.create_remote("origin", target_url)
            if remotes[0].name != "origin":
                repo.create_remote("origin", target_url)
            origin = repo.remote(name="origin")
            origin.fetch()
            origin.push()
        except git.GitCommandError:
            raise git.GitCommandError
