"""Create Grafana's admin credential without printing or saving its password."""

import json
import os
import secrets
import subprocess


def main():
    if not os.environ.get("KUBECONFIG"):
        raise SystemExit("Set KUBECONFIG to the project's .local/kubeconfig first.")
    kubectl = ["kubectl", "--context", "teamdesk", "-n", "monitoring"]
    existing = subprocess.run(
        [
            *kubectl,
            "get",
            "secret",
            "grafana-admin",
            "--ignore-not-found",
            "-o",
            "name",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    if existing.stdout.strip():
        print("Keeping the existing Grafana admin credential.")
        return
    secret = {
        "apiVersion": "v1",
        "kind": "Secret",
        "type": "Opaque",
        "metadata": {"name": "grafana-admin", "namespace": "monitoring"},
        "stringData": {
            "admin-user": "admin",
            "admin-password": secrets.token_urlsafe(32),
        },
    }
    result = subprocess.run(
        [*kubectl, "create", "-f", "-"],
        input=json.dumps(secret),
        capture_output=True,
        text=True,
    )
    if result.returncode:
        raise SystemExit("Secret creation failed; check cluster access and namespace.")
    print("Created grafana-admin; no credential was printed or saved locally.")


if __name__ == "__main__":
    main()
