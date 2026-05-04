---
status: complete
phase: 01-windows-vm-provisioning
source:
  - .planning/phases/01-windows-vm-provisioning/01-01-SUMMARY.md
  - .planning/phases/01-windows-vm-provisioning/01-02-SUMMARY.md
  - .planning/phases/01-windows-vm-provisioning/01-03-SUMMARY.md
started: 2026-04-29
updated: 2026-04-29
---

## Current Test

[testing complete]

## Tests

### 1. Role directory structure and FQCN correctness
expected: The windows_oci_vm role has 16 files matching the ocp_virt_vm structure (defaults/, meta/, tasks/). All FQCN references point to osac.templates.windows_oci_vm — zero references to ocp_virt_vm anywhere.
result: pass

### 2. Windows-specific defaults
expected: defaults/main.yaml has exposed_ports: "3389/tcp" (RDP, not SSH), memoryGiB: 4, bootDisk.sizeGiB: 40, and image.sourceRef pointing to a Windows OCI image.
result: pass

### 3. Template discovery metadata
expected: meta/osac.yaml has template_type: compute_instance, allowing the role to be discovered by osac.service.enumerate_templates alongside other templates.
result: pass

### 4. Override pattern orchestration
expected: create.yaml has 6 overrideable steps (secrets, modify_vm_spec, pre_create_hook, resources, post_create_hook, wait_annotate) plus 2 non-overrideable steps (validate, build_spec). Each overrideable step checks for a `*_override` variable and falls back to `*_default`.
result: pass

### 5. Windows hostname truncation
expected: create_validate.yaml extracts hostname from ComputeInstance metadata and truncates to 15 characters (Windows NetBIOS limit). A debug warning is logged when truncation occurs.
result: pass

### 6. Hyper-V enlightenments
expected: create_build_spec.yaml includes the 3 base enlightenments (relaxed, vapic, spinlocks) plus 7 enhanced ones (synic, vpindex, frequencies, reenlightenment, tlbflush, reset, runtime). Windows clock config includes UTC base, HPET disabled, and Hyper-V timer.
result: pass

### 7. Sysprep hostname configuration
expected: create_secrets.yaml creates a ConfigMap named {name}-sysprep containing unattend.xml with a <ComputerName> element set to the truncated hostname. The sysprep disk is mounted as cdrom bus sata (not virtio).
result: pass

### 8. CloudBase-Init user-data delivery
expected: When ComputeInstance spec includes a userDataSecretRef, create_secrets.yaml copies the secret to the VM namespace and mounts it via cloudInitNoCloud volume type with virtio bus.
result: pass

### 9. VM ready wait with extended timeout
expected: create_wait_annotate.yaml waits for VirtualMachine Ready condition with a 900-second timeout (not 600). Display output includes "OS: Windows" and the hostname. ComputeInstance is annotated with reconciled-config-version.
result: pass

### 10. Resource cleanup on delete
expected: delete_resources.yaml cleans up the VirtualMachine, DataVolumes, and the sysprep ConfigMap. Sysprep cleanup uses soft-fail pattern (ignores "not found" errors).
result: issue
reported: "delete_resources.yaml contained orphaned delete tasks for SSH key secret ({name}-ssh-public-key) and cloud-init secret ({name}-cloud-init) that are never created by the Windows VM role. These were copied from ocp_virt_vm but Windows uses RDP, not SSH, and creates user-data not cloud-init secrets."
severity: major
fix: "Removed both orphaned delete tasks from delete_resources.yaml. Fix applied inline during UAT."

### 11. Port validation
expected: create_validate.yaml validates exposed_ports format (port/protocol, e.g. "3389/tcp"). Invalid port ranges or formats are rejected with a clear error.
result: pass

### 12. Windows test fixture
expected: tests/integration/fixtures/computeinstance-windows-test.yaml exists with templateID: osac.templates.windows_oci_vm, memoryGiB: 4, bootDisk.sizeGiB: 40, and name under 15 characters.
result: pass

## Summary

total: 12
passed: 11
issues: 1
skipped: 0

## Gaps

- truth: "delete_resources.yaml only cleans up resources actually created by the Windows VM role"
  status: fixed
  reason: "Orphaned SSH key and cloud-init secret delete tasks removed during UAT"
  severity: major
  test: 10
  artifacts:
    - collections/ansible_collections/osac/templates/roles/windows_oci_vm/tasks/delete_resources.yaml
  missing: []
