import urllib.request
import json
import sys

token = "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"
repo_name = "financial-edge-daily-reel-agent"

url = "https://api.github.com/user/repos"
data = {
    "name": repo_name,
    "private": True,
    "description": "24/7 Automated video pipeline for Financial Edge Daily Facebook Reels."
}

req = urllib.request.Request(
    url,
    data=json.dumps(data).encode("utf-8"),
    headers={
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json",
        "User-Agent": "antigravity-agent"
    },
    method="POST"
)

try:
    with urllib.request.urlopen(req) as response:
        res = json.loads(response.read().decode())
        print(f"SUCCESS: Created repository {res['full_name']}")
        print(f"CLONE_URL: {res['clone_url']}")
except Exception as e:
    print(f"FAILED: {e}", file=sys.stderr)
    sys.exit(1)
