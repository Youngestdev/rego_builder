from fastapi import Depends, HTTPException, APIRouter
import requests as r

from app.config.config import settings
from app.database.policy_database import PolicyDatabase, get_db
from app.schemas.rules import RequestObject, UpdateRequestObject
from app.server.auth.authorize import TokenBearer
from app.utils.write_rego import WriteRego
from app.database.datasource_database import database

default_path = settings.BASE_PATH

router = APIRouter()


@router.get("/policies")
async def get_policies(
    database: PolicyDatabase = Depends(get_db), dependencies=Depends(TokenBearer())
) -> list:
    return database.get_policies(dependencies["login"])


@router.post("/policies/")
async def write_policy(
    rego_rule: RequestObject,
    database=Depends(get_db),
    dependencies=Depends(TokenBearer()),
) -> dict:
    rego_rule.owner = dependencies["login"]
    policy = rego_rule.dict()

    if database.exists(rego_rule.name, dependencies["login"]):
        raise HTTPException(status_code=409, detail="Policy already exists")

    policies = database.get_policies(dependencies["login"])
    policies.append(policy)

    # Write the policy to the database after successful push
    WriteRego(
        access_token=dependencies["token"], github_repo_url=rego_rule.github_repo_url
    ).write_to_file(policies)

    database.add_policy(policy, dependencies["login"])

    return {"status": 200, "message": "Policy created successfully"}


@router.get("/policies/{policy_id}")
async def retrieve_policy(
    policy_id: str, database=Depends(get_db), dependencies=Depends(TokenBearer())
) -> dict:
    stored_policy = database.get_policy(policy_id, dependencies["login"])
    if not stored_policy:
        raise HTTPException(status_code=404, detail="Policy does not exist")

    return stored_policy


@router.put("/policies/{policy_id}")
async def modify_policy(
    policy_id: str,
    rego_rule: UpdateRequestObject,
    database=Depends(get_db),
    dependencies=Depends(TokenBearer()),
) -> dict:
    if not database.exists(policy_id, dependencies["login"]):
        raise HTTPException(status_code=404, detail="Policy not found")

    # Clean out fields which weren't updated.
    rego_rule = {k: v for k, v in rego_rule.dict().items() if v is not None}

    # Update database
    database.update_policy(policy_id, rego_rule, dependencies["login"])

    # Retrieve updated policy
    updated_policy = database.get_policy(policy_id, dependencies["login"])

    policies = database.get_policies(dependencies["login"])
    policies.append(updated_policy)

    # Rewrite rego file and update GitHub
    WriteRego(dependencies["token"], rego_rule["github_repo_url"]).write_to_file(
        policies
    )

    return {"status": 200, "message": "Updated successfully"}


@router.delete("/policies/{policy_id}")
async def remove_policy(
    policy_id: str,
    github_repo_url: str,
    database=Depends(get_db),
    dependencies=Depends(TokenBearer()),
) -> dict:
    if not database.exists(policy_id, dependencies["login"]):
        raise HTTPException(status_code=404, detail="Policy not found")

    user = dependencies["login"]
    # Remove policy from database
    database.delete_policy(policy_id, user, github_repo_url)

    # Update the policy in the rego file
    policies = database.get_policies(owner=user)
    WriteRego(dependencies["token"], github_repo_url).write_to_file(policies)

    return {"status": 200, "message": "Policy deleted successfully."}


@router.get("/data")
async def get_data(dependencies=Depends(TokenBearer())) -> dict:
    return {"users": database.get_data()}


@router.get("/user/repos")
async def get_public_and_private_repo(
    dependencies=Depends(TokenBearer()),
) -> dict:

    url = f"https://api.github.com/search/repositories?q=user:{dependencies['login']}"
    repos = r.get(
        url=url,
        headers={"Authorization": f"token {dependencies['token']}"},
    ).json()

    return [
        {
            "name": repo["name"],
            "url": repo["url"],
            "html_url": repo["html_url"],
            "owner": repo["owner"]["login"],
        }
        for repo in repos["items"]
    ]
