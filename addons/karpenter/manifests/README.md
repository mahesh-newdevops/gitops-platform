# Karpenter Manifests

Replace these placeholders before syncing:

- `__KARPENTER_NODE_ROLE_NAME__`
- `__EKS_CLUSTER_NAME__`

The matching subnets and security groups must be tagged with:

```text
karpenter.sh/discovery = <cluster-name>
```

