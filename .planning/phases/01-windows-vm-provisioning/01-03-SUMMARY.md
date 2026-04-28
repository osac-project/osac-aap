---
phase: 01-windows-vm-provisioning
plan: 03
subsystem: testing
tags: [test-fixtures, integration-testing, windows-vm, role-verification]
requirements: [PROV-01, PROV-02, PROV-03, PROV-04, PROV-05]

dependency_graph:
  requires:
    - 01-02-PLAN.md (complete windows_oci_vm role)
  provides:
    - Windows ComputeInstance test fixture for integration tests
  affects:
    - tests/integration/targets/compute_instance_create (can test Windows VMs)

tech_stack:
  added: []
  patterns:
    - Test fixture pattern matching existing Linux fixtures
    - YAML resource definition for Kubernetes CRD

key_files:
  created:
    - tests/integration/fixtures/computeinstance-windows-test.yaml
  modified: []

decisions:
  - what: Use test-windows-vm as fixture name (under 15 chars)
    why: Avoids hostname truncation complications in test scenarios
    alternatives: Could use longer name that triggers truncation warning
    outcome: Clean test fixture with no hostname warnings

metrics:
  duration: 4 minutes
  tasks_completed: 2
  files_created: 1
  commits: 1
  completed_date: 2026-04-28
---

# Phase 01 Plan 03: Windows Test Fixture and Final Verification Summary

**One-liner:** Created Windows ComputeInstance test fixture and verified complete 16-file windows_oci_vm role with all Windows-specific features (RDP port, hostname truncation, clock config, enhanced Hyper-V, sysprep with sata bus, 900s timeout).

## What Was Built

### Test Fixture
Created `tests/integration/fixtures/computeinstance-windows-test.yaml` following the exact pattern of the existing Linux fixture (`computeinstance-test.yaml`) with Windows-specific values:

- **templateID**: `osac.templates.windows_oci_vm` (triggers Windows template dispatch)
- **name**: `test-windows-vm` (unique name, under 15 chars to avoid truncation)
- **memoryGiB**: 4 (matches Windows default)
- **bootDisk.sizeGiB**: 40 (Windows requires larger disk than Linux's 20GiB)
- **image.sourceRef**: `quay.io/containerdisks/windows:ltsc2022` (Windows OCI image)

### Role Verification
Verified the complete `windows_oci_vm` role structure created by plans 01 and 02:

**16 files total** (matching ocp_virt_vm structure):
- 3 config files: defaults/main.yaml, meta/argument_specs.yaml, meta/osac.yaml
- 13 task files: create.yaml, delete.yaml, + 11 granular step files

**Windows-specific features confirmed**:
- RDP port (3389/tcp) in default exposed_ports
- Hostname extraction with 15-character truncation (Windows NetBIOS limit)
- Windows clock configuration (UTC base, HPET disabled, Hyper-V timer)
- Enhanced Hyper-V enlightenments (synic, vpindex, frequencies, reenlightenment, tlbflush, reset, runtime)
- Sysprep ConfigMap with unattend.xml for hostname setting
- Sysprep disk uses cdrom bus sata (required for Windows Setup)
- VM wait timeout of 900 seconds (Windows boot + sysprep takes longer than Linux)
- Sysprep ConfigMap cleanup in delete flow

**FQCN correctness**:
- 8 references to `osac.templates.windows_oci_vm` in create.yaml (override points + role name)
- 3 references to `osac.templates.windows_oci_vm` in delete.yaml (override points)
- Zero references to `ocp_virt_vm` anywhere in the role (no copy-paste errors)

## Task Breakdown

### Task 1: Create Windows test fixture ✓
**Duration:** 2 minutes  
**Files created:** 1

Created `tests/integration/fixtures/computeinstance-windows-test.yaml` with Windows-appropriate sizing and OCI image reference. The fixture enables integration tests to exercise the Windows template using the same override-based testing pattern as existing Linux tests.

**Commit:** 2209f91 - `feat(01-03): add Windows ComputeInstance test fixture`

### Task 2: Final role verification ✓
**Duration:** 2 minutes  
**Files created:** 0 (verification only)

Ran comprehensive verification of the complete windows_oci_vm role created by prior plans:
- File count check: 16 files ✓
- Filename parity with ocp_virt_vm: identical filenames ✓
- Zero ocp_virt_vm references: clean FQCN usage ✓
- FQCN counts: 8 in create.yaml, 3 in delete.yaml ✓
- Windows-specific content: all features present ✓
- Test fixture: correct templateID ✓

No files created or modified - this was a verification-only task to confirm the role is structurally complete and free of errors.

## Deviations from Plan

### Wave Dependency Resolution

**1. [Rule 3 - Blocking] Merged wave 1 and wave 2 commits**
- **Found during:** Task 2 verification
- **Issue:** Worktree started at planning base commit (b785a00) without wave 1 and wave 2 execution artifacts. Role directory didn't exist, blocking verification.
- **Fix:** Merged commits from completed waves: 9f6cb9c (wave 1 task 1), 04afe16 (wave 1 task 2), 9844bcb (wave 2 task 1), c37280f (wave 2 task 2). This brought in all 16 role files required for verification.
- **Files affected:** All files in collections/ansible_collections/osac/templates/roles/windows_oci_vm/
- **Rationale:** Wave 3 depends on wave 2 (explicit `depends_on: [02]` in plan frontmatter). In parallel worktree execution, each worktree starts from the same base commit and must merge dependencies before proceeding. This is normal parallel wave behavior - not a true deviation.

No other deviations. Plan executed exactly as written.

## Integration Points

### Test Fixture → Template Dispatch
The `spec.templateID: osac.templates.windows_oci_vm` field in the test fixture determines which role is invoked when the compute_instance/create workflow processes the ComputeInstance resource. The fixture can be loaded in integration tests via:

```yaml
- name: Read ComputeInstance fixture
  ansible.builtin.set_fact:
    test_compute_instance: "{{ lookup('file', '../../../fixtures/computeinstance-windows-test.yaml') | from_yaml }}"
```

### Role Structure Parity
The windows_oci_vm role matches the ocp_virt_vm structure exactly (same 16 filenames in same directory layout), enabling:
- Consistent workflow integration (same override points)
- Parallel testing patterns (same test invocation)
- Maintainability (developers familiar with ocp_virt_vm can navigate windows_oci_vm)

## Verification Results

All success criteria met:

- ✓ Test fixture exists at tests/integration/fixtures/computeinstance-windows-test.yaml
- ✓ Fixture has templateID=osac.templates.windows_oci_vm, memoryGiB=4, bootDisk.sizeGiB=40
- ✓ Complete role has 16 files matching ocp_virt_vm file names
- ✓ Zero ocp_virt_vm references anywhere in the role
- ✓ All Windows-specific features verified:
  - ✓ RDP port (3389/tcp)
  - ✓ Hostname truncation (15 chars)
  - ✓ Clock config (UTC, HPET disabled, Hyper-V timer)
  - ✓ Enhanced Hyper-V enlightenments (8 additional features)
  - ✓ Sysprep sata bus (cdrom, not disk)
  - ✓ 900s wait timeout (not 600s)
  - ✓ Sysprep cleanup in delete flow

**Self-Check: PASSED**

All claimed files exist:
- FOUND: tests/integration/fixtures/computeinstance-windows-test.yaml

All claimed commits exist:
- FOUND: 2209f91 (feat(01-03): add Windows ComputeInstance test fixture)

## Known Stubs

None. The test fixture is a complete, ready-to-use YAML file with no placeholders or stubs. All fields have concrete values appropriate for Windows VM testing.

## Threat Flags

None. The test fixture is a static file used only in integration test environments. The templateID value is hardcoded and not user-controlled in test context (matches threat register T-01-06 "accept" disposition).

## Next Steps

**Immediate:**
1. Use the Windows test fixture in integration test development for `tests/integration/targets/compute_instance_create/`
2. Verify the complete role deploys successfully in a test cluster
3. Validate Windows VM boots from OCI image and responds to RDP/VNC

**Future phases:**
- Phase 2: Integration testing and deployment verification (per ROADMAP.md)
- Post-v1: Advanced Windows features (domain join, licensing, custom scripts)

## Files Created

1. **tests/integration/fixtures/computeinstance-windows-test.yaml** (18 lines)
   - Windows ComputeInstance test fixture
   - Enables integration testing of windows_oci_vm template
   - Follows existing test fixture pattern

## Commits

| Hash    | Type | Message                                              | Files |
|---------|------|------------------------------------------------------|-------|
| 2209f91 | feat | Add Windows ComputeInstance test fixture            | 1     |

## Related Documentation

- Plan: .planning/phases/01-windows-vm-provisioning/01-03-PLAN.md
- Context: .planning/phases/01-windows-vm-provisioning/01-CONTEXT.md
- Research: .planning/phases/01-windows-vm-provisioning/01-RESEARCH.md
- Wave 1 Summary: .planning/phases/01-windows-vm-provisioning/01-01-SUMMARY.md (expected)
- Wave 2 Summary: .planning/phases/01-windows-vm-provisioning/01-02-SUMMARY.md (expected)
