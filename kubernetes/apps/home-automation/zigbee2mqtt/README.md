# Zigbee2MQTT recovery

The app container has startup, readiness, and liveness probes against port 9001
at `/healthz`. The repository-managed `adapter-health.cjs` external extension
starts this endpoint after coordinator initialization and returns HTTP 503 after
the `adapterDisconnected` event. Stopping the extension closes the endpoint.
This covers the observed Ember fatal-disconnect failure where the process stayed
alive and MQTT incorrectly returned to online. A stalled event loop also causes
probe timeouts. This does not detect every possible silent radio failure.

The MQTT `bridge/request/health_check` implementation in 2.14.2 returns a constant
`healthy: true`, so it is unsuitable for detecting this failure. Network parameters
are cached too. The probe does not open a second serial connection or depend on
individual device traffic, MQTT availability, or a separate Kubernetes controller.

Startup allows 18 failures at 10-second intervals (about three minutes). After
startup, liveness checks run every 60 seconds and restart only the app container
after three consecutive failures. Readiness checks run every 10 seconds with two
failures removing the pod from service. The existing built-in watchdog stays
enabled and can recover before Kubernetes intervenes. Pairings and configuration
remain on the existing PVC. Persistent coordinator failures can cause repeated
restarts with Kubernetes backoff; there is no hourly restart cap.

The ConfigMap is mounted as one read-only file inside `external_extensions`;
other extensions remain on the PVC. Reloader watches the ConfigMap for changes.
External JavaScript must remain enabled for the extension to load. Revalidate
the extension's event API when upgrading Zigbee2MQTT.

Validation:

```sh
node --test tests/zigbee2mqtt-health.test.cjs
kubectl --kubeconfig ./kubeconfig --context k8s-cluster -n home-automation rollout status deployment/zigbee2mqtt --timeout=180s
kubectl --kubeconfig ./kubeconfig --context k8s-cluster -n home-automation logs deployment/zigbee2mqtt -c app --tail=20
```

The test simulates adapter disconnection without interrupting the live radio.
There is no Prometheus/Alertmanager installation in this cluster as of 2026-11-06.
Repeated-restart notifications need a separate notification destination; probe
failures and restarts are recorded in Kubernetes events and container status.

Rollback: revert the commit adding recovery, push it, and reconcile the Flux
`zigbee2mqtt` Kustomization. This removes the probes, extension mount, and ConfigMap
and rolls the deployment back to its previous behavior without modifying the PVC.
