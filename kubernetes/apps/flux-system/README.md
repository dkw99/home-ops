# Flux System

This directory contains the Flux installation and the GitHub webhook receiver used to reconcile this repository.

## Layout

Active Flux webhook files:

```text
flux-instance/app/receiver.yaml
flux-instance/app/httproute.yaml
flux-instance/app/secret.sops.yaml
```

The old standalone `webhooks/` tree was removed. The active webhook is managed by the Flux instance manifests.

## GitHub Webhook URL

Flux generates the `/hook/...` path from the live `Receiver` and its token secret. The path is stored in cluster status, not hardcoded in Git.

Print the full GitHub webhook payload URL:

```bash
kubectl --kubeconfig /home/dkwise/home-lab/repos/dkw99/home-ops/kubeconfig \
  -n flux-system get receiver github-webhook \
  -o jsonpath='https://flux-webhook.wisesalmon.net{.status.webhookPath}{"\n"}'
```

Print only the generated path:

```bash
kubectl --kubeconfig /home/dkwise/home-lab/repos/dkw99/home-ops/kubeconfig \
  -n flux-system get receiver github-webhook \
  -o jsonpath='{.status.webhookPath}{"\n"}'
```

## GitHub Webhook Secret

The webhook token is stored in:

```text
flux-instance/app/secret.sops.yaml
```

To read the live token when updating GitHub:

```bash
kubectl --kubeconfig /home/dkwise/home-lab/repos/dkw99/home-ops/kubeconfig \
  -n flux-system get secret github-webhook-token-secret \
  -o jsonpath='{.data.token}' | base64 -d
```

Do not commit decrypted secret files.

## GitHub Settings

In the GitHub repository webhook settings:

```text
Payload URL:   output from the Receiver command
Content type:  application/json
Secret:        github-webhook-token-secret token value
Events:        push
Active:        enabled
```

Check the configured GitHub webhook:

```bash
gh api repos/dkw99/home-ops/hooks \
  --jq '.[] | {id, url: .config.url, events, last_response}'
```

## Troubleshooting

Check the live Flux receiver:

```bash
kubectl --kubeconfig /home/dkwise/home-lab/repos/dkw99/home-ops/kubeconfig \
  -n flux-system get receiver github-webhook -o wide
```

Check the HTTPRoute:

```bash
kubectl --kubeconfig /home/dkwise/home-lab/repos/dkw99/home-ops/kubeconfig \
  -n flux-system describe httproute github-webhook
```

Check notification-controller logs:

```bash
kubectl --kubeconfig /home/dkwise/home-lab/repos/dkw99/home-ops/kubeconfig \
  -n flux-system logs deploy/notification-controller --since=30m
```

Common failure modes:

```text
404 from GitHub
  GitHub is using an old /hook/... path. Update the GitHub webhook URL from Receiver status.

Invalid signature
  GitHub webhook secret does not match github-webhook-token-secret.

Route accepted but GitHub cannot connect
  Check public DNS, Cloudflare Tunnel, and envoy-external.

Webhook fires but app changes do not apply
  Confirm the Receiver resources include the GitRepository/Kustomizations that should reconcile.
```

The current receiver should log a successful ping like:

```text
handling GitHub event: ping
resource 'GitRepository/flux-system.flux-system' annotated
resource 'Kustomization/flux-system.flux-system' annotated
```
