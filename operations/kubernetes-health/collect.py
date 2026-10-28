#!/usr/bin/env python3
"""Collect bounded status output without fetching Secrets or workload specs."""
import datetime
import subprocess
from zoneinfo import ZoneInfo

BASE = ['kubectl', '--kubeconfig', './kubeconfig', '--context', 'k8s-cluster',
        '--request-timeout=10s']


def run(label, args):
    print('\n## ' + label, flush=True)
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=35)
        print('exit=' + str(result.returncode))
        print((result.stdout + result.stderr)[:60000])
        return result.returncode
    except subprocess.TimeoutExpired:
        print('Timed out after 35 seconds; check not assessed.')
        return 124


print('Snapshot: ' + datetime.datetime.now(ZoneInfo('Australia/Sydney')).isoformat())
if run('Nodes', BASE + ['get', 'nodes', '-o', 'wide']) == 0:
    checks = [
        ('Namespaces', ['get', 'namespaces']),
        ('Node conditions', ['get', 'nodes', '-o', 'custom-columns=NAME:.metadata.name,CONDITIONS:.status.conditions']),
        ('Pods', ['get', 'pods', '-A', '-o', 'wide']),
        ('Container status', ['get', 'pods', '-A', '-o', 'custom-columns=NAMESPACE:.metadata.namespace,NAME:.metadata.name,CONTAINERS:.status.containerStatuses']),
        ('Workloads', ['get', 'deployments,statefulsets,daemonsets', '-A']),
        ('Jobs', ['get', 'jobs', '-A']),
        ('Flux', ['get', 'kustomizations,helmreleases,gitrepositories,ocirepositories,helmrepositories', '-A']),
        ('Flux conditions', ['get', 'kustomizations,helmreleases', '-A', '-o', 'custom-columns=NAMESPACE:.metadata.namespace,NAME:.metadata.name,SUSPENDED:.spec.suspend,CONDITIONS:.status.conditions']),
        ('PVCs', ['get', 'pvc', '-A']),
        ('Warning events (retained by API; inspect timestamps)', ['get', 'events', '-A', '--field-selector=type=Warning', '--sort-by=.lastTimestamp']),
        ('Node metrics', ['top', 'nodes']),
        ('Pod metrics', ['top', 'pods', '-A']),
        ('Home Assistant service', ['get', 'svc', 'home-assistant', '-n', 'home-automation']),
        ('Home Assistant route', ['get', 'httproute', 'home-assistant', '-n', 'home-automation', '-o', 'custom-columns=NAME:.metadata.name,HOSTS:.spec.hostnames,PARENTS:.status.parents']),
    ]
    for label, args in checks:
        run(label, BASE + args)
else:
    print('Cluster status unavailable; not attempting further cluster queries.')

for path in ['/', '/auth/providers']:
    run('Home Assistant GET ' + path, ['curl', '--silent', '--show-error',
        '--max-time', '15', '--output', '/dev/null', '--write-out',
        'HTTP %{http_code}; remote %{remote_ip}; TLS verify %{ssl_verify_result}\n',
        'https://hass.wisesalmon.net' + path])
print('Coverage limits: no disk-free telemetry, browser login or public-ingress isolation; '
      'no application logs collected. API warning events may include older retained events.')
