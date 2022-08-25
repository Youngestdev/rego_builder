from functools import lru_cache

import gitlab.exceptions
from gitlab import Gitlab


@lru_cache(maxsize=1)
class GitLabOperations:
    """GitLab operations, clone, commit, push and return user repository list"""

    def __init__(self, repo_id: int, access_token: str) -> None:
        """Initialize the class with repo_id and access_token"""

        self.access_token = access_token
        self.repo_id = repo_id

        self.gitlab = Gitlab(url="https://gitlab.com", oauth_token=self.access_token)

        # Initialize Gitlab instance
        self.gitlab.auth()

        # Retrieve the repository
        self.repo = self.gitlab.projects.get(self.repo_id)

    def prepare_data_and_commit(self, policy: str, action: str) -> bool:
        """
        prepare policy for commit and commit it

        params: policy: str - policy to be committed
                action: str - action to be performed on the policy

        return: True if commit was successful, False otherwise
        """
        data = {
            # Once this works, enable user set the branch or use default branch instead.
            "branch": "master",
            "commit_message": "Policy update from the OPA Manager",
            "actions": [
                {
                    "action": action,
                    "file_path": "auth.rego",
                    "content": policy,
                },
            ],
        }

        # Commit the changes
        changes = self.repo.commits.create(data)

        if not changes.id:
            return False
        return True

    def delete_policy(self) -> bool:
        data = {
            "branch": "master",
            "commit_message": "Policy deleted by the OPA Manager",
            "actions": [
                {
                    "action": "delete",
                    "file_path": "auth.rego",
                }
            ],
        }

        try:
            self.repo.commits.create(data)
        except gitlab.exceptions.GitlabCreateError:
            return False
        return True

    def repo_url_from_id(self) -> str:
        return self.repo.web_url

    def retrieve_repos(self):
        """Retrieve the list of repositories that belongs to the user"""

        unfiltered_repos = self.gitlab.projects(owned=True).list()
        repos = []

        for repo in unfiltered_repos:
            repos.append(
                RepoStructure(
                    name=repo["name"],
                    id=repo["id"],
                    url=repo["http_url_to_repo"],
                    owner=repo["owner"]["username"],
                )
            )

        return repos
