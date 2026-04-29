# Roadmap: Windows VM Provisioning for OpenShift Virtualization

## Overview

This roadmap delivers Windows VM provisioning capability to the OSAC platform. We start by creating an Ansible template role that provisions Windows VMs from OCI container images with proper sizing, networking, and Windows-specific optimizations. Then we add comprehensive verification tasks to ensure VMs are running and accessible via network, RDP, guest agent, and VNC console.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Windows VM Provisioning** - Create Ansible template role for Windows VM creation

## Phase Details

### Phase 1: Windows VM Provisioning
**Goal**: Ansible template role can create Windows VMs with proper configuration and networking
**Depends on**: Nothing (first phase)
**Requirements**: PROV-01, PROV-02, PROV-03, PROV-04, PROV-05
**Success Criteria** (what must be TRUE):
  1. Template creates VirtualMachine CR with Windows-optimized configuration (virtio-win, Hyper-V enlightenments)
  2. VM boots from OCI container image using DataVolume registry source
  3. VM receives specified CPU, memory, and disk sizing from ComputeInstance spec
  4. VM connects to specified VirtualNetwork and Subnet
  5. Windows hostname is set from ComputeInstance metadata
**Plans**: 3 (complete)

### ~~Phase 2: VM Verification~~ (REMOVED)
**Reason**: Basic VM verification (Ready state wait, ComputeInstance annotation) is already implemented in Phase 1's `create_wait_annotate.yaml`, matching the Linux `ocp_virt_vm` pattern. Deeper checks (ping, RDP port, guest agent, VNC console) deferred to v2 milestone.

## Progress

**Execution Order:**
Phase 1 only (milestone complete)

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Windows VM Provisioning | 3/3 | Complete | 2026-04-28 |
