---
phase: 01-windows-vm-provisioning
fixed_at: 2026-04-28T00:00:00Z
review_path: .planning/phases/01-windows-vm-provisioning/01-REVIEW.md
iteration: 1
findings_in_scope: 4
fixed: 4
skipped: 0
status: all_fixed
---

# Phase 01: Code Review Fix Report

**Fixed at:** 2026-04-28T00:00:00Z
**Source review:** .planning/phases/01-windows-vm-provisioning/01-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 4
- Fixed: 4
- Skipped: 0

## Fixed Issues

### CR-01: Missing kubeconfig parameter breaks multi-cluster secret reads

**Files modified:** `collections/ansible_collections/osac/templates/roles/windows_oci_vm/tasks/create_secrets.yaml`
**Commit:** 2bfdede
**Applied fix:** Added missing `kubeconfig: "{{ remote_cluster_kubeconfig | default(omit) }}"` parameter to the k8s_info task that reads user-data secret from ComputeInstance namespace. This fixes multi-cluster deployments where remote_cluster_kubeconfig is set, ensuring the task reads from the target cluster instead of the local cluster.

### WR-01: Windows hostname truncation logic loses characters incorrectly

**Files modified:** `collections/ansible_collections/osac/templates/roles/windows_oci_vm/tasks/create_validate.yaml`
**Commit:** b43ea31
**Applied fix:** Replaced `truncate(15, True, '')` with string slicing `[:15]` to properly truncate Windows hostname from the start instead of the middle. Windows NetBIOS names must be exactly 15 characters or fewer, with characters taken from the START of the name. The previous implementation would remove characters from the middle of long names.

### WR-02: Regex validation allows invalid port numbers

**Files modified:** `collections/ansible_collections/osac/templates/roles/windows_oci_vm/tasks/create_validate.yaml`
**Commit:** e55c13b
**Applied fix:** Added validation task to ensure port numbers in exposed_ports are in the valid range (1-65535). The existing regex only validated the format but allowed invalid ports like 0 or 99999. This prevents invalid configurations from passing validation and failing later when creating Kubernetes Services.

### WR-03: Missing resource deletion in cleanup flow

**Files modified:** `collections/ansible_collections/osac/templates/roles/windows_oci_vm/tasks/delete_resources.yaml`
**Commit:** 141f76b
**Applied fix:** Removed `failed_when` clause from sysprep ConfigMap deletion task. Since this resource is always created during the create flow (not conditional like user-data secret), the error suppression was unnecessary and could hide genuine deletion failures (permissions, API errors). This ensures errors are properly surfaced.

---

_Fixed: 2026-04-28T00:00:00Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
