# Troubleshooting exercises

These exercises deliberately break a small web server in the separate `teamdesk-troubleshooting` namespace. They do not change the real TeamDesk Deployments, database, Ingress or monitoring. The server reuses our backend image's Python runtime to serve an empty directory; it has no database settings, API token, persistent disk or public load balancer.

Run from the repository root with `KUBECONFIG` pointing to `.local/kubeconfig`. The manifest is intentionally broken and must not be included in the application's normal Helm deployment.

## 1. ImagePullBackOff

Create the lab and inspect the failure:

```sh
kubectl apply -f troubleshooting/lab.yaml
kubectl get pods -n teamdesk-troubleshooting
kubectl describe pods -n teamdesk-troubleshooting -l app=lab-web
```

The pod remains unready and moves between `ErrImagePull` and `ImagePullBackOff`. Its events report `missing-demo-tag: not found`. The container never started, so application logs cannot explain this failure. Check the image reference and registry availability first.

Fix the Deployment to use a real, published image tag:

```sh
kubectl set image deployment/lab-web -n teamdesk-troubleshooting \
  web=ghcr.io/suhaniawasthi10/teamdesk-backend:d9bbe6bbbdf528c963227b77cf3c36854ca70991
kubectl rollout status deployment/lab-web -n teamdesk-troubleshooting --timeout=120s
kubectl get pods -n teamdesk-troubleshooting
```

Recovery means the new pod is `1/1 Running` and the rollout succeeds. In an application release, correct the source image configuration and redeploy; deleting the failed pod alone would reproduce the same bad image reference.

## 2. Service selector mismatch

The pod is now healthy, but its Service still selects `app=lab-typo`; the pod is labelled `app=lab-web`. A Service can exist and have a ClusterIP while selecting no backend pods.

```sh
kubectl get pods -n teamdesk-troubleshooting --show-labels
kubectl get service lab-web -n teamdesk-troubleshooting -o yaml
kubectl get endpointslices -n teamdesk-troubleshooting \
  -l kubernetes.io/service-name=lab-web
```

Confirm the process works locally, then try the Service from inside the cluster:

```sh
kubectl exec deployment/lab-web -n teamdesk-troubleshooting -- python -c \
  'from urllib.request import urlopen; print(urlopen("http://127.0.0.1:8000", timeout=3).status)'
kubectl exec deployment/lab-web -n teamdesk-troubleshooting -- python -c \
  'from urllib.request import urlopen; print(urlopen("http://lab-web:8000", timeout=3).status)'
```

The local request returns `200`; the Service request fails while the EndpointSlice has no addresses. This narrows the problem to Service routing rather than the application process.

Fix the selector and repeat the Service request:

```sh
kubectl patch service lab-web -n teamdesk-troubleshooting --type merge \
  -p '{"spec":{"selector":{"app":"lab-web"}}}'
kubectl get endpointslices -n teamdesk-troubleshooting \
  -l kubernetes.io/service-name=lab-web
kubectl exec deployment/lab-web -n teamdesk-troubleshooting -- python -c \
  'from urllib.request import urlopen; print(urlopen("http://lab-web:8000", timeout=3).status)'
```

Recovery means the EndpointSlice contains the ready pod's address and the Service request returns `200`. A matching `targetPort` also matters; this lab uses the named `http` container port, 8000.

## Cleanup

After the demonstration, remove only the isolated lab:

```sh
kubectl delete namespace teamdesk-troubleshooting --wait=true
kubectl get namespace teamdesk-troubleshooting --ignore-not-found
kubectl get pods -n teamdesk
```

The namespace check should return no resource, while the real application remains healthy. Reapplying `lab.yaml` recreates both intentional faults for a later presentation.

## Verified results

Both exercises were run on EKS on 16 October 2026. The bad image produced `ErrImagePull` and `ImagePullBackOff`, with registry events reporting that the tag was not found; replacing it with the published SHA produced a successful rollout and a ready pod. With the incorrect Service selector, the EndpointSlice had no addresses: localhost returned HTTP 200 while the Service request failed. Correcting the selector populated a ready endpoint and the Service returned HTTP 200.

References: [Kubernetes image failures](https://kubernetes.io/docs/concepts/containers/images/), [debugging Services](https://kubernetes.io/docs/tasks/debug/debug-application/debug-service/).
