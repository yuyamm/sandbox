# 参考: https://openapi.apidog.io/import-openapiswagger-data-7312738e0

import json

import requests

access_token = ""
project_id = ""
url = f"https://api.apidog.com/v1/projects/{project_id}/import-openapi?locale=en-US"
load_path = "scripts/schema/openapi.json"

with open(load_path, encoding="utf-8") as f:
    data = json.load(f)

payload = json.dumps(
    {
        "input": data,
        "options": {
            "targetEndpointFolderId": 0,
            "targetSchemaFolderId": 0,
            "endpointOverwriteBehavior": "OVERWRITE_EXISTING",
            "schemaOverwriteBehavior": "OVERWRITE_EXISTING",
            "updateFolderOfChangedEndpoint": False,
            "prependBasePath": False,
        },
    }
)
headers = {
    "X-Apidog-Api-Version": "2024-03-28",
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json",
}

response = requests.request("POST", url, headers=headers, data=payload)

print(response.text)
