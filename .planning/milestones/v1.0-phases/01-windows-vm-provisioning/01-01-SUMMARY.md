---
phase: 01-windows-vm-provisioning
plan: 01
subsystem: osac.templates
tags: [infrastructure, ansible-roles, windows, vm-provisioning]
dependency_graph:
  requires: []
  provides:
    - windows_oci_vm role directory structure
    - Windows-specific configuration defaults
    - Override-pattern orchestration files
  affects:
    - osac.templates collection (adds windows_oci_vm template)
tech_stack:
  added:
    - collections/ansible_collections/osac/templates/roles/windows_oci_vm
  patterns:
    - Ansible role structure (defaults/, meta/, tasks/)
    - Override pattern for workflow customization
    - OSAC template discovery via meta/osac.yaml
key_files:
  created:
    - collections/ansible_collections/osac/templates/roles/windows_oci_vm/defaults/main.yaml
    - collections/ansible_collections/osac/templates/roles/windows_oci_vm/meta/argument_specs.yaml
    - collections/ansible_collections/osac/templates/roles/windows_oci_vm/meta/osac.yaml
    - collections/ansible_collections/osac/templates/roles/windows_oci_vm/tasks/create.yaml
    - collections/ansible_collections/osac/templates/roles/windows_oci_vm/tasks/delete.yaml
    - collections/ansible_collections/osac/templates/roles/windows_oci_vm/tasks/create_modify_vm_spec.yaml
    - collections/ansible_collections/osac/templates/roles/windows_oci_vm/tasks/create_pre_create_hook.yaml
    - collections/ansible_collections/osac/templates/roles/windows_oci_vm/tasks/create_post_create_hook.yaml
    - collections/ansible_collections/osac/templates/roles/windows_oci_vm/tasks/delete_pre_delete_hook.yaml
    - collections/ansible_collections/osac/templates/roles/windows_oci_vm/tasks/delete_post_delete_hook.yaml
  modified: []
decisions: []
metrics:
  duration_minutes: 3.0
  tasks_completed: 2
  files_created: 10
  commits: 2
  completed_date: "2026-04-28"
---

# Phase 01 Plan 01: Role Skeleton Creation Summary

**One-liner:** Created windows_oci_vm role directory structure with Windows-specific defaults (RDP port 3389, 4GiB RAM, 40GiB disk) and override-pattern orchestration files copied from ocp_virt_vm with FQCN updates.

## What Was Built

Established the complete windows_oci_vm template role skeleton with 10 files across three directories (defaults/, meta/, tasks/). The role follows the established OSAC pattern by copying the proven ocp_virt_vm structure and making two targeted modifications: (1) replacing all FQCN references from ocp_virt_vm to windows_oci_vm in orchestration files, and (2) updating configuration defaults to Windows-specific values (RDP instead of SSH, larger RAM and disk for Windows workloads).

The role is now discoverable by osac.service.enumerate_templates via the template_type: compute_instance metadata in meta/osac.yaml. However, the role is not yet functional — it references 6 substantive task files (create_validate.yaml, create_build_spec.yaml, create_secrets.yaml, create_resources.yaml, create_wait_annotate.yaml, delete_resources.yaml) that will be created in Plan 02.

## Tasks Completed

### Task 1: Create role config files (defaults, meta)
**Commit:** 9f6cb9c  
**Files:** defaults/main.yaml, meta/argument_specs.yaml, meta/osac.yaml

Created three configuration files with Windows-specific defaults:
- **defaults/main.yaml**: Changed exposed_ports from 22/tcp (SSH) to 3389/tcp (RDP), memoryGiB from 2 to 4, bootDisk.sizeGiB from 10 to 40, and image.sourceRef to quay.io/containerdisks/windows:ltsc2022
- **meta/argument_specs.yaml**: Updated exposed_ports parameter default to 3389/tcp and example to '3389/tcp,80/tcp'
- **meta/osac.yaml**: Set title to "Windows OCI VM ComputeInstance Template" with description mentioning CloudBase-Init and Hyper-V enlightenments; preserved template_type: compute_instance for OSAC discovery

All other fields (cores: 2, default_vm_internal_network: "hypershift", default_vm_storage_class: "nfs-client", runStrategy: "Always") remain identical to ocp_virt_vm.

### Task 2: Create orchestration files (create.yaml, delete.yaml) and no-op hooks
**Commit:** 04afe16  
**Files:** tasks/create.yaml, tasks/delete.yaml, tasks/create_modify_vm_spec.yaml, tasks/create_pre_create_hook.yaml, tasks/create_post_create_hook.yaml, tasks/delete_pre_delete_hook.yaml, tasks/delete_post_delete_hook.yaml

Created 7 task files:
- **tasks/create.yaml**: 80-line orchestration file with 8 FQCN references to osac.templates.windows_oci_vm (6 override step defaults + 2 non-overrideable validate/build_spec steps)
- **tasks/delete.yaml**: 45-line orchestration file with 3 FQCN references to osac.templates.windows_oci_vm (3 override step defaults)
- **5 no-op hook files**: Verbatim copies from ocp_virt_vm providing override points for VM spec customization (create_modify_vm_spec.yaml) and pre/post-create/delete custom logic

Verified zero occurrences of "ocp_virt_vm" remain in the entire windows_oci_vm role directory — all FQCN references correctly point to the new role name.

## Deviations from Plan

None - plan executed exactly as written.

## Known Stubs

None. The no-op hook files are intentional placeholders for the override pattern, not stubs. The missing substantive task files (create_validate.yaml, etc.) are out of scope for this plan and will be created in Plan 02.

## Verification Results

All verification criteria passed:

```
Complete directory structure: 10 files created
Zero ocp_virt_vm references: 0 occurrences
Windows defaults confirmed:
  - exposed_ports: "3389/tcp"
  - memoryGiB: 4
  - bootDisk.sizeGiB: 40
Template discovery metadata: template_type: compute_instance
```

FQCN counts verified:
- create.yaml: 8 occurrences of osac.templates.windows_oci_vm
- delete.yaml: 3 occurrences of osac.templates.windows_oci_vm

## Self-Check: PASSED

All created files verified to exist:
- ✓ defaults/main.yaml
- ✓ meta/argument_specs.yaml
- ✓ meta/osac.yaml
- ✓ tasks/create.yaml
- ✓ tasks/delete.yaml
- ✓ tasks/create_modify_vm_spec.yaml
- ✓ tasks/create_pre_create_hook.yaml
- ✓ tasks/create_post_create_hook.yaml
- ✓ tasks/delete_pre_delete_hook.yaml
- ✓ tasks/delete_post_delete_hook.yaml

All commits verified to exist:
- ✓ 9f6cb9c: feat(01-01): create windows_oci_vm role config files
- ✓ 04afe16: feat(01-01): create windows_oci_vm orchestration and hook files

## Next Steps

Plan 02 will create the 6 substantive task files that provide the actual Windows VM provisioning logic:
- create_validate.yaml (parameter validation)
- create_build_spec.yaml (VirtualMachine spec construction)
- create_secrets.yaml (Windows user-data and credential generation)
- create_resources.yaml (DataVolume and VirtualMachine creation)
- create_wait_annotate.yaml (wait for VM ready, annotate ComputeInstance)
- delete_resources.yaml (cleanup VirtualMachine, DataVolumes, Secrets)

The role skeleton created in this plan provides the complete directory structure and orchestration wiring for those substantive tasks to plug into.
