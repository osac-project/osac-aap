---
phase: 01-windows-vm-provisioning
fixed_at: 2026-05-03T00:00:00Z
review_path: .planning/phases/01-windows-vm-provisioning/01-REVIEW.md
iteration: 1
findings_in_scope: 3
fixed: 2
skipped: 1
status: partial
---

# Phase 01: Code Review Fix Report

**Fixed at:** 2026-05-03T00:00:00Z
**Source review:** .planning/phases/01-windows-vm-provisioning/01-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 3 (WR-01, WR-02, WR-03; IN-01 excluded per fix_scope=critical_warning)
- Fixed: 2
- Skipped: 1

## Fixed Issues

### WR-01: `argument_specs.yaml` `exposed_ports` default is wrong for Windows — spec `default` field is always `22/tcp`

**Files modified:** `collections/ansible_collections/osac/templates/roles/ocp_virt_vm/meta/argument_specs.yaml`
**Commit:** c2ee834
**Applied fix:** Added a multi-line YAML comment immediately above `default: "22/tcp"` (lines 57-61) explaining that this is intentionally the static Linux fallback value, that Windows gets overridden to `3389/tcp` at runtime via `create_validate.yaml` merging `default_arg_specs` before the argument-spec default is ever consulted, and warning future maintainers not to change this value without auditing the Windows override path. The `default: "22/tcp"` value itself was left unchanged as instructed.

### WR-02: `delete_resources.yaml` deletes load-balancer Service that is never created by the default create flow

**Files modified:** `collections/ansible_collections/osac/templates/roles/ocp_virt_vm/tasks/delete_resources.yaml`
**Commit:** fdf71a8
**Applied fix:** Added a `register: delete_lb_service` and a `failed_when` guard to the "Delete VM load balancer service" task (lines 70-74) matching the exact pattern used by the Secret and ConfigMap delete tasks in the same file. Also added a task-level comment explaining that the Service is only created when a post-create hook provisions one, and does not exist in the default create flow. This resolves the latent reliability bug where an RBAC denial or other unexpected API error would fail the playbook without any guard.

## Skipped Issues

### WR-03: `delete_resources.yaml` delete order — VirtualMachine deleted before secrets/ConfigMap, but Wait-for-stop condition uses `VirtualMachineInstance` not `VirtualMachine`

**File:** `collections/ansible_collections/osac/templates/roles/ocp_virt_vm/tasks/delete_resources.yaml:33-45`
**Reason:** Skipped per explicit instruction — this is a complex KubeVirt race condition fix that would replace the existing `VirtualMachine` Ready=False wait with a `VirtualMachineInstance` disappearance poll. This is a meaningful behavioral change in the VM stop/delete sequencing that must be verified against a live KubeVirt environment to ensure the new wait condition does not introduce its own race (e.g., a VMI that is being created by KubeVirt's runStrategy reconciler after the Halted patch). The fix requires human review and testing before application.
**Original issue:** The "Wait for VM to stop" task (lines 33-45) waits on the `VirtualMachine` resource for `Ready=False`, but it is gated on `vm_exists.resources | length > 0` which checked for a `VirtualMachineInstance`. These are two different resources; the safer pattern is to wait for the VMI to disappear before issuing the VM delete, to avoid KubeVirt rejecting the delete while a VMI is still running.

---

_Fixed: 2026-05-03T00:00:00Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
