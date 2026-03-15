#!/bin/bash
set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== Setting up test environment ==="

# 0. Delete existing cluster if it exists
echo "Cleaning up any existing test cluster..."
kind delete cluster --name osac-test 2>/dev/null || true

# 0.5. Install required Python libraries
echo "Installing required Python libraries..."
pip install --user kubernetes openstacksdk 2>/dev/null || pip3 install --user kubernetes openstacksdk

# 1. Create kind cluster
echo "Creating kind cluster..."
kind create cluster --name osac-test --wait 5m

# 1.5. Export kubeconfig to dedicated file
echo "Exporting kubeconfig to dedicated file..."
kind export kubeconfig --name osac-test --kubeconfig "${SCRIPT_DIR}/kubeconfig-osac-test"
echo "Kubeconfig exported to: ${SCRIPT_DIR}/kubeconfig-osac-test"

# 2. Clone osac-operator for CRDs
echo "Cloning osac-operator for CRDs..."
if [ -d "/tmp/osac-operator" ]; then
  rm -rf /tmp/osac-operator
fi
git clone https://github.com/osac-project/osac-operator.git /tmp/osac-operator

# 3. Install OSAC CRDs
echo "Installing OSAC CRDs..."
kubectl apply -f /tmp/osac-operator/config/crd/bases/

# 3.5. Install external CRDs needed by workflows
echo "Installing KubeVirt operator..."
kubectl apply -f https://github.com/kubevirt/kubevirt/releases/download/v1.1.0/kubevirt-operator.yaml

echo "Waiting for KubeVirt operator to be ready..."
kubectl wait --for=condition=Available --timeout=120s -n kubevirt deployment/virt-operator || echo "KubeVirt operator not ready yet"

echo "Installing KubeVirt CR to trigger CRD creation..."
kubectl apply -f https://github.com/kubevirt/kubevirt/releases/download/v1.1.0/kubevirt-cr.yaml

echo "Waiting for VirtualMachine CRD to be created..."
timeout 60 bash -c 'until kubectl get crd virtualmachines.kubevirt.io 2>/dev/null; do echo "Waiting for VirtualMachine CRD..."; sleep 2; done' || echo "Timeout waiting for VirtualMachine CRD"

echo "Installing CDI operator for DataVolume support..."
kubectl apply -f https://github.com/kubevirt/containerized-data-importer/releases/download/v1.58.0/cdi-operator.yaml

echo "Waiting for CDI operator to be ready..."
kubectl wait --for=condition=Available --timeout=120s -n cdi deployment/cdi-operator || echo "CDI operator not ready yet"

echo "Installing CDI CR to trigger DataVolume CRD creation..."
kubectl apply -f https://github.com/kubevirt/containerized-data-importer/releases/download/v1.58.0/cdi-cr.yaml

echo "Waiting for DataVolume CRD to be created..."
timeout 60 bash -c 'until kubectl get crd datavolumes.cdi.kubevirt.io 2>/dev/null; do echo "Waiting for DataVolume CRD..."; sleep 2; done' || echo "Timeout waiting for DataVolume CRD"

# 3.6. Scale down all deployments (keep CRs and CRDs)
echo "Scaling down all KubeVirt and CDI deployments to save resources..."
kubectl scale deployment -n kubevirt --all --replicas=0 || echo "Could not scale kubevirt deployments"
kubectl scale deployment -n cdi --all --replicas=0 || echo "Could not scale cdi deployments"

echo "Waiting for pods to terminate..."
kubectl wait --for=delete pod --all -n kubevirt --timeout=60s 2>/dev/null || echo "Some kubevirt pods still terminating"
kubectl wait --for=delete pod --all -n cdi --timeout=60s 2>/dev/null || echo "Some cdi pods still terminating"

echo "KubeVirt and CDI deployments scaled down. CRs and CRDs remain available for testing."

echo "Installing OLM CRDs..."
kubectl apply -f https://github.com/operator-framework/operator-lifecycle-manager/releases/download/v0.25.0/crds.yaml 2>/dev/null || echo "OLM CRDs may already exist or URL changed"

echo "Installing RHACM CRDs (ManagedCluster)..."
kubectl apply -f https://raw.githubusercontent.com/stolostron/managedcluster-import-controller/main/deploy/crds/cluster.open-cluster-management.io_managedclusters.yaml 2>/dev/null || echo "RHACM CRDs may already exist or URL changed"

# 4. Create test namespaces
echo "Creating test namespaces..."
kubectl create namespace osac-system || true
kubectl create namespace osac-workflows-test || true
kubectl create namespace cluster-test-cluster-work || true
kubectl create namespace computeinstance-test-vm-work || true
kubectl create namespace hostpool-test-hostpool-work || true

# 5. Apply test fixtures
echo "Applying test fixtures..."
kubectl apply -f "${SCRIPT_DIR}/fixtures/"

echo "=== Test environment ready ==="
