# GitHub Actions deployment

The deployment job runs after successful tests, frontend build, image builds, Trivy scans and GHCR publication. Helm updates both application images to the exact commit SHA. The job waits for migrations and rollouts, then checks the live `/health` version, database readiness and frontend through the Ingress. A failed Helm rollout triggers rollback.

This account's AWS organization policy denies creation of an IAM OIDC provider. The demonstration therefore uses a Kubernetes ServiceAccount with permissions limited to the `teamdesk` namespace. Its token expires after eight hours; no AWS access key is stored in GitHub. The Role includes namespace Secrets because Helm stores release records there, so the deployment credential must still be treated as sensitive.

## Enable or refresh access

The EKS stack must already exist. From the project root:

```sh
export KUBECONFIG="$PWD/.local/kubeconfig"
kubectl apply -f k8s/github-deployer.yaml
gh auth login --hostname github.com --git-protocol ssh --web --skip-ssh-key
python3 scripts/configure_deployment_secret.py
```

Sign in to the personal `suhaniawasthi10` GitHub account. The helper verifies that identity, creates a short-lived token, and sends a minimal kubeconfig directly to the encrypted repository secret `KUBE_CONFIG_DATA`. It sets the repository variable `DEPLOY_TO_EKS=true` and prints only the expiry time. It does not save the token to a local file or commit it.

Push a meaningful change to `main`. The **Deploy to EKS** job should become green and its summary should link to the application. Compare `/health`'s `version` with the commit SHA to verify the release. If access has expired, rerun the helper and rerun the failed job.

Pull requests cannot deploy. Main-branch runs are not cancelled during a Helm operation, preventing an interrupted upgrade from leaving a pending release.

## Disable after the demo

Disable delivery before removing the cluster:

```sh
gh variable set DEPLOY_TO_EKS --body false --repo suhaniawasthi10/TeamDesk-
gh secret delete KUBE_CONFIG_DATA --repo suhaniawasthi10/TeamDesk-
kubectl delete -f k8s/github-deployer.yaml
```

Deleting the ServiceAccount revokes its bound tokens. The test, build, scan and image publication jobs continue to work after the cloud demo ends; deployment is skipped while the variable is false.
