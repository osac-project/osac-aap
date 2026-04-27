# Testing Patterns

**Analysis Date:** 2026-04-27

## Test Framework

**Runner:**
- Ansible playbooks executed via `ansible-playbook`
- No specialized test runner (pytest, etc.) - uses native Ansible execution
- Integration tests only (no unit tests for playbooks)

**Test Infrastructure:**
- Kind (Kubernetes-in-Docker) for test cluster
- Cluster name: `osac-test`
- Kubeconfig: `tests/integration/kubeconfig-osac-test` (dedicated file)

**Run Commands:**
```bash
make test                    # Run all tests (setup + test + teardown)

# Manual workflow
cd tests/integration
./setup_test_env.sh         # Create kind cluster and install CRDs
./run_tests.sh              # Run all tests
./teardown_test_env.sh      # Clean up
```

**Test Execution Requirements:**
- MUST be run from repository root (for `make test`)
- Integration test scripts MUST be run from `tests/integration/` directory
- Requires: `kind`, `kubectl`, `ansible`, `kubernetes` Python library, `openstacksdk` Python library

## Test File Organization

**Location:**
- Co-located with source: NOT used (tests are separate)
- Dedicated test directory: `tests/integration/`

**Naming:**
- Test targets: `targets/{workflow_name}/` (e.g., `targets/cluster_create/`, `targets/finalizer/`)
- Test playbooks: `tasks/baseline.yml`, `tasks/overrides.yml`, `tasks/{scenario}.yml`
- Fixtures: `fixtures/{resource}-test.yaml`

**Structure:**
```
tests/integration/
├── common_vars.yml              # Shared test variables
├── setup_test_env.sh            # Create kind cluster, install CRDs
├── run_tests.sh                 # Execute all tests
├── teardown_test_env.sh         # Delete kind cluster
├── fixtures/                    # Test fixtures (Kubernetes manifests)
│   ├── clusterorder-test.yaml
│   ├── computeinstance-test.yaml
│   └── computeinstance-with-gpu-test.yaml
└── targets/                     # Test targets
    ├── cluster_create/
    │   ├── meta/main.yml        # Test dependencies
    │   └── tasks/
    │       ├── baseline.yml     # Standard workflow test
    │       └── overrides.yml    # Override extension test
    ├── finalizer/
    │   └── tasks/
    │       └── baseline.yml     # Role-level integration test
    └── cluster_working_namespace/
        └── tasks/
            ├── test_not_found.yml    # Scenario: namespace doesn't exist
            ├── test_predefined.yml   # Scenario: namespace predefined
            └── test_found.yml        # Scenario: namespace exists
```

## Test Structure

**Workflow Test Pattern:**

Each workflow test has two files:
1. `baseline.yml`: Tests standard workflow execution
2. `overrides.yml`: Tests all extension points are callable

**Baseline Test Structure:**
```yaml
---
- name: {Workflow} - Baseline Test
  hosts: localhost
  gather_facts: true
  vars_files:
    - ../../../common_vars.yml

  tasks:
    - name: Read {Resource} fixture
      ansible.builtin.set_fact:
        test_resource: "{{ lookup('file', '../../../fixtures/resource-test.yaml') | from_yaml }}"

    - name: Set test variables for baseline workflow
      ansible.builtin.set_fact:
        ansible_eda:
          event:
            payload: "{{ test_resource }}"
        # Override infrastructure steps to avoid actual resource creation
        install_step_cluster_infra_override:
          name: osac.workflows.workflow_helpers
          tasks_from: noop.yml

- name: Import workflow (baseline)
  ansible.builtin.import_playbook: osac.workflows.{workflow}.{action}

- name: Verify baseline results
  hosts: localhost
  gather_facts: false

  tasks:
    - name: Verify expected variable extracted
      ansible.builtin.assert:
        that:
          - variable_name is defined
          - variable_name == "expected_value"
        fail_msg: "Descriptive error message"
```

**Override Test Structure:**
```yaml
---
- name: {Workflow} - Override Test Setup
  hosts: localhost
  gather_facts: true
  vars_files:
    - ../../../common_vars.yml

  tasks:
    - name: Read {Resource} fixture
      ansible.builtin.set_fact:
        test_resource: "{{ lookup('file', '../../../fixtures/resource-test.yaml') | from_yaml }}"

    - name: Clear override log
      ansible.builtin.file:
        path: /tmp/osac_test_overrides.log
        state: absent

    - name: Create empty override log
      ansible.builtin.file:
        path: /tmp/osac_test_overrides.log
        state: touch

    - name: Set test variables with all overrides
      ansible.builtin.set_fact:
        ansible_eda:
          event:
            payload: "{{ test_resource }}"
        hook_workflow_start:
          name: osac.test_overrides.workflow_hooks
          tasks_from: workflow_start.yml
        # ... all override points

- name: Import workflow with overrides
  ansible.builtin.import_playbook: osac.workflows.{workflow}.{action}

- name: Verify override results
  hosts: localhost
  gather_facts: false
  vars_files:
    - ../../../common_vars.yml

  tasks:
    - name: Read override log
      ansible.builtin.slurp:
        path: /tmp/osac_test_overrides.log
      register: override_log_content

    - name: Parse override log
      ansible.builtin.set_fact:
        override_log: "{{ override_log_content.content | b64decode }}"

    - name: Verify all overrides executed
      ansible.builtin.assert:
        that:
          - "'workflow_start' in override_log"
          - "'workflow_complete' in override_log"
          # ... verify all override points
        fail_msg: "Not all override points were executed. Log: {{ override_log }}"
```

**Role Test Pattern:**

Role tests use a single `baseline.yml` file or multiple scenario files:

```yaml
---
- name: {Role} - Baseline Test
  hosts: localhost
  gather_facts: true
  vars_files:
    - ../../../common_vars.yml

  tasks:
    - name: Test role functionality
      ansible.builtin.include_role:
        name: osac.service.{role_name}
      vars:
        role_parameter: test_value

    - name: Verify expected behavior
      ansible.builtin.assert:
        that:
          - expected_condition
        fail_msg: "Error message"
```

**Scenario Test Pattern:**

For roles with `set_fact` persistence issues (variables leak between plays):

```yaml
# targets/cluster_working_namespace/tasks/test_not_found.yml
---
- name: Scenario - Namespace not found
  hosts: localhost
  gather_facts: true
  vars_files:
    - ../../../common_vars.yml

  tasks:
    # ... scenario-specific setup

    - name: Execute role
      ansible.builtin.include_role:
        name: osac.service.cluster_working_namespace
      vars:
        cluster_working_namespace_cluster_order_name: "{{ test_cluster_name }}"

    - name: Verify namespace created
      ansible.builtin.assert:
        that:
          - cluster_working_namespace is defined
```

## Test Fixtures

**Test Data Location:**
- `tests/integration/fixtures/`

**Fixture Format:**
Kubernetes manifests in YAML format:

```yaml
# fixtures/clusterorder-test.yaml
apiVersion: osac.openshift.io/v1alpha1
kind: ClusterOrder
metadata:
  name: test-cluster
  namespace: osac-workflows-test
spec:
  templateId: osac.templates.ocp_4_17_small
  networkClass: cudn
  region: us-east-1
  nodeRequests:
    - resourceClass: small-worker
      count: 3
  templateParameters:
    pull_secret: "fake-pull-secret"
    ssh_public_key: "ssh-rsa fake-key"
```

**Fixture Loading:**
```yaml
- name: Read fixture
  ansible.builtin.set_fact:
    test_resource: "{{ lookup('file', '../../../fixtures/resource-test.yaml') | from_yaml }}"
```

## Test Environment Setup

**Setup Script (`setup_test_env.sh`):**

1. Delete existing `osac-test` kind cluster (if exists)
2. Install Python dependencies: `kubernetes`, `openstacksdk`
3. Create kind cluster with 5-minute wait
4. Export kubeconfig to dedicated file: `kubeconfig-osac-test`
5. Clone `osac-operator` to `/tmp/osac-operator` for CRDs
6. Install OSAC CRDs from `osac-operator/config/crd/bases/`
7. Install external CRDs:
   - KubeVirt operator (for VirtualMachine CRDs)
   - CDI operator (for DataVolume CRDs)
   - OLM CRDs
   - RHACM CRDs (ManagedCluster)
8. Scale down KubeVirt/CDI deployments (keep CRDs, save resources)
9. Create test namespaces:
   - `osac-system`
   - `osac-workflows-test`
   - `cluster-test-cluster-work`
   - `computeinstance-test-vm-work`
10. Apply test fixtures from `fixtures/`

**Teardown Script (`teardown_test_env.sh`):**
- Delete `osac-test` kind cluster
- Remove temporary files

**Environment Variables (set by `run_tests.sh`):**
```bash
export KUBECONFIG="${SCRIPT_DIR}/kubeconfig-osac-test"
export K8S_AUTH_KUBECONFIG="${KUBECONFIG}"
export POD_NAMESPACE="osac-system"
export POD_NAME="test-runner"
export POD_UID="00000000-0000-0000-0000-000000000000"  # Placeholder for GC
export ANSIBLE_INVENTORY_UNPARSED_WARNING=False
export ANSIBLE_LOCALHOST_WARNING=False
```

## Test Execution

**Test Runner (`run_tests.sh`):**

**Workflow Tests:**
- Tests: `cluster_create`, `cluster_delete`, `cluster_post_install`, `compute_instance_create`, `compute_instance_with_gpu_create`, `compute_instance_delete`, `cluster_status_reporting`
- For each workflow:
  1. Run `targets/{workflow}/tasks/baseline.yml`
  2. If `targets/{workflow}/tasks/overrides.yml` exists:
     - Clear `/tmp/osac_test_overrides.log`
     - Run `overrides.yml`
     - Verify log has entries

**Role Tests:**
- Tests: `finalizer`, `lease`
- Creates real pod (`lease-test-pod`) for lease ownerReference tests
- Exports real `POD_UID` for lease tests (prevents Kubernetes GC)
- Runs `targets/{role}/tasks/baseline.yml`

**Role Scenario Tests:**
- Tests with multiple scenarios (separate files):
  - `cluster_working_namespace`: `test_not_found`, `test_predefined`, `test_found`
  - `compute_instance_working_namespace`: `test_not_found`, `test_predefined`, `test_found`
- Each scenario runs independently

**Success Criteria:**
- All tests pass: Exit 0
- Any test fails: Exit 1, print failed test list

**Current Test Status:**
- 10/14 tests passing (as of documentation date)
- Override tests: Require template-level hooks (future work)
- Config-as-code tests: Require AAP instance (not in scope for kind tests)

## Test Assertions

**Pattern:**
```yaml
- name: Verify expected state
  ansible.builtin.assert:
    that:
      - variable is defined
      - variable == "expected_value"
      - list_variable | length > 0
      - "'substring' in string_variable"
    fail_msg: "Descriptive error message with {{ context }}"
```

**Common Assertions:**
- Variable defined: `variable is defined`
- Variable undefined: `variable is not defined`
- Equality: `variable == value`
- List length: `list_var | length > 0`
- String contains: `"'text' in string_var"`
- Multiple conditions: Use list of expressions (AND logic)

## Test Mocking

**Mock Pattern:**
Override infrastructure-creating steps with no-op tasks:

```yaml
install_step_hosted_cluster_override:
  name: osac.workflows.workflow_helpers
  tasks_from: noop.yml
install_step_cluster_infra_override:
  name: osac.workflows.workflow_helpers
  tasks_from: noop.yml
```

**What to Mock:**
- Kubernetes resource creation (HostedCluster, NodePool)
- Cloud provider API calls (infrastructure provisioning)
- External API interactions (fulfillment-service)
- Long-running operations (wait for cluster operators)

**What NOT to Mock:**
- Workflow logic (variable extraction, namespace determination)
- State management (finalizers, leases, locks)
- Template selection and invocation
- Override mechanism itself

**Mock Implementation (`osac.workflows.workflow_helpers`):**
- `noop.yml`: Empty task file that returns success immediately
- Used for default hooks and test mocking

## Test Override Collection

**Collection:** `osac.test_overrides`

**Purpose:**
- Provide test implementations for all workflow and template override points
- Log execution to `/tmp/osac_test_overrides.log` for verification
- Delegate to original roles to maintain workflow integrity (where appropriate)

**Roles:**
- `workflow_hooks`: Generic workflow hooks (start, complete, failure)
- `cluster_hooks`: Cluster-specific hooks (apply_defaults, modify_hosted_cluster, modify_nodepool)
- `vm_create_hooks`: Compute instance hooks (modify_vm_spec, pre_create_hook, post_create_hook)
- `test_template`: Mock template role (install, delete, post_install)

**Test Override Pattern:**
```yaml
# osac.test_overrides.workflow_hooks/tasks/workflow_start.yml
---
- name: Log workflow start hook
  ansible.builtin.lineinfile:
    path: /tmp/osac_test_overrides.log
    line: "{{ workflow_name }}:workflow_start"
    create: yes

# Optional: Delegate to original role if needed
- name: Call original hook
  ansible.builtin.include_role:
    name: osac.workflows.workflow_helpers
    tasks_from: noop.yml
```

**Verification:**
```yaml
- name: Read override log
  ansible.builtin.slurp:
    path: /tmp/osac_test_overrides.log
  register: override_log_content

- name: Parse override log
  ansible.builtin.set_fact:
    override_log: "{{ override_log_content.content | b64decode }}"

- name: Verify override executed
  ansible.builtin.assert:
    that:
      - "'workflow_start' in override_log"
    fail_msg: "Override point was not executed"
```

## Coverage

**Requirements:**
- No explicit coverage targets
- Focus: Verify all override extension points are callable
- 44 extension points total:
  - 33 workflow-level overrides
  - 11 template-level overrides

**Current Coverage:**
- Workflow baseline tests: 7 workflows
- Workflow override tests: 7 workflows (implementation in progress)
- Role integration tests: 8 role/scenario combinations
- Fixture-based tests: 3 fixtures (ClusterOrder, ComputeInstance, ComputeInstance with GPU)

**View Coverage:**
- No automated coverage reporting
- Manual verification via test execution logs
- Override log analysis for extension point coverage

## Test Types

**Integration Tests:**
- Scope: End-to-end workflow execution
- Approach: Real Kubernetes cluster (kind), real CRDs, mocked infrastructure
- Files: All tests in `tests/integration/`
- Run: `make test`

**Unit Tests:**
- Not used for Ansible playbooks/roles
- Python dependencies could be unit tested (but no tests present)

**E2E Tests:**
- Not implemented
- Would require: Real OpenShift cluster, real cloud infrastructure, real AAP instance

## Common Patterns

**Loading Fixtures:**
```yaml
- name: Read fixture
  ansible.builtin.set_fact:
    test_resource: "{{ lookup('file', '../../../fixtures/resource-test.yaml') | from_yaml }}"
```

**Simulating EDA Events:**
```yaml
- name: Set EDA event structure
  ansible.builtin.set_fact:
    ansible_eda:
      event:
        payload: "{{ test_resource }}"
```

**Multi-Play Test Playbooks:**
```yaml
# Play 1: Setup
- name: Setup test
  hosts: localhost
  tasks:
    - name: Prepare test data
      ansible.builtin.set_fact:
        test_var: value

# Play 2: Execute workflow
- name: Import workflow
  ansible.builtin.import_playbook: osac.workflows.cluster.create

# Play 3: Verify
- name: Verify results
  hosts: localhost
  tasks:
    - name: Check outcome
      ansible.builtin.assert:
        that:
          - expected_result
```

**Namespace Cleanup Pattern:**
```yaml
# Not explicitly used - kind cluster is deleted and recreated for each test run
# Future: Could use kubernetes.core.k8s with state: absent for granular cleanup
```

## Test Debugging

**Preserve Test Environment:**
```bash
# Run setup only
cd tests/integration
./setup_test_env.sh

# Run tests manually
export KUBECONFIG="${PWD}/kubeconfig-osac-test"
export K8S_AUTH_KUBECONFIG="${KUBECONFIG}"
ansible-playbook targets/cluster_create/tasks/baseline.yml -e "@common_vars.yml" -vv

# Inspect cluster
kubectl get clusterorders -A
kubectl get namespaces

# Clean up when done
./teardown_test_env.sh
```

**Increase Verbosity:**
```bash
ansible-playbook ... -v    # Basic output
ansible-playbook ... -vv   # More output
ansible-playbook ... -vvv  # Even more output
ansible-playbook ... -vvvv # Connection-level debugging
```

**Override Log Inspection:**
```bash
# View override log during/after test
cat /tmp/osac_test_overrides.log

# Clear override log
> /tmp/osac_test_overrides.log
```

**Kind Cluster Access:**
```bash
# Get clusters
kind get clusters

# Export kubeconfig
kind export kubeconfig --name osac-test

# Delete cluster
kind delete cluster --name osac-test
```

---

*Testing analysis: 2026-04-27*
