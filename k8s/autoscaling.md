# Backend autoscaling

Metrics Server supplies CPU measurements to Kubernetes. The Helm chart creates an `autoscaling/v2` HorizontalPodAutoscaler for `teamdesk-backend`, with a minimum of two replicas, a maximum of four, and a target of 60% CPU utilization. Each backend requests 100 millicores, so the target is an average of 60 millicores per replica. The HPA changes application pod count; it does not create EC2 workers.

The Deployment omits `spec.replicas` while autoscaling is enabled, so Helm upgrades do not continually reset the HPA's chosen count. Scale-up can add two pods per minute. Scale-down waits for a 120-second stabilization window and then removes at most one pod per minute. The frontend remains at two replicas.

## Install and inspect

Run from the repository root with the project kubeconfig selected:

```sh
export KUBECONFIG="$PWD/.local/kubeconfig"
helm repo add metrics-server https://kubernetes-sigs.github.io/metrics-server/
helm repo update metrics-server
helm upgrade --install metrics-server metrics-server/metrics-server \
  --version 3.14.0 --namespace kube-system \
  -f k8s/metrics-server-values.yaml --wait --timeout 5m
kubectl get apiservice v1beta1.metrics.k8s.io
kubectl top nodes
kubectl top pods -n teamdesk
kubectl get hpa -n teamdesk
```

Chart 3.14.0 installs Metrics Server v0.9.0. Helm generates its serving certificate and supplies the CA to the aggregated APIService; kubelet certificates are checked against the cluster CA. No insecure TLS flags are used.

Deploy the application chart through the normal GitHub Actions workflow to apply its HPA. For a manual update, use the verified full image SHA as shown in the [deployment guide](../helm/teamdesk/README.md). Set `backend.autoscaling.enabled=false` only when intentionally switching back to the fixed `backend.replicas` count.

## Controlled load demonstration

The temporary Job sends up to 120 read-only employee-list requests per second for three minutes. It has CPU/memory limits, a four-minute deadline and no API token. The script stops early on repeated errors. It never adds, edits or deletes employees.

```sh
kubectl create configmap teamdesk-load-check -n teamdesk \
  --from-file=load_backend.py=scripts/load_backend.py
kubectl apply -f k8s/load-check.yaml
kubectl get hpa -n teamdesk --watch
```

In another terminal:

```sh
kubectl top pods -n teamdesk
kubectl get deployments -n teamdesk
kubectl describe hpa teamdesk-backend -n teamdesk
kubectl logs job/teamdesk-load-check -n teamdesk
```

Record actual CPU utilization, current/desired replica counts and `SuccessfulRescale` events. A running traffic generator alone is not proof of scaling. After traffic stops, allow several minutes for metrics and the stabilization window to settle. Verify the backend returns to two ready replicas and that the application remains usable.

To stop the test early or clean up afterward:

```sh
kubectl delete job teamdesk-load-check -n teamdesk --ignore-not-found
kubectl delete configmap teamdesk-load-check -n teamdesk --ignore-not-found
```

If CPU appears as `<unknown>`, inspect Metrics Server readiness/logs, the `metrics.k8s.io` APIService and the backend's CPU requests. Do not lower the target simply to manufacture a successful result.

## Verified demonstration

On 16 October 2026, idle backend CPU was about 3 millicores per pod. The load Job completed 21,496 successful employee-list requests in 180 seconds with zero errors. The HPA recorded CPU above its 60% target and increased the backend from two to three, then four replicas; all four became Ready. The frontend stayed at two replicas and the test did not modify employee records.

After traffic stopped, CPU returned to approximately 3% of the request and the HPA automatically scaled down from four to three, then two ready replicas. All three employee records matched the pre-test data. The temporary Job and ConfigMap were removed after verification.

During final cleanup, uninstall `metrics-server` from `kube-system` before destroying EKS. Application uninstall removes its HPA.

References: [Metrics Server](https://github.com/kubernetes-sigs/metrics-server), [Kubernetes HPA](https://kubernetes.io/docs/concepts/workloads/autoscaling/horizontal-pod-autoscale/).
