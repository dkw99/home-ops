#!/usr/bin/env bash
export PROJECT_DIR=$(git rev-parse --show-toplevel)
KUBECONFIG=${PROJECT_DIR}/provision/kubeconfig

volumesnapshotcontents=$(kubectl --kubeconfig $KUBECONFIG get --no-headers volumesnapshotcontents | awk '{print $1}')
for volumesnapshotcontent in $volumesnapshotcontents
do
    kubectl delete volumesnapshotcontents "${volumesnapshotcontent}"
done

volumesnapshots=$(kubectl --kubeconfig $KUBECONFIG get --no-headers volumesnapshots -A | awk '{print $1","$2}')
for item in $volumesnapshots
do
    namespace="$(echo "${item}" | awk -F',' '{print $1}')"
    volumesnapshot="$(echo "${item}" | awk -F',' '{print $2}')"
    kubectl delete volumesnapshots "${volumesnapshot}" -n "${namespace}"
done
for item in $volumesnapshots
do
    namespace="$(echo "${item}" | awk -F',' '{print $1}')"
    volumesnapshot="$(echo "${item}" | awk -F',' '{print $2}')"
    kubectl delete volumesnapshots "${volumesnapshot}" -n "${namespace}"
done
