# Codebase Structure

**Analysis Date:** 2026-04-27

## Directory Layout

```
osac-aap/
├── collections/                              # Local Ansible collections
│   ├── ansible_collections/osac/workflows/  # Workflow orchestration playbooks
│   ├── ansible_collections/osac/service/    # Reusable service roles
│   ├── ansible_collections/osac/templates/  # Infrastructure template roles
│   ├── ansible_collections/osac/config_as_code/  # AAP configuration
│   ├── ansible_collections/osac/test_overrides/  # Test override validation
│   ├── ansible_collections/massopencloud/   # MassOpenCloud provider integration
│   └── ansible_collections/netris/          # Netris network provider integration
│   └── requirements.yml                      # Third-party collection dependencies
├── vendor/                                   # Vendored third-party collections
├── playbook_osac_*.yml                       # Root-level entry point playbooks
├── rulebooks/                                # Event-Driven Ansible rulebooks
├── execution-environment/                    # Container image build definition
├── tests/integration/                        # Integration test suite
├── samples/                                  # Example resource definitions
├── config/                                   # AAP configuration files
├── docs/                                     # Documentation
├── ansible.cfg                               # Ansible configuration
└── pyproject.toml                            # Python dependencies (managed by uv)
```

## Directory Purposes

**collections/ansible_collections/osac/workflows:**
- Purpose: Multi-step workflow playbooks with customer override support
- Contains: Playbooks organized by category (cluster/, compute_instance/, reporting/)
- Key files:
  - `playbooks/cluster/create.yml` - Orchestrate hosted cluster creation
  - `playbooks/cluster/delete.yml` - Orchestrate cluster deletion
  - `playbooks/cluster/post_install.yml` - Post-installation configuration
  - `playbooks/compute_instance/create.yml` - VM provisioning workflow
  - `playbooks/reporting/cluster_status.yml` - Status reporting
  - `roles/workflow_helpers/tasks/noop.yml` - Default no-op for hooks

**collections/ansible_collections/osac/service:**
- Purpose: Reusable service roles implementing infrastructure operations
- Contains: 20 service roles for specific capabilities
- Key roles:
  - `hosted_cluster` - Create/delete OpenShift hosted control plane
  - `cluster_infra` - Provision cluster infrastructure (nodes, networking)
  - `external_access` - Configure ingress/egress and port forwarding
  - `finalizer` - Add/remove Kubernetes finalizers
  - `lease` - Acquire/release resource locks
  - `retrieve_kubeconfig` - Extract admin kubeconfig from cluster
  - `wait_for` - Poll until resources reach desired state
  - `nmstate_config` - Configure network interfaces via NMState
  - `common` - Shared utilities (get_remote_cluster_kubeconfig)
  - `publish_templates` - Register templates with fulfillment-service
  - `enumerate_templates` - Discover templates from collections
  - `extract_template_info` - Parse template metadata from CRDs

**collections/ansible_collections/osac/templates:**
- Purpose: Concrete infrastructure patterns for specific resource types
- Contains: 5 template roles implementing different infrastructure strategies
- Key roles:
  - `ocp_4_17_small` - Small OpenShift 4.17 cluster (tasks: install.yaml, delete.yaml, post_install.yaml)
  - `ocp_4_17_small_github` - Variant with GitHub integration
  - `metallb_l2` - MetalLB Layer 2 load balancer configuration
  - `cudn_net` - CUDN network provider (tasks: create/delete virtual_network, subnet, security_group)
  - `ocp_virt_vm` - OpenShift Virtualization VM provisioning

**collections/ansible_collections/osac/config_as_code:**
- Purpose: Bootstrap and configure AAP instances
- Contains: Playbooks and roles for AAP setup
- Key files:
  - `playbooks/configure.yml` - Configure AAP organization, projects, job templates
  - `playbooks/subscription.yml` - Apply AAP license manifest
  - `README.md` - Detailed setup guide with environment variables

**collections/ansible_collections/osac/test_overrides:**
- Purpose: Validate all workflow extension points
- Contains: Test roles that log execution and delegate to original implementations
- Used by: Integration tests verifying 44 override points (33 workflow-level, 11 template-level)

**collections/ansible_collections/massopencloud:**
- Purpose: MassOpenCloud provider-specific integration
- Contains: ESI (Elastic Secure Infrastructure) roles and steps

**collections/ansible_collections/netris:**
- Purpose: Netris network controller integration
- Contains: Netris API client roles and configuration steps

**vendor/ansible_collections:**
- Purpose: Third-party Ansible collections vendored locally
- Contains: 16 collections (kubernetes.core, openstack.cloud, amazon.aws, ansible.controller, ansible.eda, infra.aap_configuration, etc.)
- Generated: Yes (via `ansible-galaxy collection install -r collections/requirements.yml`)
- Committed: Yes

**playbook_osac_*.yml (root):**
- Purpose: Entry point playbooks invoked by AAP job templates
- Contains: 17 top-level playbooks for create/delete operations
- Key files:
  - `playbook_osac_create_hosted_cluster.yml` - Cluster creation entry point
  - `playbook_osac_delete_hosted_cluster.yml` - Cluster deletion entry point
  - `playbook_osac_create_compute_instance.yml` - VM creation entry point
  - `playbook_osac_create_virtual_network.yml` - VirtualNetwork creation
  - `playbook_osac_create_subnet.yml` - Subnet creation
  - `playbook_osac_create_security_group.yml` - SecurityGroup creation
  - `playbook_osac_create_public_ip_pool.yml` - PublicIPPool creation
  - `playbook_osac_cleanup_stale_network_resources.yml` - Maintenance workflow
  - `playbook_osac_config_as_code.yml` - AAP bootstrap entry point

**rulebooks:**
- Purpose: Event-Driven Ansible rulebooks defining webhook routing
- Contains: EDA rulebooks mapping webhook endpoints to job templates
- Key files:
  - `cluster_fulfillment.yml` - Main rulebook routing cluster/compute/network events

**execution-environment:**
- Purpose: Container image definition for Ansible execution environment
- Contains: `execution-environment.yaml` (ansible-builder config), `requirements.txt` (Python deps)
- Generated: `requirements.txt` generated via `uv pip compile ../pyproject.toml`
- Committed: Yes

**tests/integration:**
- Purpose: Integration test suite validating workflows and overrides
- Contains: Test targets organized by component (cluster_create, cluster_delete, finalizer, lease, etc.)
- Key structure:
  - `targets/{component}/tasks/baseline.yml` - Baseline test without overrides
  - `targets/{component}/tasks/overrides.yml` - Test with customer overrides
  - `common_vars.yml` - Shared test variables
  - `setup_test_env.sh` - Create kind cluster and install CRDs
  - `run_tests.sh` - Execute all integration tests
  - `teardown_test_env.sh` - Clean up test environment

**samples:**
- Purpose: Example resource definitions for testing
- Contains: Sample CRD manifests (ClusterOrder, ComputeInstance, VirtualNetwork, etc.)

**config:**
- Purpose: AAP instance configuration files
- Contains: Configuration templates and manifests

**docs:**
- Purpose: User-facing documentation
- Contains: Getting started guides, architecture diagrams, API references

## Key File Locations

**Entry Points:**
- `playbook_osac_create_hosted_cluster.yml` - Cluster creation entry point
- `playbook_osac_create_virtual_network.yml` - Network resource entry point
- `rulebooks/cluster_fulfillment.yml` - Event routing configuration

**Configuration:**
- `ansible.cfg` - Ansible configuration (jinja2_native=True, collections_path)
- `pyproject.toml` - Python dependencies
- `collections/requirements.yml` - Third-party collection dependencies
- `execution-environment/execution-environment.yaml` - Container image build config
- `.ansible-lint.yml` - Linting rules
- `.yamllint.yaml` - YAML formatting rules

**Core Logic:**
- `collections/ansible_collections/osac/workflows/playbooks/cluster/create.yml` - Main cluster creation workflow
- `collections/ansible_collections/osac/service/roles/hosted_cluster/tasks/main.yaml` - Hosted cluster service role
- `collections/ansible_collections/osac/templates/roles/ocp_4_17_small/tasks/install.yaml` - Small cluster template

**Testing:**
- `tests/integration/targets/*/tasks/baseline.yml` - Integration test implementations
- `Makefile` - Test orchestration (`make test`)

## Naming Conventions

**Files:**
- Root playbooks: `playbook_osac_{action}_{resource}.yml` (e.g., `playbook_osac_create_virtual_network.yml`)
- Workflow playbooks: `{category}/{action}.yml` (e.g., `cluster/create.yml`, `compute_instance/delete.yml`)
- Task files: `{action}.yaml` or `{action}_{resource}.yaml` (e.g., `create.yaml`, `create_virtual_network.yaml`)
- Main task files: `main.yml` or `main.yaml`

**Directories:**
- Collections: `ansible_collections/{namespace}/{name}/` (e.g., `ansible_collections/osac/workflows/`)
- Roles: `roles/{role_name}/` (e.g., `roles/hosted_cluster/`)
- Playbook categories: `playbooks/{category}/` (e.g., `playbooks/cluster/`)

**Override Variables:**
- Workflow hooks: `hook_{workflow_event}` (e.g., `hook_workflow_start`, `hook_workflow_complete`)
- Workflow step overrides: `step_{action}_override` (e.g., `step_apply_defaults_override`)
- Template step overrides: `{action}_step_{operation}_override` (e.g., `install_step_hosted_cluster_override`)
- Default values: `{override_name}_default` (e.g., `hook_workflow_start_default`)

**Collections:**
- Namespace: `osac` for OSAC-specific, `massopencloud`/`netris` for providers
- Collection names: `workflows`, `service`, `templates`, `config_as_code`, `test_overrides`

## Where to Add New Code

**New Workflow (e.g., "configure storage"):**
- Primary code: `collections/ansible_collections/osac/workflows/playbooks/storage/configure.yml`
- Entry point: `playbook_osac_configure_storage.yml` (root)
- Rulebook route: Add rule to `rulebooks/cluster_fulfillment.yml`
- Tests: `tests/integration/targets/storage_configure/tasks/baseline.yml`

**New Service Role (e.g., "backup_manager"):**
- Implementation: `collections/ansible_collections/osac/service/roles/backup_manager/tasks/main.yaml`
- Sub-tasks: `collections/ansible_collections/osac/service/roles/backup_manager/tasks/{create,delete,restore}.yaml`
- Defaults: `collections/ansible_collections/osac/service/roles/backup_manager/defaults/main.yaml`

**New Template Role (e.g., "ocp_4_18_large"):**
- Directory: `collections/ansible_collections/osac/templates/roles/ocp_4_18_large/`
- Task files: `tasks/install.yaml`, `tasks/delete.yaml`, `tasks/post_install.yaml`
- Metadata: `meta/template.yaml` (template metadata for publish_templates role)
- Register: Add to `OSAC_TEMPLATE_COLLECTIONS` env var if should be published

**New Override Hook:**
- Define default in workflow playbook vars section: `{hook_name}_default`
- Add include_role task with override support: `{{ ({hook_name}_override | default({hook_name}_default)).name }}`
- Document in workflow playbook header comments
- Add test case to `collections/ansible_collections/osac/test_overrides/`

**Utilities:**
- Shared helpers: `collections/ansible_collections/osac/service/roles/common/tasks/{utility_name}.yml`
- Workflow helpers: `collections/ansible_collections/osac/workflows/roles/workflow_helpers/tasks/{helper_name}.yml`

**Network Resource Templates:**
- VirtualNetwork: `collections/ansible_collections/osac/templates/roles/{template_name}/tasks/create_virtual_network.yaml`
- Subnet: `collections/ansible_collections/osac/templates/roles/{template_name}/tasks/create_subnet.yaml`
- SecurityGroup: `collections/ansible_collections/osac/templates/roles/{template_name}/tasks/create_security_group.yaml`
- All must implement both create and delete variants

## Special Directories

**vendor/:**
- Purpose: Vendored third-party Ansible collections
- Generated: Yes (via `ansible-galaxy collection install`)
- Committed: Yes (ensures consistent dependencies)
- Excluded from: ansible-lint (see `.ansible-lint.yml`)

**.venv/:**
- Purpose: Python virtual environment (uv managed)
- Generated: Yes (via `uv sync`)
- Committed: No

**.pytest_cache/:**
- Purpose: Pytest cache directory
- Generated: Yes (by pytest)
- Committed: No

**.planning/:**
- Purpose: GSD workflow state and codebase documentation
- Generated: Partially (by `/gsd:*` commands)
- Committed: Yes

**.github/workflows/:**
- Purpose: CI/CD pipeline definitions
- Contains: GitHub Actions for pre-commit hooks, tests, execution environment builds
- Key files:
  - `tests.yml` - Run integration tests on PRs
  - `execution-environment.yml` - Build and push container image
  - `pre-commit.yaml` - Run linters and formatters

**collections/ansible_collections/osac/*/docs/:**
- Purpose: Collection-specific documentation
- Contains: Collection READMEs, API docs, architecture guides
- Committed: Yes

## Collection Dependency Resolution

**Order of precedence:** `./collections` → `./vendor` → system collections (disabled)

Configured in `ansible.cfg`:
```ini
collections_path=./vendor:./collections
collections_scan_sys_path=False
```

This ensures:
1. Local OSAC collections in `./collections` are loaded first
2. Vendored third-party collections in `./vendor` are used next
3. System-wide collections are ignored (prevents version conflicts)

**Updating vendored collections:**
1. Edit `collections/requirements.yml`
2. Run `rm -rf vendor && ansible-galaxy collection install -r collections/requirements.yml`
3. Commit changes to `vendor/`

---

*Structure analysis: 2026-04-27*
