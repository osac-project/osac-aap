---
phase: 01-windows-vm-provisioning
reviewed: 2026-05-03T00:00:00Z
depth: standard
files_reviewed: 2
files_reviewed_list:
  - collections/ansible_collections/osac/templates/roles/ocp_virt_vm/meta/argument_specs.yaml
  - collections/ansible_collections/osac/templates/roles/ocp_virt_vm/tasks/delete_resources.yaml
findings:
  critical: 0
  warning: 3
  info: 1
  total: 4
status: issues_found
---

# Phase 01: Code Review Report

**Reviewed:** 2026-05-03T00:00:00Z
**Depth:** standard
**Files Reviewed:** 2
**Status:** issues_found

## Summary

Reviewed two files from the `ocp_virt_vm` Ansible role:

- `argument_specs.yaml`: Adds an OS-dependent default note to the `exposed_ports` description.
- `delete_resources.yaml`: Removes an orphaned "Delete cloud-init secret" task; adds OS-conditional cleanup for Linux SSH key Secret and Windows sysprep ConfigMap.

Cross-referencing against `create_secrets.yaml`, `create_resources.yaml`, `create_build_spec.yaml`, `defaults/main.yaml`, and the full create/delete flow revealed the following issues.

---

## Warnings

### WR-01: `argument_specs.yaml` `exposed_ports` default is wrong for Windows — spec `default` field is always `22/tcp`

**File:** `collections/ansible_collections/osac/templates/roles/ocp_virt_vm/meta/argument_specs.yaml:57`

**Issue:** The `description` (lines 51–54) correctly states that the default for Windows is `3389/tcp` and the default for Linux is `22/tcp`. However, the machine-readable `default` field on line 57 is hard-coded to `"22/tcp"`. Ansible's module documentation and tooling (e.g., `ansible-doc`, AAP survey generation, role argument validation) read `default` as the authoritative fallback value for the parameter — not the description text. When a Windows VM is provisioned without an explicit `exposed_ports`, `create_validate.yaml` (line 10) merges `default_arg_specs` into `template_parameters`, and `default_arg_specs` for Windows is correctly overridden to `3389/tcp` in `defaults/main.yaml`. But the spec `default` being `22/tcp` is misleading: any tool or operator reading the spec to understand what the default is for Windows will get the wrong answer. More critically, if the argument-spec default were ever used as a fallback before the `set_fact` override runs, a Windows VM would receive `22/tcp` instead of `3389/tcp`, which would expose the wrong port and silently misconfigure the load balancer Service selector.

The correct fix is to document that there is no single static default — it is OS-dependent — and either:
1. Remove the `default` field from the spec and require callers to always supply it (or rely on the runtime merge in `create_validate.yaml`), or
2. Set `default` to the Linux value and make the description note that `create.yaml` overrides this for Windows at runtime.

Option 2 is the minimal safe change if the runtime override is always guaranteed to run first:

```yaml
exposed_ports:
  description: >
    Ports to expose on the VM for ingress traffic.
    The syntax is a comma-separated list of `<port>/<protocol>` pairs, where `<protocol>` is either `tcp` or `udp`.
    For example, `22/tcp,80/tcp` will expose tcp ports 22 and 80 on the VM.
    Runtime default: `22/tcp` for Linux; `3389/tcp` for Windows (overridden at runtime via
    `guest_os_family` before this argument-spec default is consulted).
  type: str
  required: false
  default: "22/tcp"
```

Add a comment in the file making the ordering dependency explicit so a future maintainer does not break it.

---

### WR-02: `delete_resources.yaml` deletes load-balancer Service that is never created by the default create flow

**File:** `collections/ansible_collections/osac/templates/roles/ocp_virt_vm/tasks/delete_resources.yaml:58-65`

**Issue:** The task "Delete VM load balancer service" (lines 58–65) unconditionally attempts to delete a Service named `{{ compute_instance_name }}-load-balancer`. Searching the entire `ocp_virt_vm` role, this Service is never created by the default create flow (not in `create_resources.yaml`, `create_secrets.yaml`, `create_build_spec.yaml`, or any hook). This task therefore succeeds only if the Service was injected by an external caller that overrides a create hook, or fails silently if the `kubernetes.core.k8s` module returns no error on absent resources.

The risk is twofold:

1. **Silent no-op in the normal case.** Every deletion run issues an API call against a non-existent resource. This is benign in isolation but represents dead logic that will mislead future maintainers into thinking a load-balancer Service is part of the standard provisioned resource set.

2. **No `failed_when` guard.** All other Secret and ConfigMap delete tasks in this file include a `failed_when` guard that ignores "not found" errors (lines 102–105, 116–119, 131–134). The load-balancer Service delete task has no such guard. If the Kubernetes API returns an unexpected error (e.g., RBAC denial), the task will fail the playbook. The inconsistency is a latent reliability bug.

**Fix:** Either remove the task entirely if the load-balancer Service is never created by this role's default flow, or add a `failed_when` guard consistent with the other delete tasks and add a comment explaining which create hook is expected to create this resource:

```yaml
- name: Delete VM load balancer service
  kubernetes.core.k8s:
    kubeconfig: "{{ remote_cluster_kubeconfig | default(omit) }}"
    api_version: v1
    kind: Service
    name: "{{ compute_instance_name }}-load-balancer"
    namespace: "{{ compute_instance_target_namespace }}"
    state: absent
  register: delete_lb_service
  failed_when:
    - delete_lb_service.failed is defined
    - delete_lb_service.failed
    - "'not found' not in (delete_lb_service.msg | default(''))"
```

---

### WR-03: `delete_resources.yaml` delete order — VirtualMachine deleted before secrets/ConfigMap, but Wait-for-stop condition uses `VirtualMachineInstance` not `VirtualMachine`

**File:** `collections/ansible_collections/osac/templates/roles/ocp_virt_vm/tasks/delete_resources.yaml:33-45`

**Issue:** The "Wait for VM to stop" task (lines 33–45) waits on the `VirtualMachine` resource for `Ready=False`. It is gated on `vm_exists.resources | length > 0` which checked whether a `VirtualMachineInstance` exists (lines 11–19). These are two different resources — a `VirtualMachine` can exist without a running `VirtualMachineInstance` (e.g., `runStrategy: Halted`). If a VM was created but is already halted:

- `vm_exists.resources | length == 0` (no VMI) → both "Stop VirtualMachine" and "Wait for VM to stop" are skipped (correct, no race).
- But if a VMI exists and the `runStrategy` is set to `Halted` (patch applied on line 21), there is a window between patch and the VMI terminating during which the `VirtualMachine` may still report `Ready=True`. The wait condition waits for `Ready=False`, which is correct. However, the `wait_timeout: 300` on the wait task and the VirtualMachine delete task (line 55) also carry `wait: true` and `wait_timeout: 300`. If the VMI termination is slow (busy node), the delete task at line 47 may race with the VMI still running, which KubeVirt will reject — causing the delete task to fail.

The safer pattern is to wait for the `VirtualMachineInstance` to disappear (not just for the `VirtualMachine` Ready condition to go False) before issuing the delete:

```yaml
- name: Wait for VirtualMachineInstance to stop
  kubernetes.core.k8s_info:
    kubeconfig: "{{ remote_cluster_kubeconfig | default(omit) }}"
    api_version: kubevirt.io/v1
    kind: VirtualMachineInstance
    name: "{{ compute_instance_name }}"
    namespace: "{{ compute_instance_target_namespace }}"
  register: vmi_stopped
  until: vmi_stopped.resources | length == 0
  retries: 60
  delay: 5
  when: vm_exists.resources | length > 0
```

This avoids the subtle race between KubeVirt rejecting a VM delete while a VMI is still live.

---

## Info

### IN-01: `delete_resources.yaml` "Display deletion status" debug message is always optimistic

**File:** `collections/ansible_collections/osac/templates/roles/ocp_virt_vm/tasks/delete_resources.yaml:137-143`

**Issue:** The final debug task (lines 137–143) unconditionally prints `"All associated resources have been removed"` regardless of whether the individual delete tasks registered failures or skipped resources. If the playbook ever reaches this task after a `failed_when` guard absorbed an error, the message will be misleading in logs. This is a minor quality issue — the message should either be removed or reflect only the completion of the task list (not assert correctness of all deletions).

**Fix:** Rephrase to reflect task completion rather than asserting resource state:

```yaml
- name: Display deletion status
  ansible.builtin.debug:
    msg:
      - "Virtual Machine '{{ compute_instance_name }}' deletion tasks completed"
      - "Namespace: {{ compute_instance_target_namespace }}"
```

---

_Reviewed: 2026-05-03T00:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
