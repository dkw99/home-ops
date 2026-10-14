# NAS step-ca endpoint

`step-ca.wisesalmon.net` uses the internal gateway and its existing Let's Encrypt
frontend certificate. The dedicated backend is NAS `192.168.2.30:9000`, verified
from the deployed container's published port. BackendTLSPolicy verifies the CA's
private TLS chain using the public root ConfigMap and matching SNI.

External-dns manages both internal DNS views through established controllers;
no manually owned NAS CNAME or Synology reverse proxy is required. The CA's
issuance policy allows home.lan names only; this endpoint does not change how
wisesalmon.net certificates are issued.

NAS deployment, root fingerprint, trust distribution, backups and recovery are
documented in sibling synology's `docs/step-ca.md`. Root private keys and NAS
passwords are never stored in this repository.

Before rollout no route, backend or DNS record existed for this hostname.
Rollback by reverting the addition commit through the tracked main GitOps branch;
external-dns removes its owned records on reconciliation. Stop the NAS Compose
project separately if retiring the CA, preserving all signing keys and state.
