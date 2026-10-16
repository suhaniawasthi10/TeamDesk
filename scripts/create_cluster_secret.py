"""Create TeamDesk's database secret without printing or saving its password."""

import json
import os
import secrets
import subprocess


def main():
    if not os.environ.get("KUBECONFIG"):
        raise SystemExit("Set KUBECONFIG to the project's .local/kubeconfig first.")
    kubectl = ["kubectl", "--context", "teamdesk", "--namespace", "teamdesk"]
    existing = subprocess.run(
        [*kubectl, "get", "secret", "teamdesk-db", "--ignore-not-found", "-o", "name"],
        check=True,
        capture_output=True,
        text=True,
    )
    if existing.stdout.strip():
        print("Keeping existing teamdesk-db secret and database password.")
        return

    password = secrets.token_urlsafe(32)
    secret = {
        "apiVersion": "v1",
        "kind": "Secret",
        "metadata": {"name": "teamdesk-db", "namespace": "teamdesk"},
        "type": "Opaque",
        "stringData": {
            "POSTGRES_PASSWORD": password,
            "DATABASE_URL": (
                f"postgresql+psycopg://teamdesk:{password}"
                "@teamdesk-postgres:5432/teamdesk"
            ),
        },
    }
    result = subprocess.run(
        [*kubectl, "create", "-f", "-"],
        input=json.dumps(secret),
        capture_output=True,
        text=True,
    )
    if result.returncode:
        # Do not echo API error bodies that might include the submitted manifest.
        raise SystemExit(
            "Secret creation failed; check Kubernetes access and namespace."
        )
    print("Created teamdesk-db; the password was not printed or saved locally.")


if __name__ == "__main__":
    main()
