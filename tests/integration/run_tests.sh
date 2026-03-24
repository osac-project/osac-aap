#!/bin/bash
set -e

# Set KUBECONFIG to dedicated file for kind cluster
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export KUBECONFIG="${SCRIPT_DIR}/kubeconfig-osac-test"
export K8S_AUTH_KUBECONFIG="${KUBECONFIG}"
echo "Using kubeconfig: ${KUBECONFIG}"

# Set Pod environment variables for lease creation (normally set by Kubernetes)
export POD_NAMESPACE="osac-system"
export POD_NAME="test-runner"
export POD_UID="00000000-0000-0000-0000-000000000000"

# Suppress inventory parsing warnings
export ANSIBLE_INVENTORY_UNPARSED_WARNING=False
export ANSIBLE_LOCALHOST_WARNING=False

FAILED=()
PASSED=()

# Test workflows
WORKFLOWS=(
  "cluster_create"
  "cluster_delete"
  "cluster_post_install"
  "compute_instance_create"
  "compute_instance_delete"
  "hostpool_create"
  "hostpool_delete"
  "cluster_status_reporting"
  "hostpool_status_reporting"
)

echo "=== Running Integration Tests ==="
echo ""

for workflow in "${WORKFLOWS[@]}"; do
  echo "----------------------------------------"
  echo "Testing: $workflow"
  echo "----------------------------------------"

  # Baseline test
  echo "  [1/2] Running baseline test..."
  if ansible-playbook "targets/${workflow}/tasks/baseline.yml" -e "@common_vars.yml" -v; then
    echo "  ✓ Baseline passed"
    PASSED+=("$workflow:baseline")
  else
    echo "  ✗ Baseline failed"
    FAILED+=("$workflow:baseline")
  fi

  # Override test
  echo "  [2/2] Running override test..."
  # Clear override log
  > /tmp/osac_test_overrides.log

  if ansible-playbook "targets/${workflow}/tasks/overrides.yml" -e "@common_vars.yml" -v; then
    # Verify override log has entries
    if [ -s /tmp/osac_test_overrides.log ]; then
      echo "  ✓ Override test passed"
      PASSED+=("$workflow:overrides")
    else
      echo "  ✗ Override test failed (no override log entries)"
      FAILED+=("$workflow:overrides-no-log")
    fi
  else
    echo "  ✗ Override test failed"
    FAILED+=("$workflow:overrides")
  fi

  echo ""
done

echo "========================================"
echo "Test Results"
echo "========================================"
echo "Passed: ${#PASSED[@]}"
echo "Failed: ${#FAILED[@]}"

if [ ${#FAILED[@]} -eq 0 ]; then
  echo ""
  echo "✓ All tests passed!"
  exit 0
else
  echo ""
  echo "✗ Failed tests:"
  for test in "${FAILED[@]}"; do
    echo "  - $test"
  done
  exit 1
fi
