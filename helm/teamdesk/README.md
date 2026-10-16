# Deploy TeamDesk on EKS

Run these commands from the repository root after applying `terraform/`.
Terraform installs the EBS CSI driver and Pod Identity agent, with separate IAM
roles for storage and the AWS Load Balancer Controller. The controller itself
is installed with Helm.

```sh
export AWS_PROFILE=teamdesk
export AWS_REGION=ap-southeast-2
export KUBECONFIG="$PWD/.local/kubeconfig"
mkdir -p .local
aws eks update-kubeconfig --name teamdesk --alias teamdesk
kubectl get nodes

TEAMDESK_VPC_ID=$(terraform -chdir=terraform output -raw vpc_id)
helm upgrade --install aws-load-balancer-controller aws-load-balancer-controller \
  --repo https://aws.github.io/eks-charts --version 3.6.0 \
  --namespace kube-system -f k8s/load-balancer-values.yaml \
  --set "vpcId=$TEAMDESK_VPC_ID" --wait --timeout 5m

kubectl apply -f k8s/namespace.yaml -f k8s/storage-class.yaml
python3 scripts/create_cluster_secret.py
helm lint helm/teamdesk
helm upgrade --install teamdesk helm/teamdesk --namespace teamdesk \
  --wait --wait-for-jobs --timeout 10m --history-max 5
```

The chart defaults to a verified full-SHA release from the public GHCR packages.
For an update, pass `--set-string image.tag=<full-commit-sha>` after that commit's
image pipeline succeeds. Both application images use the same tag. Neither
application container runs as root.

The secret helper generates a password and sends it to Kubernetes through stdin.
It preserves an existing `teamdesk-db` Secret, so rerunning setup does not change
the password of an existing database. It does not write credentials into Helm
values, Terraform state or a local file. Kubernetes Secrets are base64-encoded,
not encrypted by that encoding; access is controlled through Kubernetes RBAC and
the cluster's storage encryption. Do not display or screenshot Secret contents.

## Startup and traffic

PostgreSQL runs as a single StatefulSet replica with a 5 GiB encrypted gp3 volume.
This is persistent demonstration storage, not a highly available database.
Each Helm revision creates one migration Job. It waits for PostgreSQL, runs
`alembic upgrade head`, and exits. Backend init containers wait for the image's
Alembic head before starting the API; two replicas do not race to migrate the
same schema. Completed migration Jobs are removed automatically after two minutes.

The frontend and backend each have two replicas, readiness checks and CPU/memory
requests and limits. Their Services are ClusterIP. The `alb` Ingress sends `/api`
to the backend and `/` to the frontend; Nginx also proxies API documentation,
health checks and metrics. The controller creates one internet-facing ALB in the
two public subnets, targeting pod IPs in the private subnets.

The demo uses HTTP and synthetic employee records. A production service would
need authentication, HTTPS with a domain/certificate, backups and a database
availability plan.

## Verify and capture evidence

```sh
kubectl get pods -n teamdesk
kubectl get deployments,svc,ingress,pvc -n teamdesk
helm list -n teamdesk
TEAMDESK_HOST=$(kubectl get ingress teamdesk -n teamdesk \
  -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
.venv/bin/python scripts/smoke_backend.py --url "http://$TEAMDESK_HOST"
```

Allow a few minutes for the ALB address to become reachable. Open its HTTP address,
add synthetic employees and verify editing/deletion. Capture `M8-pods.png`,
`M8-services.png`, `M8-helm.png` and `M8-application.png` in `evidence/`.

For a failed rollout, inspect `kubectl get events -n teamdesk --sort-by=.lastTimestamp`,
the affected pod's `describe` output, and its logs. `helm history teamdesk -n teamdesk`
shows revisions. An application rollback does not undo database migrations;
keep migrations compatible with the previous release or plan a separate recovery.

## Cleanup after the demonstration

Remove monitoring first when installed, then run:

```sh
helm uninstall teamdesk -n teamdesk --wait --timeout 10m
```

Wait for the Ingress-created ALB, target groups and security groups to disappear
before removing its controller. StatefulSet PVCs and the separately created Secret
remain after uninstall, deliberately preserving the database. Only when its data
is no longer needed, delete the database claim and Secret:

```sh
kubectl delete pvc data-teamdesk-postgres-0 -n teamdesk
kubectl delete secret teamdesk-db -n teamdesk
```

Verify the EBS volume is deleted while the CSI driver is still installed. Then
uninstall `aws-load-balancer-controller` from `kube-system` and follow the
[Terraform cleanup instructions](../../terraform/README.md#cleanup). Do not run
Terraform destroy first: it cannot clean up AWS resources owned by Kubernetes.
