#!/usr/bin/env bash

namespaces=$(kubectl get --no-headers ns -A | awk '{print $1","$2}')
for item in $namespaces
do

    status="$(echo "${item}" | awk -F',' '{print $2}')"
    if [ "$status" == "Terminating" ]; then
        namespace="$(echo "${item}" | awk -F',' '{print $1}')"
        echo "patch ns/$namespace"
        kubectl patch ns/$namespace --type json --patch='[ { "op": "remove", "path": "/metadata/finalizers" } ]'
        kubectl get ns $namespace
    fi

done

# kubectl patch ns/test-finalizers --type json --patch='[ { "op": "remove", "path": "/metadata/finalizers" } ]'
