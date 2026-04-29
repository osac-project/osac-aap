---
phase: 01-windows-vm-provisioning
reviewed: 2026-04-28T00:00:00Z
depth: standard
files_reviewed: 17
files_reviewed_list:
  - collections/ansible_collections/osac/templates/roles/windows_oci_vm/defaults/main.yaml
  - collections/ansible_collections/osac/templates/roles/windows_oci_vm/meta/argument_specs.yaml
  - collections/ansible_collections/osac/templates/roles/windows_oci_vm/meta/osac.yaml
  - collections/ansible_collections/osac/templates/roles/windows_oci_vm/tasks/create_build_spec.yaml
  - collections/ansible_collections/osac/templates/roles/windows_oci_vm/tasks/create_modify_vm_spec.yaml
  - collections/ansible_collections/osac/templates/roles/windows_oci_vm/tasks/create_post_create_hook.yaml
  - collections/ansible_collections/osac/templates/roles/windows_oci_vm/tasks/create_pre_create_hook.yaml
  - collections/ansible_collections/osac/templates/roles/windows_oci_vm/tasks/create_resources.yaml
  - collections/ansible_collections/osac/templates/roles/windows_oci_vm/tasks/create_secrets.yaml
  - collections/ansible_collections/osac/templates/roles/windows_oci_vm/tasks/create_validate.yaml
  - collections/ansible_collections/osac/templates/roles/windows_oci_vm/tasks/create_wait_annotate.yaml
  - collections/ansible_collections/osac/templates/roles/windows_oci_vm/tasks/create.yaml
  - collections/ansible_collections/osac/templates/roles/windows_oci_vm/tasks/delete_post_delete_hook.yaml
  - collections/ansible_collections/osac/templates/roles/windows_oci_vm/tasks/delete_pre_delete_hook.yaml
  - collections/ansible_collections/osac/templates/roles/windows_oci_vm/tasks/delete_resources.yaml
  - collections/ansible_collections/osac/templates/roles/windows_oci_vm/tasks/delete.yaml
  - tests/integration/fixtures/computeinstance-windows-test.yaml
findings:
  critical: 1
  warning: 3
  info: 3
  total: 7
status: issues_found
---

# Phase 01: Code Review Report

**Reviewed:** 2026-04-28T00:00:00Z
**Depth:** standard
**Files Reviewed:** 17
**Status:** issues_found

## Summary

Reviewed the Ansible `windows_oci_vm` role for provisioning Windows VMs on OpenShift Virtualization. The role was created by forking the existing `ocp_virt_vm` role with Windows-specific modifications (sysprep, CloudBase-Init, Hyper-V enlightenments).

**Key concerns identified:**

1. **BLOCKER**: Missing kubeconfig parameter in create_secrets.yaml breaks multi-cluster deployments
2. **WARNING**: Windows hostname truncation logic loses characters silently (should truncate from end, not middle)
3. **WARNING**: Regex validation allows invalid port numbers (0, >65535)
4. **WARNING**: Missing sysprep ConfigMap deletion could leak resources

The role structure and FQCN references are correct (all properly using `osac.templates.windows_oci_vm`). Windows-specific features (Hyper-V enlightenments, sysprep, hostname truncation) are implemented correctly aside from the truncation issue.

## Critical Issues

### CR-01: Missing kubeconfig parameter breaks multi-cluster secret reads

**File:** `collections/ansible_collections/osac/templates/roles/windows_oci_vm/tasks/create_secrets.yaml:50`

**Issue:** The `kubernetes.core.k8s_info` task reads the user-data secret from the ComputeInstance namespace but does not include the `kubeconfig` parameter. This breaks in multi-cluster scenarios where `remote_cluster_kubeconfig` is set, causing the task to read from the local cluster instead of the target cluster.

All other k8s operations correctly use `kubeconfig: "{{ remote_cluster_kubeconfig | default(omit) }}"`, but this one task is missing it.

**Impact:** When provisioning VMs to a remote cluster, the role will fail to find the user-data secret because it looks in the wrong cluster. This is a critical functional bug that breaks a primary use case.

**Fix:**
```yaml
- name: Read user-data secret from ComputeInstance namespace
  kubernetes.core.k8s_info:
    kubeconfig: "{{ remote_cluster_kubeconfig | default(omit) }}"  # ADD THIS LINE
    api_version: v1
    kind: Secret
    name: "{{ vm_user_data_secret_ref }}"
    namespace: "{{ compute_instance.metadata.namespace }}"
  register: user_data_secret
```

## Warnings

### WR-01: Windows hostname truncation logic loses characters incorrectly

**File:** `collections/ansible_collections/osac/templates/roles/windows_oci_vm/tasks/create_validate.yaml:19`

**Issue:** The hostname truncation uses `truncate(15, True, '')` which truncates from the middle of the string (adds ellipsis) when the third parameter is empty. According to Jinja2 docs, when `end=''`, it truncates by removing characters from the middle, not the end.

For a 20-character name like `test-windows-vm-12345`, this produces `test-windows-vm` (15 chars) but for longer names like `very-long-windows-vm-name-12345` (31 chars), it would produce something like `very-long-wind...` which includes the ellipsis marker.

**Expected behavior:** Windows NetBIOS names must be exactly 15 characters or fewer, with characters taken from the START of the name. The correct approach is `name[:15]` to take the first 15 characters.

**Fix:**
```yaml
- name: Extract VM hostname from ComputeInstance metadata
  ansible.builtin.set_fact:
    vm_hostname: "{{ compute_instance.metadata.name[:15] }}"
```

**Additional consideration:** Windows hostnames have character restrictions (alphanumeric and hyphens only, cannot start/end with hyphen). The current implementation doesn't validate this. Consider adding validation or sanitization.

### WR-02: Regex validation allows invalid port numbers

**File:** `collections/ansible_collections/osac/templates/roles/windows_oci_vm/tasks/create_validate.yaml:27-30`

**Issue:** The regex `^([0-9]+/(tcp|udp))(,[0-9]+/(tcp|udp))*$` validates the format but allows invalid port numbers:
- Port 0 (reserved, not valid for user services)
- Ports above 65535 (exceeds TCP/UDP port range)
- No validation for duplicate ports

**Examples that incorrectly pass:**
- `0/tcp` (port 0 is reserved)
- `99999/tcp` (exceeds max port 65535)
- `3389/tcp,3389/tcp` (duplicate port)

**Impact:** Invalid configurations will pass validation but fail when creating Kubernetes Services or may cause unexpected networking behavior.

**Fix:**
```yaml
- name: Validate exposed_ports format
  ansible.builtin.assert:
    that:
      - params.exposed_ports is match('^([0-9]+/(tcp|udp))(,[0-9]+/(tcp|udp))*$')
    fail_msg: "exposed_ports must be in format 'port/protocol' (e.g., '3389/tcp,80/tcp') where protocol is 'tcp' or 'udp'"

- name: Validate port numbers are in valid range
  ansible.builtin.assert:
    that:
      - item.split('/')[0] | int > 0
      - item.split('/')[0] | int <= 65535
    fail_msg: "Port {{ item.split('/')[0] }} is invalid. Ports must be between 1-65535"
  loop: "{{ params.exposed_ports.split(',') }}"
  loop_control:
    label: "{{ item.split('/')[0] }}"
```

### WR-03: Missing resource deletion in cleanup flow

**File:** `collections/ansible_collections/osac/templates/roles/windows_oci_vm/tasks/delete_resources.yaml:135-147`

**Issue:** The delete flow cleans up the sysprep ConfigMap but uses `failed_when` with a lenient condition that suppresses "not found" errors. However, this ConfigMap is ALWAYS created in the create flow (line 2-27 of create_secrets.yaml), so it should always exist during deletion.

The current pattern matches the user-data secret cleanup (which is conditional), but sysprep ConfigMap cleanup should be unconditional.

**Impact:** If the ConfigMap deletion genuinely fails (permissions, API errors, etc.), the error will be suppressed and the resource will leak. This is a minor issue since ConfigMaps are namespace-scoped and will be cleaned up when the namespace is deleted, but it's inconsistent with the create flow.

**Fix:**
```yaml
- name: Delete sysprep ConfigMap
  kubernetes.core.k8s:
    kubeconfig: "{{ remote_cluster_kubeconfig | default(omit) }}"
    api_version: v1
    kind: ConfigMap
    name: "{{ compute_instance_name }}-sysprep"
    namespace: "{{ compute_instance_target_namespace }}"
    state: absent
  # Remove failed_when - ConfigMap should always exist
```

Alternatively, keep the error suppression but add a comment explaining why (e.g., "ConfigMap may not exist if role was interrupted during create").

## Info

### IN-01: Inconsistent YAML file naming convention

**File:** `collections/ansible_collections/osac/templates/roles/windows_oci_vm/tasks/*.yaml`

**Issue:** Task files use `.yaml` extension consistently, which is good. However, the pattern of naming override tasks (e.g., `create_step_secrets_override`, `create_step_resources_override`) uses `tasks_from: create_secrets.yaml` which includes the `.yaml` extension in the variable.

This is technically correct but unusual for Ansible. The `tasks_from` parameter typically omits the extension (Ansible adds it automatically), though explicitly including it also works.

**Current pattern:**
```yaml
tasks_from: create_secrets.yaml
```

**Common pattern:**
```yaml
tasks_from: create_secrets
```

**Recommendation:** Consider standardizing to omit the extension for consistency with common Ansible patterns, or document the explicit extension choice in a role README.

### IN-02: Default port 3389/tcp hardcoded in multiple locations

**File:** Multiple files

**Issue:** The default RDP port `3389/tcp` appears in:
1. `defaults/main.yaml:8` - `exposed_ports: "3389/tcp"`
2. `meta/argument_specs.yaml:44` - `default: "3389/tcp"`

This duplication means the default must be updated in two places if changed. While this is unlikely to change (RDP is standardized), it's still a maintenance concern.

**Recommendation:** Remove the duplicate in `argument_specs.yaml` and rely on the value from `defaults/main.yaml`, or add a comment linking the two:

```yaml
# argument_specs.yaml
default: "3389/tcp"  # Must match default_arg_specs.exposed_ports in defaults/main.yaml
```

### IN-03: Sysprep unattend.xml only sets ComputerName

**File:** `collections/ansible_collections/osac/templates/roles/windows_oci_vm/tasks/create_secrets.yaml:14-27`

**Issue:** The sysprep `Unattend.xml` currently only configures the `ComputerName` in the `specialize` pass. Windows sysprep typically requires additional configuration for a fully automated deployment:

- No `oobeSystem` pass for initial user setup
- No timezone configuration
- No Windows Update settings
- No firewall configuration for RDP

**Current configuration:**
```xml
<settings pass="specialize">
  <component name="Microsoft-Windows-Shell-Setup">
    <ComputerName>{{ vm_hostname }}</ComputerName>
  </component>
</settings>
```

**Impact:** This is not a bug - the minimal sysprep is intentional for templating. However, users may expect more complete Windows configuration. Consider documenting that additional sysprep configuration should be provided via `userDataSecretRef` using CloudBase-Init.

**Recommendation:** Add a comment to the task or role documentation:

```yaml
- name: Create sysprep ConfigMap with unattend.xml for hostname
  # NOTE: This provides minimal sysprep (hostname only). For additional
  # Windows configuration (users, timezone, etc.), use userDataSecretRef
  # with CloudBase-Init cloud-config format.
  kubernetes.core.k8s:
```

---

_Reviewed: 2026-04-28T00:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
