#!/bin/bash
set -e

echo "=== Tearing down test environment ==="

# Delete kind cluster
kind delete cluster --name osac-test

# Clean up temporary files
rm -f /tmp/osac_test_overrides.log
rm -rf /tmp/osac-operator

echo "=== Cleanup complete ==="
