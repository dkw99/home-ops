# Just Commands Cheatsheet

Run these commands from the repository root unless noted otherwise.

## Safety Notes

Commands that change running Talos nodes can interrupt the whole cluster. This is a single-node control-plane/worker cluster, so a reboot, reset, or bad config apply makes Kubernetes and workloads unavailable until the node recovers.

Commands marked **disruptive** may restart or temporarily break cluster services.

Commands marked **destructive** can wipe node state or reset the cluster and should not be run against healthy production nodes unless that is the explicit goal.

## List Commands

List available top-level command groups:

```bash
just -l
```

List commands in a module:

```bash
just talos
just kube
just bootstrap
```

If you are already inside a module directory, such as `talos/`, run:

```bash
just -l
```

## Sync GitOps Changes

Force Flux to pull changes from Git:

```bash
just kube reconcile
```

## Check Kubernetes State

Check Kubernetes nodes:

```bash
kubectl get nodes -o wide
```

Check pods across namespaces:

```bash
kubectl get pods -A
```

Check Flux Kustomizations and HelmReleases:

```bash
kubectl get kustomizations,helmreleases -A
```

## Check Talos Node State

Use these commands when you need to inspect the running Talos node without changing it.

Check Talos node health:

```bash
talosctl --endpoints 192.168.16.100 \
  --nodes 192.168.16.100 \
  health
```

Check node network links:

```bash
talosctl --endpoints 192.168.16.100 \
  --nodes 192.168.16.100 \
  get links
```

Check node addresses:

```bash
talosctl --endpoints 192.168.16.100 \
  --nodes 192.168.16.100 \
  get addresses
```

## Generate Talos Config

Use this after editing files under `talos/`, such as `talconfig.yaml`, `talenv.yaml`, or patch files. This only regenerates local `talos/clusterconfig/` files; it does not apply changes to the node.

Generate Talos config from `talos/talconfig.yaml`, `talos/talenv.yaml`, `talos/talsecret.sops.yaml`, and `talos/patches/`:

```bash
just talos generate-config
```

Equivalent from inside `talos/`:

```bash
just generate-config
```

## Change Talos Node Config

Use this workflow when changing node configuration, such as network interfaces, kubelet settings, files, sysctls, time settings, or Talos/Kubernetes versions.

1. Edit source files under `talos/`, usually `talos/talconfig.yaml` or files under `talos/patches/`.

2. Regenerate the rendered machine config:

```bash
just talos generate-config
```

3. Review what changed:

```bash
git diff -- talos/talconfig.yaml talos/patches talos/clusterconfig
```

4. Apply the generated config with the least disruptive mode that fits the change:

```bash
just talos apply-node 192.168.16.100 no-reboot
```

Use `no-reboot` for changes Talos can apply live. If Talos says the change requires a reboot, use `staged` to queue it for the next reboot:

```bash
just talos apply-node 192.168.16.100 staged
```

Use `reboot` only when you deliberately want Talos to apply the config and reboot immediately:

```bash
just talos apply-node 192.168.16.100 reboot
```

5. Verify the node after apply or reboot:

```bash
talosctl --endpoints 192.168.16.100 \
  --nodes 192.168.16.100 \
  health

kubectl get nodes -o wide
kubectl get pods -A
```

On this single-node cluster, `staged`, `reboot`, upgrades, and manual reboot can take Kubernetes and workloads offline until the node returns.

## Apply Or Restart Talos

Use these commands only when you need the running Talos node to consume generated config, upgrade software, or reboot. On this single-node cluster, these actions can interrupt Kubernetes and workloads.

Apply Talos config to a node:

```bash
just talos apply-node 192.168.16.100 staged
```

**Disruptive:** applying Talos config can reboot the node or stage changes that take effect on next reboot. Always review the dry-run output or generated diff before applying to a running node.

Common apply modes:

```text
auto      Let Talos choose the apply behavior
staged    Stage config and apply after the next reboot
reboot    Apply config and reboot as part of the operation
try       Apply with rollback timeout
no-reboot Apply only changes that do not require reboot
```

Upgrade Kubernetes to the version in `talos/talenv.yaml`:

```bash
just talos upgrade-k8s
```

**Disruptive:** Kubernetes control-plane components and node workloads can restart during the upgrade.

Upgrade Talos on one node:

```bash
just talos upgrade-node 192.168.16.100
```

**Disruptive:** Talos upgrades reboot the node. On this single-node cluster, Kubernetes and workloads will be unavailable during the reboot.

Reboot the Talos node:

```bash
talosctl --endpoints 192.168.16.100 \
  --nodes 192.168.16.100 \
  reboot
```

**Disruptive:** this reboots the only control-plane/worker node, so Kubernetes and workloads will go offline until it returns.

## Build Or Destroy Cluster

Bootstrap applications into a Talos cluster:

```bash
just bootstrap apps
```

Use this during initial cluster bring-up after Talos and Kubernetes are ready. Do not use it for normal day-to-day reconciliation.

Bootstrap a new Talos cluster:

```bash
just bootstrap talos
```

**Destructive on existing nodes:** this path generates/applies bootstrap Talos config and is intended for initial cluster creation, not for routine changes to an already-running cluster.

Reset Talos nodes:

```bash
just talos reset-node 192.168.16.100
just talos reset
```

**Destructive:** `reset-node` resets one node to maintenance mode. `reset` resets all nodes. Both wipe Talos state and ephemeral data labels and should only be used intentionally. Do not run these against a running cluster unless you are intentionally destroying/rebuilding it.
