# Architecture

**Analysis Date:** 2026-04-27

## Pattern Overview

**Overall:** Event-Driven Override-Based Orchestration

**Key Characteristics:**
- Event-driven automation via Ansible Automation Platform (AAP) with webhooks
- Override pattern allows customer customization without forking
- Template-based infrastructure provisioning with dynamic dispatch
- Multi-collection architecture separating concerns (workflows, service, templates, config)
- State-driven resource lifecycle management

## Layers

**Event Reception Layer (Rulebooks):**
- Purpose: Receive webhooks from fulfillment-service and dispatch to AAP job templates
- Location: `rulebooks/`
- Contains: Event-Driven Ansible (EDA) rulebooks defining webhook endpoints and routing
- Depends on: Ansible EDA plugin (`ansible.eda.webhook`)
- Used by: fulfillment-service (external system)

**Entry Point Layer (Root Playbooks):**
- Purpose: Top-level playbooks that receive EDA events and delegate to workflows
- Location: `playbook_osac_*.yml` (repository root)
- Contains: Simple adapter playbooks extracting `ansible_eda.event.payload` and importing workflow playbooks
- Depends on: Workflow playbooks in `osac.workflows` collection
- Used by: AAP job templates triggered by rulebook actions

**Workflow Orchestration Layer (osac.workflows):**
- Purpose: Multi-step orchestration with override hooks and customer extension points
- Location: `collections/ansible_collections/osac/workflows/`
- Contains: Workflow playbooks organized by category (cluster, compute_instance, reporting)
- Depends on: Service roles (`osac.service`), template roles (`osac.templates`)
- Used by: Entry point playbooks

**Service Implementation Layer (osac.service):**
- Purpose: Reusable service roles for infrastructure operations
- Location: `collections/ansible_collections/osac/service/roles/`
- Contains: 20 service roles (hosted_cluster, cluster_infra, external_access, finalizer, etc.)
- Depends on: Kubernetes API (`kubernetes.core`), cloud providers (vendored collections)
- Used by: Workflow playbooks and template roles

**Template Abstraction Layer (osac.templates):**
- Purpose: Concrete infrastructure patterns implementing specific resource types
- Location: `collections/ansible_collections/osac/templates/roles/`
- Contains: 5 template roles (ocp_4_17_small, metallb_l2, cudn_net, ocp_virt_vm, etc.)
- Depends on: Service roles for actual provisioning
- Used by: Workflows via dynamic dispatch based on `implementationStrategy` or `templateID`

**Configuration as Code Layer (osac.config_as_code):**
- Purpose: Bootstrap and configure AAP instance itself
- Location: `collections/ansible_collections/osac/config_as_code/`
- Contains: AAP configuration playbooks, roles for organization/project/credential setup
- Depends on: AAP platform collections (`ansible.controller`, `ansible.eda`, `ansible.hub`)
- Used by: Bootstrap jobs configuring AAP

**Third-Party Integration Layer (vendor/):**
- Purpose: Vendored external Ansible collections
- Location: `vendor/ansible_collections/`
- Contains: 16+ collections (kubernetes.core, openstack.cloud, amazon.aws, community.general, etc.)
- Depends on: External APIs (Kubernetes, AWS, OpenStack, etc.)
- Used by: All layers requiring external service integration

## Data Flow

**Cluster Creation Flow:**

1. fulfillment-service creates ClusterOrder CRD, sends webhook to EDA
2. Rulebook `rulebooks/cluster_fulfillment.yml` receives event, dispatches to workflow template
3. Root playbook `playbook_osac_create_hosted_cluster.yml` extracts payload, imports `osac.workflows.cluster.create`
4. Workflow executes pre_tasks: hook_workflow_start → extract cluster_order_name → generate lock holder ID → apply defaults → extract template info → determine working namespace
5. Workflow executes tasks: acquire lease → add finalizers → call template role dynamically
6. Template role `osac.templates.ocp_4_17_small` executes install.yaml: pre_install_hook → create hosted_cluster (via osac.service.hosted_cluster) → create cluster_infra → configure external_access → retrieve kubeconfig → wait for cluster operators → post_install_hook
7. Workflow executes hook_workflow_complete
8. Workflow returns control to AAP

**VirtualNetwork Creation Flow:**

1. fulfillment-service creates VirtualNetwork CRD, sends webhook
2. Rulebook routes to create-virtual-network job template
3. Root playbook `playbook_osac_create_virtual_network.yml` extracts `implementationStrategy` from spec
4. Playbook dynamically includes template role: `osac.templates.{{ implementation_strategy }}`
5. Template role executes `tasks_from: create_virtual_network.yaml`
6. For `cudn_net` template: extracts VN config, logs information, returns (actual network provisioning deferred to Subnet creation)

**State Management:**
- Resource definitions passed via `ansible_eda.event.payload` from fulfillment-service
- Workflows are stateless - all state lives in Kubernetes CRDs
- Service roles query/update CRDs using `kubernetes.core` collection
- Finalizers prevent premature deletion during async operations

## Key Abstractions

**Override Variable Pattern:**
- Purpose: Allow customer customization of any workflow step without forking
- Examples: `hook_workflow_start`, `step_apply_defaults_override`, `install_step_hosted_cluster_override`
- Pattern: Each override point defines `{step_name}_default` and checks for `{step_name}_override`

```yaml
# Default definition
vars:
  install_step_hosted_cluster_default:
    name: osac.service.hosted_cluster
    tasks_from: main.yaml

# Usage with override support
- name: Step - Create hosted cluster
  ansible.builtin.include_role:
    name: "{{ (install_step_hosted_cluster_override | default(install_step_hosted_cluster_default)).name }}"
    tasks_from: "{{ (install_step_hosted_cluster_override | default(install_step_hosted_cluster_default)).tasks_from }}"
```

**Implementation Strategy Pattern:**
- Purpose: Dynamic dispatch to template roles based on resource spec
- Examples: VirtualNetwork.spec.implementationStrategy → `cudn_net`, ClusterOrder.spec.templateID → `osac.templates.ocp_4_17_small`
- Pattern: Extract strategy field from CRD, use in dynamic include_role

```yaml
implementation_strategy: "{{ ansible_eda.event.payload.spec.implementationStrategy }}"

- name: Call the selected role
  ansible.builtin.include_role:
    name: "osac.templates.{{ implementation_strategy }}"
    tasks_from: create_virtual_network
```

**Hook Pattern:**
- Purpose: Customer extension points at workflow boundaries
- Examples: `hook_workflow_start`, `hook_workflow_complete`, `hook_workflow_failure`
- Pattern: Workflow-level hooks for cross-cutting concerns, template-level hooks for infrastructure-specific logic

**Finalizer Pattern:**
- Purpose: Prevent resource deletion until cleanup completes
- Examples: `cluster_order_infrastructure_finalizer`, `compute_instance_osac_finalizer`
- Pattern: Add finalizer to CRD at workflow start, remove in delete workflow after cleanup

**Lease Pattern:**
- Purpose: Prevent concurrent modifications to same resource
- Examples: `cluster-{{ cluster_order_name }}-lock`
- Pattern: Acquire lease at workflow start with unique holder ID, release at completion/failure

## Entry Points

**Webhook Entry Point:**
- Location: `rulebooks/cluster_fulfillment.yml`
- Triggers: HTTP POST to EDA webhook listener (port 5000)
- Responsibilities: Route events by endpoint name to corresponding job/workflow templates

**Root Playbook Entry Points:**
- Location: `playbook_osac_*.yml` (17 playbooks)
- Triggers: AAP job template execution
- Responsibilities: Extract EDA payload, import workflow playbook, set initial variables

**Workflow Entry Points:**
- Location: `collections/ansible_collections/osac/workflows/playbooks/{category}/{action}.yml`
- Triggers: Import from root playbooks
- Responsibilities: Orchestrate multi-step operations with override support

## Error Handling

**Strategy:** Ansible native error handling with workflow-level failure hooks

**Patterns:**
- Workflows define `hook_workflow_failure` for cleanup/notification on errors
- Service roles use `when:` conditionals for state-based branching (present/absent)
- Integration tests override infrastructure-creating steps with no-ops to avoid actual provisioning
- Leases ensure exclusive access; failed workflows leave leases that time out
- Finalizers prevent resource deletion if workflow fails mid-execution

## Cross-Cutting Concerns

**Logging:** Ansible native logging via `ansible.builtin.debug` with verbosity levels

**Validation:**
- Template parameters validated by fulfillment-service before webhook
- CRD schemas enforce field constraints
- Workflow playbooks use `ansible.builtin.assert` for critical invariants

**Authentication:**
- AAP authenticates via container group service accounts
- Kubernetes API access via kubeconfig (K8S_AUTH_KUBECONFIG env var)
- Cloud provider credentials injected via secrets (cluster-fulfillment-ig secret)
- fulfillment-service authentication via service account tokens

**Multi-tenancy:**
- Resources include `osac.openshift.io/tenant` annotation
- Namespace-based isolation for cluster workloads
- Template publisher uses RBAC for fulfillment-service access

**Resource Lifecycle:**
- Create workflows: validate → acquire lease → add finalizers → provision → release lease
- Delete workflows: acquire lease → remove resources → remove finalizers → release lease
- Status reporting workflows: query CRD status, aggregate, report to fulfillment-service

---

*Architecture analysis: 2026-04-27*
