---
name: home-ops-add-nas-route
description: From either home-ops or synology, add HTTPS access to an existing NAS Docker application at container.wisesalmon.net by updating the home-ops Kubernetes repository, validating, committing and pushing to GitHub, then checking GitOps reconciliation. Use for NAS HTTPRoute requests; excludes Synology reverse proxy endpoint management and container deployment.
---

# Add a NAS application HTTPS route through GitOps

Invoke as `$home-ops-add-nas-route add container maintainerr`, or an equivalent request to add its Kubernetes HTTPS route. Discover the NAS host port; derive `maintainerr.wisesalmon.net` unless the user explicitly supplies a different hostname within `wisesalmon.net`.

This skill is available globally through `${CODEX_HOME:-~/.codex}/skills/home-ops-add-nas-route`, linked to its version-controlled source in `home-ops/.agents/skills/`. It can be invoked from either repository or another working directory. Resolve the source symlink before locating repositories or following the relative references below; do not use the caller's current Git root as the Kubernetes repository.

```sh
skill_source=$(readlink -f "${CODEX_HOME:-$HOME/.codex}/skills/home-ops-add-nas-route/SKILL.md") || exit 1
home_ops_root=$(git -C "$(dirname "$skill_source")" rev-parse --show-toplevel) || exit 1
synology_root=$(git -C "$home_ops_root/../synology" rev-parse --show-toplevel) || exit 1
cd "$home_ops_root" || exit 1
```

Read `$home_ops_root/AGENTS.md` and applicable nested instructions before working in `home-ops`. Read `$synology_root/AGENTS.md` for NAS access instructions. Run Kubernetes validation, Git commits and pushes from `home-ops`; use the Synology checkout only for relevant NAS inspection guidance. If a required checkout is missing, report it instead of guessing another repository. Use repository-relative paths after resolving the roots. All relative links below are relative to the **resolved source** SKILL.md.

An add-route invocation authorizes the route/backend repository changes, validation, commit and push to GitHub, and read-only deployment checks. It does not authorize direct `kubectl apply`, live patches, container deployment or Synology reverse proxy changes. Creating this skill alone authorizes none of those actions. Honor a request for plan/repository-only work by omitting commit/push and deployment. No extra permission question is needed for commit/push when the user requested this add-route workflow.

## Establish the endpoint and conventions

Inspect Git status, relevant diffs, branch/upstream and remotes. Preserve unrelated local changes and commits. Verify the GitOps source's tracked branch from `kubernetes/apps/flux-system/flux-instance/app/helmrelease.yaml`; it currently tracks `refs/heads/main` at `dkw99/home-ops`. A push to an unrelated branch is not deployment. Do not force-push or include unrelated work merely to reach the tracked branch.

Begin cluster access with the checks required by AGENTS.md, from the repository root:

```sh
kubectl --kubeconfig ./kubeconfig --context k8s-cluster --request-timeout=10s get nodes -o wide
kubectl --kubeconfig ./kubeconfig --context k8s-cluster --request-timeout=10s get namespaces
```

Keep these config/context flags explicit for subsequent reads. If access fails, distinguish configuration, authentication and network failures. Continue independent repository preparation; report any unavailable live preflight before deployment and do not assume absence of conflicts.

Inspect only the selected container's running state, network mode and published TCP bindings over noninteractive SSH to `sysdkwise@192.168.2.30`. Docker is `/usr/local/bin/docker`. Use formatted inspection, not full container environments. Verify the NAS address and **published host HTTP port**, not merely the container's internal port. Multiple endpoints or shared namespaces need application-specific evidence or clarification; do not attribute every Gluetun publication to qBittorrent. Verify reachability from the gateway network where permitted diagnostics are available. A loopback-only NAS publication is unsuitable for a direct Kubernetes backend.

Read these repository examples and their Kustomize/Flux parents before choosing the smallest compatible change:

- [Maintainerr's per-app layout](../../../kubernetes/apps/network/media-pvr-ext/app/maintainerr/kustomization.yaml): its sibling `ingress.yaml`, `service.yaml`, and `endpointslice.yaml` are the template for new NAS application routes. Read the [parent resource includes](../../../kubernetes/apps/network/media-pvr-ext/app/kustomization.yaml) and [Flux Kustomization](../../../kubernetes/apps/network/media-pvr-ext/ks.yaml). The application routes use this per-app layout; preserve unrelated app backends when adding a route.
- [NAS management route](../../../kubernetes/apps/network/nas/app/ingress.yaml) and its `service.yaml` for the existing HTTPS-backend case.
- [Gateway listeners and TLS](../../../kubernetes/apps/network/envoy-gateway/app/envoy.yaml).
- [Network DNS conventions](../../../kubernetes/apps/network/README.md) and the external-dns HelmRelease files it identifies.
- [Network resource includes](../../../kubernetes/apps/network/kustomization.yaml) and the chosen app's `ks.yaml` for namespace, source reference and substitution behavior.

Existing application routes use `network/envoy-internal`, `sectionName: https`, and `${SECRET_DOMAIN}`. Confirm current live listeners, certificate coverage and existing routes for the requested hostname; preserve TLS and access policies. Use `${SECRET_DOMAIN}` in manifests as established, with the user-facing hostname under `wisesalmon.net`. Do not print cluster secrets, kubeconfig, TSIG keys or private certificate data.

External-dns manages gateway HTTPRoute DNS. The internal gateway advertises `internal.${SECRET_DOMAIN}` as its DNS target. Verify current controller ownership, domain filters and DNS records rather than writing a manual NAS-target CNAME. The configured DNS server address can differ from the application NAS address; do not interchange them.

## Prepare and validate repository changes

New NAS application routes use a dedicated Service and EndpointSlice per app, following Maintainerr. Place these four files under `kubernetes/apps/network/media-pvr-ext/app/<app>/`:

- `ingress.yaml`: a `gateway.networking.k8s.io/v1` HTTPRoute named `<app>`, with the selected hostname, established internal HTTPS parent, and `backendRefs` pointing to Service `<app>` at the verified published host port.
- `service.yaml`: a selectorless ClusterIP Service named `<app>`, with a named `http` TCP port. Follow Maintainerr by using the verified published host port for both `port` and `targetPort`.
- `endpointslice.yaml`: a `discovery.k8s.io/v1` EndpointSlice named `<app>`, with `kubernetes.io/service-name: <app>` and `endpointslice.kubernetes.io/managed-by: home-ops` labels, `addressType: IPv4`, the verified NAS IP, endpoint `conditions.ready: true`, and a matching named `http` TCP port at the published host port.
- `kustomization.yaml`: include `./ingress.yaml`, `./service.yaml`, and `./endpointslice.yaml`.

Include `./<app>` in `kubernetes/apps/network/media-pvr-ext/app/kustomization.yaml`. Use the existing `media-pvr-ext/ks.yaml` Flux include and namespace/substitution configuration; a new app does not need a separate Flux Kustomization. Reuse an existing correctly mapped per-app backend when present. Do not add new app ports to the shared `media-pvr-ext` Service or legacy `endpoints.yaml`, or migrate existing shared routes as part of an addition. The `nas` ExternalName/HTTPS management route is a reference for that special case, not the template for NAS application routes.

Inspect existing repository and live entries first. Matching resources require no duplicate commit. Conflicting hostnames, backend mappings, listener policies or DNS ownership require resolution before publishing; preserve unrelated resources. Keep the separate Synology `home.lan`/other-zone endpoint unchanged. This skill does not need `synology-app-manage` to create a reverse proxy rule: Kubernetes reaches the verified NAS published port directly.

Validate the affected Kustomize build and route/backend linkage. Follow [.github/workflows/flux-local.yaml](../../../.github/workflows/flux-local.yaml) for the current Flux-local test invocation and version when applicable. Account for Flux substitutions without dumping decrypted inputs or secrets. Check hostname uniqueness, namespace, parent listener, the HTTPRoute reference to the per-app Service, matching named ports in the Service and EndpointSlice, the EndpointSlice service-name label and NAS address, and both app and parent resource inclusion. Finish with `git diff --check` and review the complete intended diff. Do not claim full validation if a required tool or live check is unavailable; resolve or report the limitation before publishing a potentially conflicting route.

Identify rollback as reverting the route-addition commit through the same GitOps branch, preserving later/unrelated changes. Include any external DNS ownership/reconciliation implications in recovery notes; do not delete records by hand to force reconciliation.

## Commit, push and verify

Stage only this route's intended files and supporting includes. Commit with a concrete message naming the application and HTTPS endpoint, then push to the verified GitOps branch on GitHub. Check which commits the push will publish so unrelated local commits are not included accidentally. If repository branch protection requires a PR, follow it and report that deployment remains pending until merge; do not bypass protection or call a branch push reconciled deployment.

After a successful push, use read-only checks to verify:

- Flux source/applied revision includes the pushed commit, and the affected Kustomization is Ready. Derive its live namespace from the parent manifests/live resources; the network include can override a child manifest's namespace.
- HTTPRoute conditions `Accepted` and `ResolvedRefs` are true for the intended gateway and current generation, and the gateway/listener is programmed.
- Per-app Service and EndpointSlice state reflects the verified NAS address and application port.
- DNS for `{container}.wisesalmon.net` resolves through the intended gateway, not the NAS application IP. Inspect both DNS controllers' relevant results if they manage distinct views.
- HTTPS access uses the hostname for Host/SNI and validates the certificate. Do not disable certificate verification or modify certificate resources to hide a failure. Authentication responses can demonstrate route access without proving an application login workflow.

Allow normal Flux/DNS reconciliation time; use bounded polling and give status updates. Do not issue direct apply/patch/reconcile commands, repeated Git commits, or policy changes as a workaround for a failure. If a push or check fails, stop publishing retries, inspect the current remote/live revision, and distinguish committed, pushed, reconciled and verified states. Do not automatically roll back a successful push without authorization for that recovery action.

Report the hostname/HTTPS URL, NAS IP and published port, resource paths, commit and pushed branch, validation results, reconciliation/route/DNS/TLS status and rollback commit. State any pending merge, reconciliation or unavailable checks explicitly.
