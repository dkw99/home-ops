# Just Commands Cheatsheet

Run these commands from the repository root unless noted otherwise.

## Safety Notes

Commands that change running Talos nodes can interrupt the whole cluster. This is a single-node control-plane/worker cluster, so a reboot, reset, or bad config apply makes Kubernetes and workloads unavailable until the node recovers.

Commands marked **disruptive** may restart or temporarily break cluster services.

Commands marked **destructive** can wipe node state or reset the cluster and should not be run against healthy production nodes unless that is the explicit goal.

List available commands:

```bash
just -l
just talos -l
just kube -l
just bootstrap -l
```

## Talos

Generate Talos config from `talos/talconfig.yaml`, `talos/talenv.yaml`, `talos/talsecret.sops.yaml`, and `talos/patches/`:

```bash
just talos generate-config
```

## Kubernetes

Force Flux to pull changes from Git:

```bash
just kube reconcile
```

## Bootstrap

Bootstrap applications into a Talos cluster:

```bash
just bootstrap apps
```

This is for initial app bring-up. Do not use it for normal day-to-day reconciliation.

## Direct Useful Commands

Check Talos node health:

```bash
talosctl --talosconfig /home/dkwise/home-lab/repos/dkw99/home-ops/talos/clusterconfig/talosconfig \
  --endpoints 192.168.16.100 \
  --nodes 192.168.16.100 \
  health
```

Check node network links:

```bash
talosctl --talosconfig /home/dkwise/home-lab/repos/dkw99/home-ops/talos/clusterconfig/talosconfig \
  --endpoints 192.168.16.100 \
  --nodes 192.168.16.100 \
  get links
```

Check Kubernetes nodes:

```bash
kubectl --kubeconfig /home/dkwise/home-lab/repos/dkw99/home-ops/kubeconfig get nodes -o wide
```

## Infrequent And Disruptive Commands

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
talosctl --talosconfig /home/dkwise/home-lab/repos/dkw99/home-ops/talos/clusterconfig/talosconfig \
  --endpoints 192.168.16.100 \
  --nodes 192.168.16.100 \
  reboot
```

**Disruptive:** this reboots the only control-plane/worker node, so Kubernetes and workloads will go offline until it returns.

## Destructive Commands

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
