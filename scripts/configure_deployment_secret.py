"""Store an expiring, namespace-scoped kubeconfig in GitHub Actions secrets."""

import base64
import json
import os
import subprocess
from datetime import datetime, timezone

REPOSITORY = "suhaniawasthi10/TeamDesk-"


def capture(command):
    return subprocess.check_output(command, text=True).strip()


def main():
    if not os.environ.get("KUBECONFIG"):
        raise SystemExit("Set KUBECONFIG to the project's .local/kubeconfig first.")
    if capture(["gh", "api", "user", "--jq", ".login"]) != "suhaniawasthi10":
        raise SystemExit("Sign GitHub CLI into the personal suhaniawasthi10 account.")

    kubectl = ["kubectl", "--context", "teamdesk"]
    operator = json.loads(
        capture([*kubectl, "config", "view", "--minify", "--raw", "-o", "json"])
    )
    cluster = operator["clusters"][0]["cluster"]
    # Use the normal DNS endpoint on GitHub, even if local DNS needed a workaround.
    server = cluster["server"]
    if cluster.get("tls-server-name"):
        server = "https://" + cluster["tls-server-name"]
    token = capture(
        [
            *kubectl,
            "create",
            "token",
            "github-deploy",
            "-n",
            "teamdesk",
            "--duration=8h",
        ]
    )
    payload = token.split(".")[1]
    claims = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
    config = {
        "apiVersion": "v1",
        "kind": "Config",
        "clusters": [
            {
                "name": "teamdesk",
                "cluster": {
                    "server": server,
                    "certificate-authority-data": cluster["certificate-authority-data"],
                },
            }
        ],
        "users": [{"name": "github-deploy", "user": {"token": token}}],
        "contexts": [
            {
                "name": "teamdesk",
                "context": {
                    "cluster": "teamdesk",
                    "user": "github-deploy",
                    "namespace": "teamdesk",
                },
            }
        ],
        "current-context": "teamdesk",
    }
    encoded = base64.b64encode(json.dumps(config).encode()).decode()
    subprocess.run(
        ["gh", "secret", "set", "KUBE_CONFIG_DATA", "--repo", REPOSITORY],
        input=encoded,
        text=True,
        capture_output=True,
        check=True,
    )
    subprocess.run(
        [
            "gh",
            "variable",
            "set",
            "DEPLOY_TO_EKS",
            "--repo",
            REPOSITORY,
            "--body",
            "true",
        ],
        check=True,
    )
    expires = datetime.fromtimestamp(claims["exp"], tz=timezone.utc).isoformat()
    print(f"Deployment secret saved to {REPOSITORY}; token expires {expires}.")
    print("No credential was printed or saved to a local file.")


if __name__ == "__main__":
    main()
