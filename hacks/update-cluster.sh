#!/usr/bin/env bash
set -o errexit
set -o pipefail
export PROJECT_DIR=$(git rev-parse --show-toplevel)
cd $PROJECT_DIR

flux --kubeconfig=./provision/kubeconfig reconcile source git flux-system
