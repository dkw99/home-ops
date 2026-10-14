# Envoy connections to services outside Kubernetes

Envoy Gateway exposes NAS applications through Kubernetes HTTPRoutes while the
applications continue running in Synology Compose projects. Here, “external”
means a backend outside Kubernetes. These NAS routes use `envoy-internal`;
this document does not make them publicly accessible through `envoy-external`.

## Traffic and DNS

```mermaid
flowchart LR
    Browser -->|HTTPS hostname| Gateway[envoy-internal: 10.44.0.2]
    Gateway --> Route[HTTPRoute in network]
    Route --> Service[Selectorless Service]
    Service --> Slice[EndpointSlice]
    Slice -->|NAS published host port| NAS[Synology: 192.168.2.30]
```

The HTTPS listener terminates TLS using the existing domain certificate. Each
route references a dedicated Service, whose manually maintained EndpointSlice
points at the NAS IP and **published host port**. Container ports and container
network addresses are not generally reachable backends from Kubernetes.

Both internal external-dns controllers watch HTTPRoutes. The internal gateway
advertises `internal.${SECRET_DOMAIN}` as the DNS target, resolving to
`10.44.0.2`. OPNsense and Synology maintain their respective DNS views. Keep the
HTTPRoute hostname and DNS consistent; do not create a competing NAS-target
record or a separate Synology reverse proxy rule for this path. See
[DNS configuration](README.md#external-dns-layout) for controller ownership and
server details. TLS and existing access controls remain owned by the gateway
configuration.

## Folder ownership

Use the NAS container's `com.docker.compose.project` label to select its folder.
Match both the folder and Flux Kustomization name to the Compose project:

| Compose project | Route definitions | Flux owner |
| --- | --- | --- |
| `media-stack` | `media-stack/app/<application>/` | `network/media-stack` |
| `homepage` | `homepage/app/` | `network/homepage` |
| `heimdall` | `heimdall/app/` | `network/heimdall` |
| `gatus` | `gatus/app/` | `network/gatus` |

Each project has `ks.yaml`, included by this directory's `kustomization.yaml`.
Each app directory includes `ingress.yaml`, `service.yaml`, and
`endpointslice.yaml` through its own `kustomization.yaml`. Media-stack's parent
app Kustomization includes its application subfolders. Flux owners use
`targetNamespace: network`, an explicit `sourceRef.namespace: flux-system`, and
the established `${SECRET_DOMAIN}` substitution from cluster secrets.

`openspeedtest/` and `readarr/` retain legacy routes in separate folders. Neither
had a current NAS container on 2026-10-14, so their Compose project ownership and
backend availability are unverified. Their existing routes are preserved; do
not treat their presence or EndpointSlice `ready: true` as proof of health.
`nas/` is the separate DSM management endpoint, not a Compose project. It uses
an HTTPS backend on port 5001 with `appProtocol: https`; ordinary NAS web apps
use the verified HTTP host port.

## Configured endpoint inventory

The table records configuration preserved during the folder migration, not a
claim that every legacy endpoint is healthy. Resource names such as `jellyseer`
and `qbittorrent` are retained even where container names differ.

| Project folder | Route | Hostname | Configured backend |
| --- | --- | --- | --- |
| gatus | gatus | gatus.wisesalmon.net | 192.168.2.30:8085 |
| heimdall | heimdall | heimdall.wisesalmon.net | 192.168.2.30:80 |
| homepage | homepage | homepage.wisesalmon.net | 192.168.2.30:3001 |
| media-stack | bazarr | bazarr.wisesalmon.net | 192.168.2.30:6767 |
| media-stack | cleanuparr | cleanuparr.wisesalmon.net | 192.168.2.30:11011 |
| media-stack | jellyseer | team-seer.wisesalmon.net | 192.168.2.30:5055 |
| media-stack | maintainerr | maintainerr.wisesalmon.net | 192.168.2.30:6246 |
| media-stack | prowlarr | prowlarr.wisesalmon.net | 192.168.2.30:9696 |
| media-stack | qbittorrent | qbittorrent.wisesalmon.net | 192.168.2.30:8200 |
| media-stack | radarr | radarr.wisesalmon.net | 192.168.2.30:7878 |
| media-stack | sabnzbd | sabnzbd.wisesalmon.net | 192.168.2.30:8100 |
| media-stack | sonarr | sonarr.wisesalmon.net | 192.168.2.30:8989 |
| media-stack | tautulli | tautulli.wisesalmon.net | 192.168.2.30:8181 |
| openspeedtest | openspeedtest | openspeedtest.wisesalmon.net | 192.168.2.30:3000 |
| readarr | readarr | readarr.wisesalmon.net | 192.168.2.30:8787 |

DSM management additionally uses `nas.wisesalmon.net` → `192.168.2.30:5001`.

Known pre-existing mismatches remain outside this folder-only migration:
Heimdall's backend is configured as port 80 while its container publishes 8088;
Seerr's legacy hostname is `team-seer.wisesalmon.net`, with resource name
`jellyseer`. Do not silently change hostnames, backend ports, or access policies
while moving definitions. Verify and fix those separately when requested.

## Adding an application

1. Inspect the running container's Compose project label, network mode, and
   published HTTP binding over noninteractive NAS SSH. Shared VPN namespaces
   need application-specific verification; qBittorrent publishes through Gluetun.
2. Inspect existing routes, DNS records, listeners, and access policies for
   conflicts. Select the owning project folder using the rule above.
3. Reuse an existing project Flux owner or create `<project>/ks.yaml` and include
   it in the network parent. Add the app's HTTPRoute, selectorless Service,
   EndpointSlice, and local Kustomization. Reuse the Maintainerr files as a
   structural example, without copying its port or assuming media-stack ownership.
4. Keep the route backend port, Service port/targetPort, and EndpointSlice named
   port consistent with the verified NAS host port. Keep the EndpointSlice's
   `kubernetes.io/service-name` label consistent with the Service name.
5. Build the affected app/project and network Kustomizations, validate the Flux
   graph using the version and command in `.github/workflows/flux-local.yaml`,
   and review the complete diff. Commit/push only within the authorized scope.
6. Verify Flux revision/Ready status, HTTPRoute Accepted and ResolvedRefs at the
   current generation, backend mapping, DNS in both views, and HTTPS with normal
   certificate verification. An accepted route alone does not prove a working app.

The [NAS route skill](../../../.agents/skills/home-ops-add-nas-route/SKILL.md)
provides the deployment workflow. Application Compose files, secrets, and
appdata deployment remain owned by the sibling Synology repository.

## Moving Flux ownership safely

A folder rename can also replace a Flux Kustomization. With pruning/deletion
policies enabled, deleting the old owner can remove its routes and backends.
The global child defaults in `kubernetes/flux/cluster/ks.yaml` enforce
`deletionPolicy: WaitForTermination`; an `Orphan` value only in a child manifest
would be overwritten by those defaults.

For this migration:

1. A preparatory GitOps change set the old `network/media-pvr-ext` owner to
   `prune: false`. A targeted patch after the global defaults set its deletion
   policy to `Orphan`. Both settings and the applied revision were verified live
   before publishing the moves.
2. The next change moved definitions to their project folders, introduced the
   matching Flux owners, and removed the old owner/include and temporary patch.
   All 45 HTTPRoute/Service/EndpointSlice definitions were compared before and
   after and remained identical. New owners retain normal pruning.
3. Verify that all new owners are Ready and their inventories contain the
   expected resources. Compare resource UIDs to the pre-change snapshot to
   establish that routes/backends were adopted rather than recreated.

Pre-change snapshots and rollback notes are stored outside Git under
`~/.local/state/home-ops/envoy-project-migration/20261014T113900Z/`.

To roll back a completed ownership migration, first make the current owners
preserve their children (`prune: false` and an effective `Orphan` deletion
policy, accounting for global defaults), push, and verify the live settings.
Then restore the previous layout/owner through GitOps and verify adoption before
removing the temporary owners. A blind revert of a rename with pruning enabled
can delete resources. Do not manually delete controller-owned DNS records;
external-dns reconciles from the preserved routes.

References: [Flux pruning and deletion policy](https://fluxcd.io/flux/components/kustomize/kustomizations/#deletion-policy),
[Envoy Gateway HTTP routing](https://gateway.envoyproxy.io/docs/tasks/traffic/http-routing/),
[Kubernetes services without selectors](https://kubernetes.io/docs/concepts/services-networking/service/#services-without-selectors).

## Verified migration result — 2026-10-14

Preparatory commits `70b7eebd` and `bef42a8b` established and verified the old
owner's preservation policy. Migration commit `c1995d28` was pushed to `main`.
All six new Flux owners became Ready at that revision and the old
`media-pvr-ext` owner was removed. Inventories contain 30 resources for
`media-stack` and three each for Homepage, Heimdall, Gatus, OpenSpeedTest, and
Readarr. All 45 resources retained their original UIDs and route/backend
settings. All 15 routes reported Accepted and ResolvedRefs at their current
generations. Kustomize builds, skill reference validation, and all 69
Flux-local v8.4.0 tests passed.

Homepage and Gatus returned HTTPS 200. Representative Homepage, Gatus, and
Sonarr records resolved through `internal.wisesalmon.net` to `10.44.0.2` in
both DNS views. Several full-page probes timed out intermittently; Bazarr and
Prowlarr passed repeat checks, and Sonarr's `/ping` passed through both the
gateway and direct NAS listener. These probes do not prove application login
or all page behavior. Existing failures remain: Heimdall returned 500;
OpenSpeedTest and Readarr returned 503; `team-seer.wisesalmon.net` did not
resolve. Those failures were also present before the migration and were not
changed by moving ownership. Detailed before/after evidence is in the private
snapshot directory above.
