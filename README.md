# gitops-platform

ArgoCD GitOps definitions for EKS platform add-ons.

## Layout

```text
gitops-platform/
├── .github/workflows/platform-addons.yml
├── addons.yaml
├── bootstrap/root-app.yaml
├── argocd/apps/
├── argocd/optional/
├── addons/karpenter/manifests/
├── clusters/dev/addons.yaml
└── scripts/render-addons.py
```

## Add-ons

Enabled by default in `addons.yaml`:

- `aws-load-balancer-controller`
- `prometheus` via `kube-prometheus-stack`
- `loki` via `loki-stack`
- `metrics-server`
- `cert-manager`
- `external-secrets`
- `kyverno`
- `trivy-operator`
- `reloader`
- `karpenter` controller
- Karpenter `EC2NodeClass` and `NodePool` manifests
- `microservices-apps-deploy` application workload reference

Disabled by default:

- `external-dns`
- `istio`

## Enable Or Disable Add-ons

Edit `addons.yaml`:

```yaml
addons:
  external_dns:
    enabled: true
  istio:
    enabled: false
```

The GitHub Actions workflow also exposes each add-on as a `true` or `false` input, so one-off apply/destroy runs do not require editing `addons.yaml`.

## Apply Or Destroy

Run the `Platform Add-ons` workflow manually.

Inputs:

- `action`: `apply` or `destroy`
- `environment`: `dev`, `staging`, or `prod`
- `aws_region`
- `cluster_name`
- one `true` or `false` option per add-on
- `microservices_apps_deploy`: include or exclude the EKS application workload ArgoCD reference

The workflow applies or deletes the selected ArgoCD `Application` manifests. ArgoCD then installs, reconciles, or prunes the actual Helm releases, Karpenter manifests, and optional application workloads.

## EKS Application Workloads

`argocd/apps/microservices-apps-deploy.yaml` references:

```text
https://github.com/mahesh-newdevops/microservices-apps-deploy.git
```

When `bootstrap/root-app.yaml` syncs `argocd/apps`, ArgoCD creates this application reference and then follows the app repo's own ArgoCD structure.

## Required Placeholders

Replace placeholders before applying:

- `__EKS_CLUSTER_NAME__`
- `__AWS_REGION__`
- `__VPC_ID__`
- `__AWS_LOAD_BALANCER_CONTROLLER_ROLE_ARN__`
- `__EXTERNAL_DNS_ROLE_ARN__`
- `__EXTERNAL_SECRETS_ROLE_ARN__`
- `__KARPENTER_CONTROLLER_ROLE_ARN__`
- `__KARPENTER_INTERRUPTION_QUEUE__`
- `__KARPENTER_NODE_ROLE_NAME__`

## Optional Istio

Istio stays under `argocd/optional/istio-applicationset.yaml` and is disabled in `addons.yaml` by default. Enable it from the workflow or by setting:

```yaml
addons:
  istio:
    enabled: true
```
