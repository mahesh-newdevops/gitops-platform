#!/usr/bin/env python3
import argparse
import os
import pathlib
import re
import shutil
import sys

ADDONS = [
    ("cert_manager", "argocd/apps/cert-manager.yaml"),
    ("metrics_server", "argocd/apps/metrics-server.yaml"),
    ("aws_load_balancer_controller", "argocd/apps/aws-load-balancer-controller.yaml"),
    ("external_secrets", "argocd/apps/external-secrets.yaml"),
    ("external_dns", "argocd/apps/external-dns.yaml"),
    ("kyverno", "argocd/apps/kyverno.yaml"),
    ("trivy_operator", "argocd/apps/trivy-operator.yaml"),
    ("reloader", "argocd/apps/reloader.yaml"),
    ("karpenter", "argocd/apps/karpenter.yaml"),
    ("karpenter_manifests", "argocd/apps/karpenter-manifests-application.yaml"),
    ("prometheus", "argocd/apps/prometheus.yaml"),
    ("loki", "argocd/apps/loki.yaml"),
    ("istio", "argocd/optional/istio-applicationset.yaml"),
    ("microservices_apps_deploy", "argocd/apps/microservices-apps-deploy.yaml"),
]

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
    "microservices_apps_deploy": "ADDON_MICROSERVICES_APPS_DEPLOY",
}

PLACEHOLDERS = {
    "__EKS_CLUSTER_NAME__": "EKS_CLUSTER_NAME",
    "__AWS_REGION__": "AWS_REGION",
    "__VPC_ID__": "VPC_ID",
    "__DOMAIN_FILTER__": "DOMAIN_FILTER",
    "__EXTERNAL_DNS_ROLE_ARN__": "EXTERNAL_DNS_ROLE_ARN",
    "__KARPENTER_INTERRUPTION_QUEUE__": "KARPENTER_INTERRUPTION_QUEUE",
    "__KARPENTER_NODE_ROLE_NAME__": "KARPENTER_NODE_ROLE_NAME",
}

PLACEHOLDER_RE = re.compile(r"__[A-Z0-9_]+__")


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
    parser.add_argument("--output-dir", help="Render manifests into this directory before printing paths")
    args = parser.parse_args()

    root = pathlib.Path.cwd()
    config = load_yaml(root / args.config)
    addons = config.get("addons", {})

    enabled = []
    for name, manifest in ADDONS:
        is_enabled = addons.get(name, {}).get("enabled", False)
        override = os.environ.get(ENV_OVERRIDES[name])
        if override is not None and override != "":
            is_enabled = override.lower() == "true"
        if is_enabled:
            enabled.append((name, root / manifest))

    if not enabled:
        print("No add-ons enabled in addons.yaml", file=sys.stderr)
        return 1

    if args.action == "destroy":
        enabled.reverse()

    output_root = pathlib.Path(args.output_dir) if args.output_dir else None
    if output_root and args.action == "apply":
        if output_root.exists():
            shutil.rmtree(output_root)
        output_root.mkdir(parents=True)

    for _, path in enabled:
        if not path.exists():
            print(f"Missing manifest: {path}", file=sys.stderr)
            return 1

        rendered_path = path
        if output_root and args.action == "apply":
            content = path.read_text()
            for placeholder, env_name in PLACEHOLDERS.items():
                value = os.environ.get(env_name, "")
                if value:
                    content = content.replace(placeholder, value)

            leftovers = sorted(set(PLACEHOLDER_RE.findall(content)))
            if leftovers:
                required = ", ".join(f"{token}->{PLACEHOLDERS.get(token, 'UNKNOWN_ENV')}" for token in leftovers)
                print(f"Unresolved placeholders in {path}: {required}", file=sys.stderr)
                return 1

            rendered_path = output_root / path.relative_to(root)
            rendered_path.parent.mkdir(parents=True, exist_ok=True)
            rendered_path.write_text(content)

        print(rendered_path)


if __name__ == "__main__":
    raise SystemExit(main())
