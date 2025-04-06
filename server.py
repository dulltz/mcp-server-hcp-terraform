import os
from typing import Any, Dict, List, Optional

import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("HCP Terraform")

token = os.environ.get("HCP_TERRAFORM_TOKEN")
if not token:
    raise ValueError("HCP_TERRAFORM_TOKEN environment variable is not set.")

org_name = os.environ.get("HCP_TERRAFORM_ORG")
if not org_name:
    raise ValueError("HCP_TERRAFORM_ORG environment variable is not set.")

base_url = os.environ.get("HCP_TERRAFORM_BASE_URL", "https://app.terraform.io")


@mcp.tool()
def hcp_terraform_search_private_modules(
    query: str, provider: Optional[str] = None, limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Search for modules in the HCP Terraform Private Registry
    """
    api_path = f"/api/v2/organizations/{org_name}/registry-modules"
    params = {"page[size]": limit}
    if query:
        params["q"] = query
    if provider:
        params["filter[provider]"] = provider
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/vnd.api+json",
    }

    try:
        with httpx.Client() as client:
            response = client.get(
                f"{base_url}{api_path}", headers=headers, params=params, timeout=10
            )
            response.raise_for_status()
            data = response.json()

            modules = []
            for item in data.get("data", []):
                attributes = item.get("attributes", {})
                modules.append(
                    {
                        "id": item.get("id"),
                        "name": attributes.get("name"),
                        "namespace": attributes.get("namespace", org_name),
                        "provider": attributes.get("provider"),
                        "registry_name": attributes.get("registry-name"),
                        "status": attributes.get("status"),
                        "versions": [
                            v.get("version")
                            for v in attributes.get("version-statuses", [])
                        ],
                        "created_at": attributes.get("created-at"),
                        "updated_at": attributes.get("updated-at"),
                        "self_link": item.get("links", {}).get("self"),
                    }
                )

            return modules
    except httpx.HTTPError as e:
        return [{"error": f"An error occurred during API call: {str(e)}"}]


@mcp.tool()
def hcp_terraform_get_module(
    module_name: str,
    provider: str,
    registry_name: str = "private",
    namespace: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Get a specific module from the HCP Terraform Registry

    Args:
        module_name: The name of the module
        provider: The provider (e.g., aws, gcp, azure)
        registry_name: The registry name (private or public)
        namespace: The namespace of the module (defaults to organization name)

    Returns:
        Module details
    """
    if namespace is None:
        namespace = org_name

    api_path = f"/api/v2/organizations/{org_name}/registry-modules/{registry_name}/{namespace}/{module_name}/{provider}"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/vnd.api+json",
    }

    try:
        with httpx.Client() as client:
            response = client.get(f"{base_url}{api_path}", headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()

            module_data = data.get("data", {})
            attributes = module_data.get("attributes", {})

            return {
                "id": module_data.get("id"),
                "name": attributes.get("name"),
                "provider": attributes.get("provider"),
                "namespace": attributes.get("namespace", org_name),
                "registry_name": attributes.get("registry-name"),
                "status": attributes.get("status"),
                "versions": [
                    v.get("version") for v in attributes.get("version-statuses", [])
                ],
                "created_at": attributes.get("created-at"),
                "updated_at": attributes.get("updated-at"),
                "vcs_repo": attributes.get("vcs-repo"),
                "permissions": attributes.get("permissions"),
                "self_link": module_data.get("links", {}).get("self"),
            }
    except httpx.HTTPError as e:
        return {"error": f"An error occurred during API call: {str(e)}"}
