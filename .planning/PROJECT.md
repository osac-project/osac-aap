# Windows VM Provisioning for OpenShift Virtualization

## What This Is

An Ansible Automation Platform template that provisions Windows virtual machines in OpenShift Virtualization from pre-built Windows container images stored in OCI-compliant registries. The template integrates with OSAC's fulfillment workflow to handle ComputeInstance resources with implementationStrategy `windows_oci_vm`.

## Core Value

Boot a Windows VM from an OCI registry image, connect it to the network, and verify it's accessible via RDP and VNC console.

## Current Milestone: v1.0 Windows VM Provisioning

**Goal:** Ship a working Windows VM provisioning template for OpenShift Virtualization using the osac-aap component.

**Target features:**
- Boot Windows VMs from OCI container images (DataVolume registry source)
- Apply sizing and network configuration from ComputeInstance spec  
- Verify VM is running and accessible (network, RDP, guest agent, VNC)

**Scope:** osac-aap template role (`osac.templates.windows_oci_vm`) implementation only - reuses existing fulfillment-service API, operator, and installer components.

## Requirements

### Validated

- ✓ Linux VM provisioning via ocp_virt_vm template — existing
- ✓ ComputeInstance CRD integration with AAP workflows — existing
- ✓ DataVolume from registry source support — existing
- ✓ Hyper-V enlightenments in VM spec — existing
- ✓ Boot Windows VM from OCI container image (DataVolume registry source) — Validated in Phase 1
- ✓ Apply CPU/memory/disk sizing from ComputeInstance spec — Validated in Phase 1
- ✓ Connect VM to VirtualNetwork/Subnet specified in spec — Validated in Phase 1
- ✓ Set Windows hostname from ComputeInstance metadata — Validated in Phase 1
- ✓ Create VirtualMachine CR with Windows-optimized configuration — Validated in Phase 1

### Active

- [ ] Wait for VM to reach Running state (VirtualMachine.status.ready = True)
- [ ] Verify network reachability (ping assigned IP address)
- [ ] Verify RDP accessibility (port 3389 reachable)
- [ ] Verify QEMU guest agent responding
- [ ] Verify VNC console accessible

### Out of Scope

- Active Directory domain join workflows — deferred to v2
- Windows license activation automation — deferred to v2
- Custom PowerShell script execution during provisioning — deferred to v2
- Sysprep automation and image customization — deferred to v2
- Advanced storage features (snapshots, clones, thin provisioning) — deferred to v2

## Context

**Existing Architecture:**
This is a brownfield addition to the osac-aap repository. The codebase already supports Linux VM provisioning through the `ocp_virt_vm` template role. That template provides the foundational pattern:
- Pulls OCI images via DataVolume registry source
- Creates VirtualMachine custom resources with Hyper-V enlightenments
- Handles sizing, networking, and storage configuration
- Follows OSAC's override pattern for customization

**Integration Points:**
- Triggered by ComputeInstance CRD creation in fulfillment-service
- Receives resource definition via ansible_eda.event.payload
- Uses `implementationStrategy: windows_oci_vm` to route to this template
- Follows existing compute_instance/create workflow orchestration
- Registers with osac.templates collection alongside other infrastructure templates

**Technical Environment:**
- OpenShift Virtualization (KubeVirt) for VM management
- OCI-compliant container registries for Windows image storage
- CloudBase-Init or equivalent for Windows guest configuration
- QEMU guest agent for VM status reporting
- Registry pull secrets pre-configured in target namespaces

**Windows-Specific Considerations:**
- Windows images require different disk bus configuration than Linux (virtio-win drivers)
- RDP (port 3389) is the primary access method instead of SSH
- VNC console provides fallback access for troubleshooting
- CloudBase-Init handles basic configuration (hostname, network) similar to cloud-init
- Guest agent provides VM status and metadata to OpenShift

**Testing Strategy:**
Development cluster with pre-built Windows OCI images available for validation. Manual testing of each success criterion before integration test automation.

## Constraints

- **Tech Stack**: Ansible Automation Platform, OpenShift Virtualization, OCI registries — Required for OSAC integration
- **Integration Pattern**: Must follow osac.templates collection structure and override pattern — Maintains consistency with existing templates
- **Authentication**: Registry pull secrets managed externally — Template assumes secrets exist, doesn't create them
- **Scope**: Basic boot and network validation only in v1 — Advanced customization deferred to reduce initial complexity
- **Timeline**: Product roadmap feature — Ships when core functionality validated

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| implementationStrategy: windows_oci_vm | Clear, descriptive name distinguishing Windows VMs from Linux; indicates OCI image source | Implemented in Phase 1 |
| Follow ocp_virt_vm pattern | Proven architecture for VM provisioning; reduces implementation risk and maintains consistency | Implemented in Phase 1 |
| Defer advanced customization to v2+ | Ship basic functionality fast to validate approach; iterate based on real usage feedback | Active |
| Hybrid Windows setup approach | V1 focuses on boot and connectivity; domain join, licensing, scripts come later as separate phases | Active |
| Reuse existing Hyper-V enlightenments | ocp_virt_vm already configures hyperv features (relaxed, vapic, spinlocks) optimal for Windows | Implemented in Phase 1, plus 7 additional enlightenments |

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
*Last updated: 2026-04-28 - Phase 1 complete: windows_oci_vm role created (16 files, all PROV-01 through PROV-05 validated)*
