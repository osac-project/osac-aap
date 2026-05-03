# Milestones

Release history for Windows VM Provisioning for OpenShift Virtualization.

## Completed

### v1.0 — Windows VM Provisioning (Shipped: 2026-04-29)

**Started:** 2026-04-28
**Shipped:** 2026-04-29
**Phases:** 1 | **Plans:** 3 | **Tasks:** 6

**Key accomplishments:**

1. Created `windows_oci_vm` template role (16 files) following the proven `ocp_virt_vm` pattern with Windows-specific adaptations
2. Implemented Windows hostname setting via sysprep unattend.xml with 15-character NetBIOS truncation
3. Added enhanced Hyper-V enlightenments (10 features) and Windows clock configuration for optimal guest performance
4. Delivered CloudBase-Init user-data support via cloudInitNoCloud volume type
5. Created Windows ComputeInstance test fixture for integration testing

**Key decisions:**

- `implementationStrategy: windows_oci_vm` — clear, descriptive routing name
- Follow `ocp_virt_vm` pattern — proven architecture, reduced risk
- Sysprep disk as SATA CD-ROM — required by Windows Setup
- 900s VM ready timeout — accommodates Windows first boot + sysprep
- Phase 2 (deeper VM verification) removed — basic Ready state wait matches Linux pattern, deeper checks deferred to v2

**Archive:** [v1.0-ROADMAP.md](milestones/v1.0-ROADMAP.md) | [v1.0-REQUIREMENTS.md](milestones/v1.0-REQUIREMENTS.md)

### v1.1 — ocp_virt_vm Consolidation (Shipped: 2026-05-02)

**Started:** 2026-05-02
**Shipped:** 2026-05-02
**Phases:** 1 | **Plans:** 3 | **Tasks:** 5

**Key accomplishments:**

1. Consolidated `windows_oci_vm` into `ocp_virt_vm` — unified Linux+Windows compute template via `guest_os_family` branching; single catalog registration, OS family inferred automatically from annotation or image path
2. Removed orphaned "Delete cloud-init secret" task from `delete_resources.yaml` — create/delete symmetry now holds for all resources
3. Updated `exposed_ports` description in `argument_specs.yaml` with OS-dependent default note (D-01)
4. Deleted `windows_oci_vm` role directory (16 files) — no longer needed

**Key decisions:**

- `ocp_virt_vm` as unified template — single OSAC catalog registration handles both Linux and Windows; OS family inferred from `osac.openshift.io/guest-os-family` annotation or `containerdisks/windows` image path heuristic
- `guest_os_family` branching over separate roles — reduces duplication, keeps orchestration layer unchanged (template_id dispatch still works)
