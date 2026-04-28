# Roadmap: Windows VM Provisioning for OpenShift Virtualization

## Overview

This roadmap delivers Windows VM provisioning capability to the OSAC platform. We start by creating an Ansible template role that provisions Windows VMs from OCI container images with proper sizing, networking, and Windows-specific optimizations. Then we add comprehensive verification tasks to ensure VMs are running and accessible via network, RDP, guest agent, and VNC console.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Windows VM Provisioning** - Create Ansible template role for Windows VM creation
- [ ] **Phase 2: VM Verification** - Add verification tasks for VM accessibility

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
**Plans**: TBD

### Phase 2: VM Verification
**Goal**: System can verify Windows VMs are running and accessible through all expected channels
**Depends on**: Phase 1
**Requirements**: VERIFY-01, VERIFY-02, VERIFY-03, VERIFY-04, VERIFY-05
**Success Criteria** (what must be TRUE):
  1. Template waits for VM to reach Running state (VirtualMachine.status.ready = True)
  2. Template verifies network reachability by pinging assigned IP address
  3. Template verifies RDP port 3389 is reachable
  4. Template verifies QEMU guest agent is responding
  5. Template verifies VNC console is accessible
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Windows VM Provisioning | 0/TBD | Not started | - |
| 2. VM Verification | 0/TBD | Not started | - |
