# Network Apps

This directory contains the cluster workloads that expose services and publish DNS records for internal and external access.

## NAS application routing

See [Envoy external connections](envoy-external-connections.md) for the traffic
path, project folder convention, endpoint inventory, addition workflow, and safe
Flux ownership migrations. NAS app routes are grouped by their Compose project;
only media-stack services belong under `media-stack/`.

## NAS Flux Source

The NAS Flux Kustomization runs in `network`, as set by this directory's
`kustomization.yaml`. Its `sourceRef.namespace` must explicitly be `flux-system`
to use the GitRepository `flux-system/flux-system`. Without it, Flux searches
in `network` and fails with `GitRepository "flux-system" not found`.

The source reference was corrected in Git and patched live on 2026-10-11;
live reconciliation succeeded and created the NAS Service and HTTPRoute.
Commit and push the manifest correction so future reconciliations retain it.
After deployment, confirm
`kubectl -n network get kustomization nas` reports Ready and that the NAS Service
and HTTPRoute exist. Use the explicit kubeconfig path shown below.

## External DNS Layout

The cluster runs two internal `external-dns` instances:

- `external-dns-internal-opnsense`
- `external-dns-internal-synology`

Both are installed through Flux and use the upstream `external-dns` chart mirrored under `ghcr.io/home-operations/charts-mirror/external-dns`.

## What They Manage

Each instance watches Kubernetes `Service` and `Gateway` `HTTPRoute` sources and syncs DNS records via RFC2136.

- OPNsense instance:
  - RFC2136 host: `192.168.16.1`
  - RFC2136 port: `53530`
  - RFC2136 zone: `${SECRET_DOMAIN}`
  - TSIG key name: `rndc-key`
  - TSIG secret: `ROUTER_RNDC_KEY`
  - TXT prefix: `external-dns-`

- Synology instance:
  - RFC2136 host: `192.168.16.30`
  - RFC2136 port: `53`
  - RFC2136 zone: `${SECRET_DOMAIN}`
  - TSIG key name: `rndc-key-synology`
  - TSIG secret: `SYNOLOGY_RNDC_KEY`
  - TXT prefix: `external-dns-syn-`

Both instances use:

- `sources: ["service", "gateway-httproute"]`
- `policy: sync`
- `txtOwnerId: k8s`
- `domainFilters: ["${SECRET_DOMAIN}"]`
- `triggerLoopOnEvent: true`

## Secrets

The TSIG secrets are stored in the cluster-wide SOPS secret bundle:

- `kubernetes/components/sops/cluster-secrets.sops.yaml`

Relevant keys:

- `ROUTER_RNDC_KEY`
- `SYNOLOGY_RNDC_KEY`

Do not commit decrypted secret material.

## Flux Resources

Kustomize includes both releases from:

- `kubernetes/apps/network/kustomization.yaml`

Relevant paths:

- `kubernetes/apps/network/external-dns-internal-opnsense/`
- `kubernetes/apps/network/external-dns-internal-synology/`

## Common Record Sources

The network layer already annotates workloads with `external-dns` hints, including:

- `external-dns.alpha.kubernetes.io/hostname`
- `external-dns.alpha.kubernetes.io/target`
- `external-dns.alpha.kubernetes.io/controller`

Typical examples live in:

- `kubernetes/apps/network/envoy-gateway/app/envoy.yaml`
- `kubernetes/apps/network/cloudflare-tunnel/app/dnsendpoint.yaml`

## Setup Notes

To use this pattern in another cluster:

1. Create a TSIG key on the DNS server you want external-dns to update.
2. Store the key in SOPS as a cluster secret.
3. Configure one external-dns release per DNS backend.
4. Point each release at the correct RFC2136 host, port, key name, and zone.
5. Annotate Kubernetes Services or Gateways with the DNS hostname you want published.

For OPNsense and Synology specifically, make sure the DNS server allows RFC2136 updates for the zone and that the TSIG key name matches the server-side configuration exactly.

## Validation

After changing DNS resources, verify the Flux objects and the resulting records:

```bash
kubectl --kubeconfig /home/dkwise/home-lab/repos/dkw99/home-ops/kubeconfig \
  -n network get helmrelease,po
```

Check the external-dns logs if records do not appear:

```bash
kubectl --kubeconfig /home/dkwise/home-lab/repos/dkw99/home-ops/kubeconfig \
  -n network logs deploy/external-dns-internal-opnsense
```

```bash
kubectl --kubeconfig /home/dkwise/home-lab/repos/dkw99/home-ops/kubeconfig \
  -n network logs deploy/external-dns-internal-synology
```
