# Daily Kubernetes health check

Schedule: daily at 08:00, timezone `Australia/Sydney` (including daylight saving).
Project: `/home/dkwise/home-lab/repos/dkw99/home-ops`, local project mode.
Status: installed on dev-server using a systemd user timer and Codex CLI.

## Installed CLI job

Implementation: `operations/kubernetes-health/`. A fixed collector runs read-only
kubectl queries and HTTPS GET checks. Codex summarizes the captured snapshot in
a read-only sandbox with user config disabled, without cluster tools or automatic
remediation. The collector does not fetch Secrets, workload specs or application
logs. It does not measure disk free space or separately test public ingress.

The timer uses `Australia/Sydney` explicitly and catches up once after downtime.
User lingering is enabled so the timer can run without an interactive login.
Reports, snapshots and private execution logs are stored under
`~/.local/state/kubernetes-health/` with restrictive permissions. `latest.md`
points to the latest successful report; failed executions leave the previous
report intact. The service fails if Codex fails; inspect its journal and per-run
log. No external notification delivery is configured. Reports are retained
until manually removed. Codex uses the existing CLI sign-in and usage allowance.

Operations:

```bash
systemctl --user list-timers kubernetes-health.timer
systemctl --user start kubernetes-health.service
journalctl --user -u kubernetes-health.service -n 30
cat ~/.local/state/kubernetes-health/latest.md
systemctl --user disable --now kubernetes-health.timer
```

After editing tracked unit templates, copy them to `~/.config/systemd/user/`,
run `systemctl --user daemon-reload`, then restart the timer. Disabling the
timer does not stop an already running check; stop the service separately if
needed. Lingering can be disabled with `sudo loginctl disable-linger dkwise`
only if no other user services depend on it.

## Scheduled task prompt

Perform a read-only health check of the home Kubernetes cluster. Read the
project AGENTS.md first. Work from the home-ops repository root and always use
`kubectl --kubeconfig ./kubeconfig --context k8s-cluster --request-timeout=10s`.
Never print credentials, read Secret contents, change the cluster, restart
workloads, reconcile Flux, or edit repository files during this check.

1. Check nodes and namespaces first. If access fails, distinguish missing
   local configuration, network reachability and authentication errors. Report
   the failure without changing endpoints, TLS verification or credentials.
2. Check node readiness and pressure conditions; deployment, StatefulSet and
   DaemonSet availability; pending, failed, crash-looping or unready pods; and
   recent container termination reasons and restart timestamps. Distinguish
   old cumulative restart counts from recent failures and successful completed
   Jobs from unhealthy workloads.
3. Check Flux Kustomization, HelmRelease and source readiness. Explain suspended
   resources separately from failed resources.
4. Check PVC binding, volume-related warning events and available node/pod
   resource metrics. If metrics or storage capacity telemetry is unavailable,
   report that limitation rather than claiming storage or resource health.
5. Review recent warning events, with timestamps and recurrence counts. Inspect
   only bounded relevant logs when needed to explain a current failure; redact
   private data and credentials from the report.
6. Check Home Assistant workload/service and HTTPRoute readiness. Use GET for
   `https://hass.wisesalmon.net/` and `/auth/providers`, validating TLS. Distinguish
   internal DNS access from public ingress where possible. Check WebSocket
   upgrade if browser connectivity is suspect. Do not treat HEAD returning 405
   as an outage or claim that HTTP 200 proves a successful browser login.
7. Return a concise report dated in Australia/Sydney: overall healthy, degraded,
   or unable to assess; current findings in severity order; affected resources;
   evidence; and recommended next actions. Include successful checks briefly.
   If a previous report is available, identify new, ongoing and resolved issues;
   otherwise state that this run establishes the baseline.

## Alternative desktop activation

Create a standalone task in Scheduled using the prompt above, select the local
home-ops project and set daily 08:00 in Australia/Sydney. Run it once manually
and review the result. The execution computer needs the repository, kubeconfig,
kubectl and cluster LAN/VPN access. Local desktop scheduling requires the
computer on and the app running. Avoid enabling both this alternative and the
installed systemd timer unless duplicate reports are intended.

Reference: https://learn.chatgpt.com/docs/automations
