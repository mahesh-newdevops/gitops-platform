#!/usr/bin/env python3
import argparse
import os
import pathlib
import sys

ADDONS = {
    "aws_load_balancer_controller": "argocd/apps/aws-load-balancer-controller.yaml",
    "prometheus": "argocd/apps/prometheus.yaml",
    "loki": "argocd/apps/loki.yaml",
    "metrics_server": "argocd/apps/metrics-server.yaml",
    "cert_manager": "argocd/apps/cert-manager.yaml",
    "external_dns": "argocd/apps/external-dns.yaml",
    "external_secrets": "argocd/apps/external-secrets.yaml",
    "kyverno": "argocd/apps/kyverno.yaml",
    "trivy_operator": "argocd/apps/trivy-operator.yaml",
    "reloader": "argocd/apps/reloader.yaml",
    "karpenter": "argocd/apps/karpenter.yaml",
    "istio": "argocd/optional/istio-applicationset.yaml",
    "karpenter_manifests": "argocd/apps/karpenter-manifests-application.yaml",
}

ENV_OVERRIDES = {
    "aws_load_balancer_controller": "ADDON_AWS_LOAD_BALANCER_CONTROLLER",
    "prometheus": "ADDON_PROMETHEUS",
    "loki": "ADDON_LOKI",
    "metrics_server": "ADDON_METRICS_SERVER",
    "cert_manager": "ADDON_CERT_MANAGER",
    "external_dns": "ADDON_EXTERNAL_DNS",
    "external_secrets": "ADDON_EXTERNAL_SECRETS",
    "kyverno": "ADDON_KYVERNO",
    "trivy_operator": "ADDON_TRIVY_OPERATOR",
    "reloader": "ADDON_RELOADER",
    "karpenter": "ADDON_KARPENTER",
    "istio": "ADDON_ISTIO",
    "karpenter_manifests": "ADDON_KARPENTER_MANIFESTS",
}


def load_yaml(path):
    addons = {}
    in_addons = False
    current = None

    for raw_line in path.read_text().splitlines():
        line = raw_line.split("#", 1)[0].rstrip()
        if not line:
            continue
        if line == "addons:":
            in_addons = True
            continue
        if not in_addons:
            continue
        if line.startswith("  ") and not line.startswith("    ") and line.endswith(":"):
            current = line.strip()[:-1]
            addons[current] = {}
            continue
        if current and line.startswith("    enabled:"):
            value = line.split(":", 1)[1].strip().lower()
            addons[current]["enabled"] = value == "true"

    return {"addons": addons}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="addons.yaml")
    parser.add_argument("--action", choices=["apply", "destroy"], required=True)
    args = parser.parse_args()

    root = pathlib.Path.cwd()
    config = load_yaml(root / args.config)
    addons = config.get("addons", {})

    enabled = []
    for name, manifest in ADDONS.items():
        is_enabled = addons.get(name, {}).get("enabled", False)
        override = os.environ.get(ENV_OVERRIDES[name])
        if override is not None and override != "":
            is_enabled = override.lower() == "true"
        if is_enabled:
            enabled.append(root / manifest)

    if not enabled:
        print("No add-ons enabled in addons.yaml", file=sys.stderr)
        return 1

    if args.action == "destroy":
        enabled.reverse()

    for path in enabled:
        if not path.exists():
            print(f"Missing manifest: {path}", file=sys.stderr)
            return 1
        print(path)


if __name__ == "__main__":
    raise SystemExit(main())
