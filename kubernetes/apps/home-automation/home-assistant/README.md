# Home Assistant Cluster Backups

This directory contains the Kubernetes resources for Home Assistant. The backup CronJob here is cluster-only GitOps configuration and is separate from Home Assistant UI-managed backup settings.

## Backup Layout

- `/config`: Home Assistant config PVC, mounted from `home-assistant-config`.
- `/backup`: Synology NFS backup share, mounted from `192.168.16.30:/volume1/k3sCluster/Apps/External/Backups/home_assistant`.
- `/config/backups`: local directory only. Do not mount the Synology backup share under `/config`.

Keeping the backup destination outside `/config` prevents recursive backups where a config backup includes previous backup archives.

## Config Snapshot CronJob

Manifest:

```text
app/config-snapshot-cronjob.yaml
```

Resource:

```text
CronJob/home-assistant-config-snapshot
```

Schedule:

```text
15 2 * * * Australia/Sydney
```

Destination:

```text
/backup/config-snapshots/home-assistant-config-dashboard-YYYYMMDDTHHMMSSZ.tar.gz
```

Retention:

```text
30 days
```

The snapshot is intentionally small and only captures cluster-relevant Home Assistant configuration that changes frequently.

Included:

- `/config/configuration.yaml`
- `/config/automations.yaml`
- `/config/scripts.yaml`
- `/config/scenes.yaml`
- `/config/packages/**`
- `/config/.storage/lovelace*`, excluding generated `*bak*` files
- `/config/.storage/lovelace_dashboards`
- `/config/.storage/lovelace_resources`
- `/config/.storage/input_boolean`
- `/config/.storage/input_datetime`
- `/config/.storage/input_select`

Excluded:

- `/config/secrets.yaml`
- `/config/.storage/auth*`
- `/config/.storage/core.config_entries`
- `/config/.storage/core.device_registry`
- `/config/.storage/core.entity_registry`
- `/config/.storage/backup`
- `/config/home-assistant_v2.db*`
- `/config/backups/**`
- `/config/.vscode/**`
- `/config/.cache/**`
- `/config/.venv/**`
- logs and generated backup files

## Manual Test

Run a one-off snapshot job:

```bash
kubectl --kubeconfig /home/dkwise/home-lab/repos/dkw99/home-ops/kubeconfig \
  -n home-automation create job \
  --from=cronjob/home-assistant-config-snapshot \
  home-assistant-config-snapshot-manual-$(date +%s)
```

Check completion:

```bash
kubectl --kubeconfig /home/dkwise/home-lab/repos/dkw99/home-ops/kubeconfig \
  -n home-automation get jobs,pods | grep home-assistant-config-snapshot
```

Inspect the latest archive:

```bash
kubectl --kubeconfig /home/dkwise/home-lab/repos/dkw99/home-ops/kubeconfig \
  -n home-automation exec deploy/home-assistant -- \
  sh -c 'latest=$(ls -t /backup/config-snapshots/home-assistant-config-dashboard-*.tar.gz | head -1); tar -tzf "$latest"'
```

Delete manual test jobs after verification:

```bash
kubectl --kubeconfig /home/dkwise/home-lab/repos/dkw99/home-ops/kubeconfig \
  -n home-automation delete job <job-name>
```

## Home Assistant UI Backups

Home Assistant UI-managed backups are configured inside Home Assistant through the backup websocket/UI settings. They are not defined by this CronJob.

Current intended split:

- Daily Kubernetes CronJob: lightweight config/dashboard snapshots to `/backup/config-snapshots`.
- Weekly Home Assistant automatic backup: larger restore backup to the Synology backup agent.

Do not store large UI backup archives inside `/config`.
