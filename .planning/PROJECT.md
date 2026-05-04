# Linux and Windows VM Provisioning for OpenShift Virtualization

## What This Is

An Ansible Automation Platform template that provisions Linux and Windows virtual machines in OpenShift Virtualization from pre-built container images stored in OCI-compliant registries. The `ocp_virt_vm` template handles both OS families via `guest_os_family` branching — a single template, a single OSAC catalog registration. OS family is inferred automatically from the `osac.openshift.io/guest-os-family` annotation on the ComputeInstance or from the `containerdisks/windows` image path heuristic.

## Core Value

Boot a Windows VM from an OCI registry image, connect it to the network, and confirm it reaches Running state (RDP/VNC verification deferred to v2).

## Current State

**Shipped:** v1.1 (2026-05-02)
**Codebase:** `ocp_virt_vm` Ansible role (unified Linux+Windows) + integration test fixtures

The `ocp_virt_vm` role handles OS-specific behavior through guest_os_family branching: sysprep hostname configuration (15-char NetBIOS truncation), enhanced Hyper-V enlightenments, Windows clock config, CloudBase-Init user-data via cloudInitNoCloud, and SATA CD-ROM bus for sysprep disk (Windows); cloud-init and SSH key injection (Linux).

## Requirements

### Validated

- ✓ Boot Windows VM from OCI container image (DataVolume registry source) — v1.0
- ✓ Apply CPU/memory/disk sizing from ComputeInstance spec — v1.0
- ✓ Connect VM to VirtualNetwork/Subnet specified in spec — v1.0
- ✓ Set Windows hostname from ComputeInstance metadata (15-char truncation) — v1.0
- ✓ Create VirtualMachine CR with Windows-optimized configuration (Hyper-V enlightenments, clock config) — v1.0
- ✓ Wait for VM to reach Running state (VirtualMachine.status.ready = True, 900s timeout) — v1.0

### Active

None — planning next milestone.

### Out of Scope

- Verify network reachability (ping assigned IP address) — deferred to v2
- Verify RDP accessibility (port 3389 reachable) — deferred to v2
- Verify QEMU guest agent responding — deferred to v2
- Verify VNC console accessible — deferred to v2
- Active Directory domain join workflows — deferred to v2+
- Windows license activation automation — deferred to v2+
- Custom PowerShell script execution during provisioning — deferred to v2+
- Sysprep automation and image customization — deferred to v2+
- Advanced storage features (snapshots, clones, thin provisioning) — deferred to v2+

## Context

**Existing Architecture:**
This is a brownfield addition to the osac-aap repository. The `ocp_virt_vm` template handles both Linux and Windows VM provisioning. OS family is determined at runtime by `infer_guest_os_family.yaml`, which checks the `osac.openshift.io/guest-os-family` annotation on the ComputeInstance, then falls back to the `containerdisks/windows` image path heuristic, then defaults to `linux`.

**Integration Points:**
- Triggered by ComputeInstance CRD creation in fulfillment-service
- Receives resource definition via ansible_eda.event.payload
- Uses `template_id: osac.templates.ocp_virt_vm` in ComputeInstance spec to route to this template (both Linux and Windows)
- Follows existing compute_instance/create workflow orchestration
- Registered with osac.templates collection alongside other infrastructure templates

**Technical Environment:**
- OpenShift Virtualization (KubeVirt) for VM management
- OCI-compliant container registries for Windows image storage
- CloudBase-Init for Windows guest configuration
- QEMU guest agent for VM status reporting
- Registry pull secrets pre-configured in target namespaces

## Constraints

- **Tech Stack**: Ansible Automation Platform, OpenShift Virtualization, OCI registries — Required for OSAC integration
- **Integration Pattern**: Must follow osac.templates collection structure and override pattern — Maintains consistency with existing templates
- **Authentication**: Registry pull secrets managed externally — Template assumes secrets exist, doesn't create them
- **Timeline**: Product roadmap feature — Ships when core functionality validated

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| ocp_virt_vm as unified Linux+Windows template | Single template, single OSAC catalog registration; OS family inferred from annotation or image path; eliminates role duplication | ✓ Implemented (v1.1) |
| Follow ocp_virt_vm pattern | Proven architecture for VM provisioning; reduces implementation risk and maintains consistency | ✓ Implemented in unified `ocp_virt_vm` role |
| Defer advanced customization to v2+ | Ship basic functionality fast to validate approach; iterate based on real usage feedback | ✓ Active |
| Reuse existing Hyper-V enlightenments | ocp_virt_vm already configures hyperv features optimal for Windows | ✓ Implemented — plus 7 additional enlightenments |
| Remove Phase 2 (deeper VM verification) | Basic Ready state verification already in Phase 1 matches Linux pattern; deeper checks are net-new capability | ✓ Deferred to v2 |
| Sysprep disk as SATA CD-ROM | Required by Windows Setup; virtio bus not supported for sysprep media | ✓ Implemented |
| 900s VM ready timeout | Windows first boot + sysprep takes significantly longer than Linux boot | ✓ Implemented |
| Hostname truncation without uppercase forcing | Windows normalizes hostname case internally per MSDN documentation | ✓ Implemented |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-05-02 after v1.1 consolidation (windows_oci_vm merged into ocp_virt_vm)*
