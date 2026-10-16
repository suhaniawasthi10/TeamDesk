# TeamDesk monitoring

Prometheus scrapes both backend replicas every 15 seconds through a ServiceMonitor. Grafana provisions the **TeamDesk · API overview** dashboard from the checked-in JSON. Its panels show real HTTP counters, request rate, response time, server errors and healthy scrape targets.

The stack uses `prometheus-community/kube-prometheus-stack` **92.9.0**. Separate Prometheus and Grafana values keep resource requests small for the two-node EKS cluster. Prometheus retains six hours of metrics on a 5 GiB encrypted gp3 volume; Grafana has a 2 GiB volume. Services remain private, with browser access through localhost port-forwards. EKS-managed etcd, scheduler and controller-manager scraping is disabled because those endpoints are not exposed to the workers.

## Install

Run from the repository root after the EKS application and `teamdesk-gp3` StorageClass are ready:

```sh
export KUBECONFIG="$PWD/.local/kubeconfig"
kubectl apply -f monitoring/namespace.yaml
python3 scripts/create_monitoring_secret.py
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update prometheus-community
helm upgrade --install monitoring prometheus-community/kube-prometheus-stack \
  --version 92.9.0 --namespace monitoring \
  -f monitoring/prometheus-values.yaml -f monitoring/grafana-values.yaml \
  --wait --timeout 10m
kubectl apply -f monitoring/teamdesk-servicemonitor.yaml
kubectl create configmap teamdesk-dashboard -n monitoring \
  --from-file=teamdesk-overview.json=monitoring/teamdesk-dashboard.json \
  --dry-run=client -o yaml | kubectl apply -f -
kubectl label configmap teamdesk-dashboard -n monitoring grafana_dashboard=1 --overwrite
```

The secret helper preserves an existing admin password. It generates a random password for a new installation and sends it directly to Kubernetes without printing it or writing it to disk.

## View and verify

Keep each port-forward running in its own terminal:

```sh
kubectl port-forward -n monitoring svc/monitoring-kube-prometheus-prometheus 9090:9090
```

```sh
kubectl port-forward -n monitoring svc/monitoring-grafana 3001:80
```

Open http://localhost:9090/targets and find `serviceMonitor/monitoring/teamdesk/0`. Both backend targets should be **UP**. Open http://localhost:3001/d/teamdesk-overview for the dashboard. Sign in as `admin`; on macOS, copy the password directly to the clipboard with:

```sh
kubectl get secret grafana-admin -n monitoring \
  -o jsonpath='{.data.admin-password}' | base64 --decode | pbcopy
```

Use TeamDesk to generate requests, then allow two scrapes for rate panels to populate. Request counters reset when a backend pod is replaced; `rate()` accounts for counter resets. A zero error rate is valid when no 5xx responses occurred.

```sh
kubectl get pods,pvc -n monitoring
curl -s http://localhost:9090/api/v1/query \
  --data-urlencode 'query=up{namespace="teamdesk",service="teamdesk-backend"}'
```

For submission, capture the backend's `/metrics` output, Prometheus Targets with both application targets UP, and the Grafana dashboard with populated panels. Keep passwords and login forms out of screenshots.

## Cleanup

After the demo and screenshots, uninstall monitoring before destroying EKS. Deleting these claims permanently removes the demo's historical metrics and Grafana state; the dashboard source stays in Git.

```sh
helm uninstall monitoring -n monitoring
kubectl delete pvc --all -n monitoring
kubectl delete namespace monitoring
```

Wait for its EBS volumes to disappear before removing the EBS CSI controller or running Terraform destroy. Prometheus Operator CRDs are cluster-scoped and Helm may retain them; deleting the disposable EKS cluster removes those definitions.

References: [Prometheus community chart](https://github.com/prometheus-community/helm-charts/tree/main/charts/kube-prometheus-stack), [ServiceMonitor specification](https://prometheus-operator.dev/docs/api-reference/api/#monitoring.coreos.com/v1.ServiceMonitor).
