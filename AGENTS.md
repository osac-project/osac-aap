# osac-aap

Ansible automation for provisioning OSAC (Open Sovereign AI Cloud) infrastructure resources. Integrates with Ansible Automation Platform (AAP) and provides playbooks, collections, template roles, and Config-as-Code. Created by merging osac-templates into osac-aap.

## Critical Rules

- **Use FQCN** for all modules: `ansible.builtin.debug`, not `debug`
- **Add `name:` to every task** — ansible-lint enforces this
- **Use underscores** in role names and `implementation_strategy`, never hyphens
- **Always include `osac.service.common`** to get `remote_cluster_kubeconfig` before creating K8s resources on remote clusters
- **Run `ansible-lint`** before committing

## Dev Environment

```bash
# Setup
uv sync --all-groups && source .venv/bin/activate

# Lint
ansible-lint

# Test playbook syntax
ansible-playbook --syntax-check playbook_osac_create_subnet.yml

# Test playbook locally
ansible-playbook playbook_osac_create_subnet.yml -e @samples/subnet_payload.json

# Re-vendor collections (after updating collections/requirements.yml)
rm -rf vendor && ansible-galaxy collection install -r collections/requirements.yml

# Integration tests
make test

# Pre-commit hooks
pre-commit run --all-files
```

## Repository Structure

```text
osac-aap/
├── playbook_osac_*.yml                    # Top-level playbooks (AAP job templates)
├── collections/ansible_collections/
│   ├── osac.service/                      # Core service roles (common utilities)
│   ├── osac.templates/                    # Infrastructure templates
│   ├── osac.workflows/                    # Multi-step workflows
│   └── osac.config_as_code/              # AAP configuration
├── vendor/                                # Vendored Ansible collections
├── tests/                                 # Integration test suites
├── samples/                               # Example configurations
└── pyproject.toml                         # Python dependencies (uv)
```

### Collections

| Collection | Purpose | Key Roles |
|------------|---------|-----------|
| **osac.service** | Core utilities | `common`, `finalizer`, `lease`, `wait_for`, `publish_templates`, `tenant_storage_class` |
| **osac.templates** | Infrastructure provisioning | `cudn_net` (networking), `metallb_l2` (PublicIPPool), `ocp_virt_vm` (VMs), `ocp_4_17_small` (clusters) |
| **osac.workflows** | Multi-step playbooks | Cluster create/delete, compute instance lifecycle |
| **osac.config_as_code** | AAP configuration | Job templates, inventories, credentials |

## CI

GitHub Actions (`.github/workflows/`):
- **pre-commit.yaml** — runs pre-commit hooks on PRs
- **tests.yml** — `ansible-lint` + integration tests (with kind cluster)
- **execution-environment.yml** — builds and publishes AAP execution environment image

## Creating a New Template Role

1. Create role at `collections/ansible_collections/osac/templates/roles/<name>/`
2. Add `meta/osac.yaml` with `implementation_strategy`, `template_type`, `capabilities`
3. Create task files: `tasks/create_<resource>.yaml`, `tasks/delete_<resource>.yaml`
4. Run `playbook_osac_config_as_code.yml` to register and publish NetworkClass

## Common Pitfalls

1. **venv not activated** — `ansible-playbook: command not found` → `source .venv/bin/activate` or `uv run`
2. **Stale vendored collections** — re-vendor after updating `collections/requirements.yml`
3. **Implementation strategy mismatch** — role dir name, `meta/osac.yaml`, and CR annotation must all match (use underscores)
4. **Missing remote kubeconfig** — always include `osac.service.common` with `tasks_from: get_remote_cluster_kubeconfig`
5. **Namespace label syntax** — `k8s.ovn.org/primary-user-defined-network: ""` (empty string, not missing value)

## Cross-Repo Coordination

**Adding a new field to a resource (e.g., `mtu` to Subnet):**
1. fulfillment-service: Add field to proto, regenerate
2. osac-operator: Add field to CRD spec, update controller
3. osac-aap: Extract field in playbook, pass to role
4. osac-aap: Role reads field and provisions infrastructure

**Adding a new networking implementation:**
1. osac-aap: Create template role with `meta/osac.yaml`
2. osac-aap: Run config-as-code to publish NetworkClass
3. fulfillment-service: NetworkClass auto-discovered in API
4. Users: Create VirtualNetwork with new `networkClass`

## PR Checklist

- [ ] `ansible-lint` passes
- [ ] `meta/osac.yaml` updated for template role changes
- [ ] Cross-repo dependencies documented in PR description
- [ ] Playbook tested locally or against AAP

## Playbook and Template Patterns

### Playbook Naming

Top-level playbooks: `playbook_osac_{action}_{resource}.yml`
AAP job templates: `osac-{action}-{resource}`

| Playbook | AAP Job Template | Triggered By |
|----------|------------------|--------------|
| `playbook_osac_create_subnet.yml` | `osac-create-subnet` | osac-operator SubnetReconciler |
| `playbook_osac_delete_virtual_network.yml` | `osac-delete-virtual-network` | osac-operator VirtualNetworkReconciler |
| `playbook_osac_create_security_group.yml` | `osac-create-security-group` | osac-operator SecurityGroupReconciler |

**Configuration:** osac-operator env var `OSAC_AAP_TEMPLATE_PREFIX` (default: `osac`)

### Standard Playbook Structure

```yaml
---
- name: Create a Subnet resource
  hosts: localhost
  gather_facts: false

  vars:
    subnet: "{{ ansible_eda.event.payload }}"
    subnet_name: "{{ ansible_eda.event.payload.metadata.name }}"
    implementation_strategy: >-
      {{ ansible_eda.event.payload.metadata.annotations
         ['osac.openshift.io/implementation-strategy']
         | default(ansible_eda.event.payload.spec.implementationStrategy, true) }}

  pre_tasks:
    - name: Show EDA Event
      ansible.builtin.debug:
        var: ansible_eda.event.payload

  tasks:
    - name: Call the selected implementation role
      ansible.builtin.include_role:
        name: "osac.templates.{{ implementation_strategy }}"
        tasks_from: create_subnet
```

**Key pattern:**
1. Playbook receives K8s CR as `ansible_eda.event.payload`
2. Extracts implementation strategy from CR annotation (`osac.openshift.io/implementation-strategy`) or `spec.implementationStrategy` — annotation takes precedence when both are present
3. Dynamically includes the appropriate role from `osac.templates`
4. Role performs actual provisioning (creates K8s resources, updates CR)

### Template Roles

Live in `collections/ansible_collections/osac/templates/roles/`. Each must have `meta/osac.yaml`:

```yaml
---
title: CUDN Network Implementation
description: Provisions networking resources using CUDN
template_type: network
implementation_strategy: cudn_net
capabilities:
  supports_ipv4: true
  supports_ipv6: true
  supports_dual_stack: true
```

**Fields:**
- `implementation_strategy` — matches annotation value, role name, and NetworkClass strategy
- `template_type` — `network`, `compute`, or `cluster`
- `capabilities` — feature flags published to NetworkClass

**Note:** Use underscores (`_`), not hyphens (`-`), in role names and `implementation_strategy`.

### Service Roles

| Role | Purpose | Usage |
|------|---------|-------|
| `osac.service.common` | Shared utilities (kubeconfig, credentials) | `tasks_from: get_remote_cluster_kubeconfig` |
| `osac.service.finalizer` | Finalizer management for CRs | `tasks_from: add_finalizer` |
| `osac.service.lease` | Bare-metal lease management | Used by cluster/compute workflows |
| `osac.service.wait_for` | Polling utilities | Wait for pods, deployments, CRs |
| `osac.service.tenant_storage_class` | StorageClass discovery | Find tenant-specific storage |
| `osac.service.publish_templates` | Template registration | Publishes NetworkClass from `meta/osac.yaml` |

### Common Ansible Patterns

**Extracting CR Fields:**

```yaml
- name: Extract Subnet configuration
  ansible.builtin.set_fact:
    subnet_name: "{{ subnet.metadata.name }}"
    subnet_namespace: "{{ subnet.metadata.namespace }}"
    subnet_id: "{{ subnet.metadata.labels['osac.openshift.io/subnet-uuid'] }}"
    subnet_ipv4_cidr: "{{ subnet.spec.ipv4Cidr | default('') }}"
    subnet_tenant_id: "{{ subnet.metadata.annotations['osac.openshift.io/tenant'] }}"
```

**Creating K8s Resources on Remote Cluster:**

```yaml
- name: Get remote cluster kubeconfig
  ansible.builtin.include_role:
    name: osac.service.common
    tasks_from: get_remote_cluster_kubeconfig

- name: Create Namespace for Subnet
  kubernetes.core.k8s:
    kubeconfig: "{{ remote_cluster_kubeconfig | default(omit) }}"
    state: present
    definition:
      apiVersion: v1
      kind: Namespace
      metadata:
        name: "{{ subnet_name }}"
        labels:
          osac.openshift.io/subnet-id: "{{ subnet_id }}"
          osac.openshift.io/tenant: "{{ subnet_tenant_id }}"
```

### Variable Flow

```text
osac-operator
  ↓ (triggers AAP job template)
playbook_osac_create_subnet.yml
  ↓ (sets implementation_strategy from annotation)
osac.templates.cudn_net (role)
  ↓ (reads subnet.spec.*, creates K8s resources)
Namespace + ClusterUserDefinedNetwork
```

### Runtime Variables

| Variable | Purpose | Set By |
|----------|---------|--------|
| `ansible_eda.event.payload` | K8s CR data | AAP/EDA event |
| `remote_cluster_kubeconfig` | Path to remote kubeconfig | `osac.service.common` role |
| `implementation_strategy` | Network implementation to use | Extracted from CR annotation |
| `OSAC_AAP_URL` | AAP server URL | osac-operator config |
| `OSAC_AAP_TOKEN` | AAP auth token | osac-operator config |

## Networking Implementation: cudn_net

The `cudn_net` role implements networking via OpenShift's ClusterUserDefinedNetwork (CUDN).

### Architecture

```text
VirtualNetwork (logical grouping)
  └── Subnet (Namespace + CUDN + IPAM)
        └── SecurityGroup (NetworkPolicy)
```

**VirtualNetwork:** Logical grouping only (no K8s resources created). Stores CIDR blocks and implementation strategy.

**Subnet:** Creates **Namespace** with labels for OVN primary UDN, plus **ClusterUserDefinedNetwork** with namespaceSelector. Provisions Layer-2 network with persistent IPAM.

**SecurityGroup:** Creates **NetworkPolicy** in target namespace. Translates ingress/egress rules to K8s NetworkPolicy. Supports TCP, UDP, ICMP, port ranges, CIDR sources.

### Key Files

- `collections/ansible_collections/osac/templates/roles/cudn_net/tasks/create_subnet.yaml` — Creates Namespace with `k8s.ovn.org/primary-user-defined-network: ""` label, creates CUDN
- `collections/ansible_collections/osac/templates/roles/cudn_net/tasks/create_security_group.yaml` — Translates SecurityGroup CR to NetworkPolicy

### Namespace Label Syntax (Critical)

Label value must be empty string, not missing:

```yaml
# Correct:
labels:
  k8s.ovn.org/primary-user-defined-network: ""

# Incorrect (will NOT work):
labels:
  k8s.ovn.org/primary-user-defined-network:
```

### Conditional CIDR Handling

```yaml
- name: Build CUDN subnets array
  ansible.builtin.set_fact:
    cudn_subnets: >-
      {{
        ((subnet_ipv4_cidr | length > 0) | ternary([subnet_ipv4_cidr], []))
        + ((subnet_ipv6_cidr | length > 0) | ternary([subnet_ipv6_cidr], []))
      }}
```

## Links

- [Ansible Documentation](https://docs.ansible.com/)
- [kubernetes.core collection](https://docs.ansible.com/ansible/latest/collections/kubernetes/core/)
- [osac-operator](https://github.com/osac-project/osac-operator) — Kubernetes operator integration
- [fulfillment-service](https://github.com/osac-project/fulfillment-service) — Backend API
