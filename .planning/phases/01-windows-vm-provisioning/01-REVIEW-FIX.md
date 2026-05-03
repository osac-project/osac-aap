---
phase: 01-windows-vm-provisioning
fixed_at: 2026-05-03T01:00:00Z
review_path: .planning/phases/01-windows-vm-provisioning/01-REVIEW.md
iteration: 2
findings_in_scope: 3
fixed: 3
skipped: 0
status: all_fixed
---

# Phase 01: Code Review Fix Report

**Fixed at:** 2026-05-03T01:00:00Z
**Source review:** .planning/phases/01-windows-vm-provisioning/01-REVIEW.md
**Iteration:** 2

**Summary:**
- Findings in scope: 3 (WR-01, WR-02, WR-03; IN-01 excluded per fix_scope=critical_warning)
- Fixed: 3
- Skipped: 0

## Fixed Issues

### WR-01: `argument_specs.yaml` `exposed_ports` default is wrong for Windows — spec `default` field is always `22/tcp`

**Files modified:** `collections/ansible_collections/osac/templates/roles/ocp_virt_vm/meta/argument_specs.yaml`
**Commit:** c2ee834 (iteration 1)
**Status:** Already fixed in iteration 1.
**Applied fix:** Added a multi-line YAML comment above `default: "22/tcp"` explaining it is intentionally the static Linux fallback, that Windows gets overridden to `3389/tcp` at runtime via `create_validate.yaml` merging `default_arg_specs` before the argument-spec default is consulted, and warning future maintainers not to change this value without auditing the Windows override path. The description was also updated to document the OS-dependent runtime default explicitly.

### WR-02: `delete_resources.yaml` deletes load-balancer Service that is never created by the default create flow

**Files modified:** `collections/ansible_collections/osac/templates/roles/ocp_virt_vm/tasks/delete_resources.yaml`
**Commit:** fdf71a8 (iteration 1)
**Status:** Already fixed in iteration 1.
**Applied fix:** Added `register: delete_lb_service` and a `failed_when` guard to the "Delete VM load balancer service" task, matching the pattern used by other Secret and ConfigMap delete tasks in the same file. Added a task-level comment explaining the Service is only created when a post-create hook provisions one, clarifying this is not part of the default create flow.

### WR-03: `delete_resources.yaml` delete order — VirtualMachine deleted before secrets/ConfigMap, but Wait-for-stop condition uses `VirtualMachineInstance` not `VirtualMachine`

**Files modified:** `collections/ansible_collections/osac/templates/roles/ocp_virt_vm/tasks/delete_resources.yaml`
**Commit:** 7734c01 (iteration 2)
**Status:** fixed: requires human verification
**Applied fix:** Replaced the "Wait for VM to stop" task (which polled `VirtualMachine` Ready=False via `wait_condition`) with a "Wait for VirtualMachineInstance to stop" task that polls `VirtualMachineInstance` resources until none remain (`vmi_stopped.resources | length == 0`). The new task uses `retries: 60` and `delay: 5` for a 5-minute maximum wait, consistent with the previous `wait_timeout: 300`. The `when: vm_exists.resources | length > 0` gate is preserved. This closes the race window where KubeVirt rejects a VM delete while its VMI is still live — a `VirtualMachine` with `runStrategy: Halted` can reach `Ready=False` before the VMI has fully terminated.

---

_Fixed: 2026-05-03T01:00:00Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 2_
