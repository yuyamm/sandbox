# 参考: https://openapi.apidog.io/export-data-in-openapiswagger-format-7312737e0

import json

import requests

access_token = ""
project_id = ""
url = f"https://api.apidog.com/v1/projects/{project_id}/export-openapi?locale=en-US"
destination_path = "scripts/schema/openapi.json"

payload = json.dumps(
    {
        "scope": {"type": "ALL", "excludedByTags": []},
        "options": {
            "includeApidogExtensionProperties": False,
            "addFoldersToTags": False,
        },
        "oasVersion": "3.1",
        "exportFormat": "JSON",
    }
)
headers = {
    "X-Apidog-Api-Version": "2024-03-28",
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json",
}

response = requests.request("POST", url, headers=headers, data=payload)

data = json.loads(response.text)

with open(destination_path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
