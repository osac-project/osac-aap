# Coding Conventions

**Analysis Date:** 2026-04-27

## Naming Patterns

**Playbook Files:**
- Root-level playbooks: `playbook_osac_{action}_{resource}.yml`
- Examples: `playbook_osac_create_virtual_network.yml`, `playbook_osac_delete_hosted_cluster.yml`
- Workflow playbooks: `{category}/{action}.yml` (e.g., `cluster/create.yml`, `compute_instance/delete.yml`)

**Collection Directories:**
- Use underscores: `osac/workflows/`, `osac/service/`, `osac/templates/`, `osac/config_as_code/`
- Test collection: `osac/test_overrides/`

**Role Names:**
- Service roles: Descriptive nouns (e.g., `cluster_infra`, `hosted_cluster`, `external_access`, `finalizer`)
- Template roles: Technology-based (e.g., `ocp_4_17_small`, `cudn_net`, `metallb_l2`, `ocp_virt_vm`)
- Use snake_case throughout

**Task Files:**
- Primary entry: `main.yaml` (NOT `main.yml`)
- Action-based: `create.yaml`, `delete.yaml`, `install.yaml`, `post_install.yaml`
- Feature-based: `create_virtual_network.yaml`, `delete_security_group.yaml`
- Utility: `noop.yaml` (for default hooks and overrides)

**Variables:**
- Use snake_case: `cluster_order_name`, `virtual_network`, `implementation_strategy`
- Override variables: `{phase}_{action}_override` (e.g., `install_step_cluster_infra_override`, `hook_workflow_start`)
- Default variables: `{phase}_{action}_default` (e.g., `install_step_cluster_infra_default`)
- Role parameters: Prefix with role name (e.g., `cluster_infra_state`, `finalizer_name`, `lease_holder`)
- Internal/temporary variables: Prefix with underscore (e.g., `_nmstate_gateway_ip`, `_wait_co_results`)

**Constants/Labels:**
- Defined in `tests/integration/common_vars.yml` and `group_vars/all/`
- Use kebab-case for labels: `osac.openshift.io/clusterorder`, `osac.openshift.io/infrastructure`
- Examples: `cluster_order_label`, `cluster_order_infrastructure_finalizer`, `compute_instance_label`

## Code Style

**Formatting:**
- Tool: `yamllint` (configured via `.yamllint.yaml`)
- Line length: Disabled (no hard limit)
- Document start: Disabled (no `---` requirement, but convention uses it)
- Indentation: `indent-sequences: whatever` (flexible list indentation)
- Hyphens: Maximum 4 spaces after hyphen
- Truthy: `check-keys: false` (allows `yes`/`no` in YAML)
- Comments: Minimum 1 space from content

**YAML Conventions:**
- Use `.yaml` extension (NOT `.yml`) for all task files, role files, and collection metadata
- Use `.yml` extension for root-level playbooks and configuration files only
- Always start playbooks and task files with `---`
- Use explicit string quoting for: Jinja2 expressions with filters, file paths with spaces
- Use unquoted strings for: Module names, simple variable references

**Linting:**
- Tool: `ansible-lint` (configured via `.ansible-lint.yml`)
- Skipped rules:
  - `role-name[path]`: Roles use collection namespaces
  - `parser-error`: Multi-play test playbooks trigger false positives
  - `fqcn[keyword]`: Workflows use `collections:` keyword
- Warned (not failed):
  - `risky-file-permissions`: Test code uses `lineinfile` without `mode`
- Excluded paths: `vendor/`, `.github/`, `collections/ansible_collections/massopencloud/`, `execution-environment/`

**Pre-commit Hooks:**
- Configured via `.pre-commit-config.yaml`
- Hooks: `trailing-whitespace`, `check-merge-conflict`, `end-of-file-fixer`, `check-added-large-files`, `check-case-conflict`, `check-json`, `check-symlinks`, `detect-private-key`, `yamllint --strict`
- Excludes: `vendor/.*`

## Import Organization

**Module FQCN (Fully Qualified Collection Names):**
- Always use FQCN for modules: `ansible.builtin.debug`, `kubernetes.core.k8s`, `ansible.utils.ipaddr`
- Never use short names like `debug`, `set_fact`, `k8s`

**Collection Resolution:**
- Workflows define collections at playbook level:
```yaml
collections:
  - osac.workflows
  - osac.service
```
- Allows unqualified role names: `include_role: name: cluster_infra` (resolves to `osac.service.cluster_infra`)

**Include/Import Order:**
1. External role includes (if any)
2. Pre-tasks (hooks, critical setup)
3. Main tasks (workflow steps)
4. Post-tasks (completion hooks)

**Role Include Pattern:**
```yaml
- name: Step description
  ansible.builtin.include_role:
    name: "{{ (step_override | default(step_default)).name }}"
    tasks_from: "{{ (step_override | default(step_default)).tasks_from }}"
  vars:
    role_param_1: value
    role_param_2: value
```

## Ansible Configuration

**Critical Settings (`ansible.cfg`):**
- `jinja2_native=True`: Allows integers and booleans without quotes (required for Kubernetes manifests)
- `collections_path=./vendor:./collections`: Local collections take precedence over vendored
- `collections_scan_sys_path=False`: Ignore system-wide collections
- `become_method=sudo`: Default privilege escalation
- `connect_timeout=30`: Persistent connection idle timeout
- `command_timeout=30`: Remote device response timeout

## Error Handling

**Patterns:**
- Use `failed_when: false` for cleanup operations that may not find resources
- Use `when:` conditionals to guard operations (e.g., `when: finalizer_state == "present"`)
- Use `ignore_errors: yes` sparingly (not detected in codebase)

**Assertions:**
```yaml
- name: Verify expected state
  ansible.builtin.assert:
    that:
      - variable_name is defined
      - variable_name == "expected_value"
    fail_msg: "Descriptive error message"
```

## Logging and Debugging

**Debug Output:**
```yaml
- name: Display information
  ansible.builtin.debug:
    msg:
      - "Item 1: {{ variable }}"
      - "Item 2: {{ other_variable }}"
      - ""
      - "NOTE: Additional context"
```
- Use multi-line messages with `msg:` list format
- Include context and labels for clarity

**Test Logging (osac.test_overrides collection):**
- Logs to `/tmp/osac_test_overrides.log`
- Uses `lineinfile` to append execution markers
- Format: `{workflow_name}:{hook_name}` (e.g., `cluster_create:workflow_start`)

## Override Pattern

**Core Architecture Pattern:**
Every workflow step supports customer overrides without forking code.

**Override Variable Structure:**
```yaml
step_name_override:
  name: custom.collection.role_name  # Role to execute
  tasks_from: custom_task_file.yml   # Task file within role
```

**Default Pattern:**
```yaml
# In workflow playbook
vars:
  step_name_default:
    name: osac.service.default_role
    tasks_from: main.yaml

tasks:
  - name: Execute step
    ansible.builtin.include_role:
      name: "{{ (step_name_override | default(step_name_default)).name }}"
      tasks_from: "{{ (step_name_override | default(step_name_default)).tasks_from }}"
```

**Override Categories:**
- `hook_{phase}`: Workflow boundary hooks (start, complete, failure)
- `step_{action}_override`: Workflow-level step overrides
- `{phase}_step_{action}_override`: Template-level step overrides (e.g., `install_step_cluster_infra_override`)

**Hook Types:**
- `hook_workflow_start`: Execute before workflow begins
- `hook_workflow_complete`: Execute after successful completion
- `hook_workflow_failure`: Execute on failure (not yet implemented in all workflows)
- Template-specific hooks: `{action}_modify_{resource}_hook` (e.g., `hosted_cluster_modify_definition_hook`)

**Critical (Non-overrideable) Steps:**
- Marked with `# CRITICAL:` comments in workflow playbooks
- Examples: Lock acquisition, finalizer management, resource name extraction
- Never override these without understanding workflow integrity requirements

## Event-Driven Architecture

**EDA Event Structure:**
```yaml
vars:
  resource: "{{ ansible_eda.event.payload }}"
  resource_name: "{{ ansible_eda.event.payload.metadata.name }}"
  implementation_strategy: "{{ ansible_eda.event.payload.spec.implementationStrategy }}"
```

**Dynamic Template Resolution:**
```yaml
- name: Call the selected role
  ansible.builtin.include_role:
    name: "osac.templates.{{ implementation_strategy }}"
    tasks_from: create_virtual_network
```
- The `implementationStrategy` field from CRD spec determines which template role executes
- Template roles must implement all required task files for their resource type

## Kubernetes Interaction

**Resource Lookup:**
```yaml
- name: Look up resource
  kubernetes.core.k8s_info:
    api_version: "{{ resource.api_version }}"
    kind: "{{ resource.kind }}"
    namespace: "{{ resource.namespace }}"
    name: "{{ resource.name }}"
  register: resource_result
```

**Resource Creation/Update:**
```yaml
- name: Create/update resource
  kubernetes.core.k8s:
    state: present
    definition:
      apiVersion: v1
      kind: ConfigMap
      metadata:
        name: example
        namespace: default
      data:
        key: value
```

**JSON Patch for Updates:**
```yaml
- name: Patch resource
  kubernetes.core.k8s_json_patch:
    api_version: v1
    kind: ConfigMap
    namespace: default
    name: example
    patch:
      - op: replace
        path: /data/key
        value: new_value
```

**KUBECONFIG Handling:**
```yaml
environment:
  K8S_AUTH_KUBECONFIG: "{{ lookup('env', 'K8S_AUTH_KUBECONFIG') | default(lookup('env', 'KUBECONFIG'), true) | default(lookup('env', 'HOME') + '/.kube/config', true) }}"
```
- Chain fallbacks: `K8S_AUTH_KUBECONFIG` → `KUBECONFIG` → `~/.kube/config`

## Role Argument Specifications

**Location:** `meta/argument_specs.yaml` in each role

**Structure:**
```yaml
---
argument_specs:
  main:
    options:
      parameter_name:
        type: str
        required: true
        description: "Parameter description"
      optional_parameter:
        type: list
        elements: dict
        default: []
      choice_parameter:
        type: str
        choices: [present, absent]
```

**Common Types:**
- `str`: String values
- `list`: Lists (specify `elements: dict` or `elements: str`)
- `dict`: Dictionary/object
- `bool`: Boolean (leverage `jinja2_native=True` for unquoted `true`/`false`)

## Template Metadata

**Template Registration (`meta/osac.yaml`):**
```yaml
template_type: cluster  # or compute_instance, network
display_name: "OpenShift 4.17 Small Cluster"
description: "Small OpenShift cluster template"
```
- Used by `osac.service.enumerate_templates` and `osac.service.publish_templates` roles
- Enables fulfillment-service API registration

## Comments and Documentation

**When to Comment:**
- Override points: Indicate whether step is overrideable or critical
- Complex Jinja2 expressions: Explain filter chains
- Workflow phases: Mark major sections (HOOK, PHASE, CRITICAL)
- Workarounds: Document why non-standard approach is needed

**Comment Style:**
```yaml
# Single-line explanation above task
- name: Task description

# CRITICAL: Important architectural note
- name: Non-overrideable task

# PHASE OVERRIDE - Description of override capability
step_name_default:
  name: osac.service.role
  tasks_from: main.yaml
```

**Inline Comments for ansible-lint:**
- `# noqa: name[template]`: Task name uses Jinja2 template
- `# noqa: jinja[invalid]`: Complex Jinja2 expression triggers false positive
- Format: `# noqa: rule[subrule]`

## File Organization

**Collection Structure:**
```
collections/ansible_collections/osac/{collection_name}/
├── galaxy.yml                 # Collection metadata
├── README.md                  # Collection documentation
├── playbooks/                 # Workflow playbooks (workflows collection only)
│   └── {category}/{action}.yml
├── roles/                     # Roles
│   └── {role_name}/
│       ├── defaults/main.yaml       # Default variables
│       ├── meta/
│       │   ├── argument_specs.yaml  # Role parameters
│       │   └── osac.yaml            # Template metadata (templates only)
│       └── tasks/
│           ├── main.yaml            # Primary entry point
│           ├── {action}.yaml        # Action-specific tasks
│           └── noop.yaml            # No-op for hooks
└── plugins/                   # Custom plugins (if any)
    └── README.md
```

**Root-Level Structure:**
```
osac-aap/
├── playbook_osac_*.yml        # EDA entry point playbooks
├── collections/
│   ├── ansible_collections/osac/  # Local collections
│   └── requirements.yml            # Third-party collection dependencies
├── vendor/                    # Vendored collections (not committed)
├── tests/integration/         # Integration tests
├── ansible.cfg                # Ansible configuration
├── pyproject.toml             # Python dependencies (managed by uv)
├── .ansible-lint.yml          # Ansible linting rules
├── .yamllint.yaml             # YAML linting rules
└── .pre-commit-config.yaml    # Git pre-commit hooks
```

---

*Convention analysis: 2026-04-27*
