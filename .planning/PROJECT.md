# Windows VM Provisioning for OpenShift Virtualization

## What This Is

An Ansible Automation Platform template that provisions Windows virtual machines in OpenShift Virtualization from pre-built Windows container images stored in OCI-compliant registries. The template integrates with OSAC's fulfillment workflow to handle ComputeInstance resources with implementationStrategy `windows_oci_vm`.

## Core Value

Boot a Windows VM from an OCI registry image, connect it to the network, and verify it's accessible via RDP and VNC console.

## Current State

**Shipped:** v1.0 (2026-04-29)
**Codebase:** 16-file Ansible role (`osac.templates.windows_oci_vm`) + 1 test fixture, ~732 lines YAML

The `windows_oci_vm` role follows the `ocp_virt_vm` pattern with Windows-specific adaptations: sysprep hostname configuration (15-char NetBIOS truncation), enhanced Hyper-V enlightenments (10 features), Windows clock config, CloudBase-Init user-data via cloudInitNoCloud, and SATA CD-ROM bus for sysprep disk.

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
This is a brownfield addition to the osac-aap repository. The codebase already supports Linux VM provisioning through the `ocp_virt_vm` template role. The `windows_oci_vm` role mirrors this structure exactly (16 files, same directory layout) to maintain consistency.

**Integration Points:**
- Triggered by ComputeInstance CRD creation in fulfillment-service
- Receives resource definition via ansible_eda.event.payload
- Uses `implementationStrategy: windows_oci_vm` to route to this template
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
| implementationStrategy: windows_oci_vm | Clear, descriptive name distinguishing Windows VMs from Linux; indicates OCI image source | ✓ Implemented |
| Follow ocp_virt_vm pattern | Proven architecture for VM provisioning; reduces implementation risk and maintains consistency | ✓ Implemented — 16 files, identical structure |
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
*Last updated: 2026-04-29 after v1.0 milestone*
