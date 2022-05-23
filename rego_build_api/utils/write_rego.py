from rego_build_api.server.models import RequestObject
from .build_rego_file import build_rego
from rego_build_api.server.github import initialize_repo, git_push
from ..config.config import settings

initiate_rule = "package httpapi.authz\nimport input\ndefault allow = false\n\n\n\n"


def write_to_file(rule: RequestObject) -> dict:
    """
    Write the rego file to the local git repository
    :param rule: rules
    :return: response dict to show the status of the request
    """

    # Initialize repository
    initialization_response = initialize_repo(settings.GITHUB_URL, settings.GITHUB_EMAIL, settings.GITHUB_USERNAME)
    repo_path = initialization_response["repo_path"]

    # Create rego file.
    with open(f"{repo_path}/auth.rego", "w") as file:
        result = initiate_rule + build_rego(rule.rules)

        file.write(result)

    # Push to GitHub
    git_push(repo_path)

    return {"status": "success"}