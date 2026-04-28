# Requirements - v1.0 Windows VM Provisioning

## v1.0 Requirements

### VM Provisioning (PROV)

Core infrastructure provisioning capabilities - creating Windows VMs with correct configuration.

- [ ] **PROV-01**: User can boot a Windows VM from an OCI container image using DataVolume registry source
- [ ] **PROV-02**: User can specify CPU, memory, and disk sizing via ComputeInstance spec and have it applied to the VirtualMachine
- [ ] **PROV-03**: User can connect the Windows VM to a specified VirtualNetwork and Subnet
- [ ] **PROV-04**: User can set the Windows hostname via ComputeInstance metadata
- [ ] **PROV-05**: System creates VirtualMachine CR with Windows-optimized configuration (virtio-win drivers, Hyper-V enlightenments)

### VM Verification (VERIFY)

Post-provisioning validation capabilities - confirming Windows VMs are running and accessible.

- [ ] **VERIFY-01**: System waits for Windows VM to reach Running state (VirtualMachine.status.ready = True)
- [ ] **VERIFY-02**: System verifies network reachability by pinging the assigned IP address
- [ ] **VERIFY-03**: System verifies RDP accessibility by checking port 3389 is reachable
- [ ] **VERIFY-04**: System verifies QEMU guest agent is responding
- [ ] **VERIFY-05**: System verifies VNC console is accessible

## Future Requirements

These requirements are deferred to future milestones:

### Active Directory Integration (AD)
- [ ] **AD-01**: User can join Windows VM to Active Directory domain during provisioning
- [ ] **AD-02**: User can specify domain credentials via secret reference

### License Management (LIC)
- [ ] **LIC-01**: System activates Windows license automatically post-boot
- [ ] **LIC-02**: User can specify KMS server or license key via ComputeInstance spec

### Guest Customization (CUSTOM)
- [ ] **CUSTOM-01**: User can execute PowerShell scripts during Windows VM provisioning
- [ ] **CUSTOM-02**: User can trigger sysprep automation for Windows image customization

### Advanced Storage (STORAGE)
- [ ] **STORAGE-01**: User can create snapshots of Windows VM disks
- [ ] **STORAGE-02**: User can clone Windows VMs from existing instances
- [ ] **STORAGE-03**: User can use thin provisioning for Windows VM disks

## Out of Scope

Explicitly excluded from all versions:

- **Multi-VM orchestration**: Coordinating multiple Windows VMs in a single provisioning operation — use separate ComputeInstance resources
- **Windows Update automation**: Automatic patching during provisioning — handled by user's image build pipeline
- **Backup/restore workflows**: VM-level backup automation — use external backup solutions
- **Performance tuning**: Automatic CPU pinning, NUMA topology, huge pages — manual configuration via override hooks if needed

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| PROV-01 | Phase 1 | Pending |
| PROV-02 | Phase 1 | Pending |
| PROV-03 | Phase 1 | Pending |
| PROV-04 | Phase 1 | Pending |
| PROV-05 | Phase 1 | Pending |
| VERIFY-01 | Phase 2 | Pending |
| VERIFY-02 | Phase 2 | Pending |
| VERIFY-03 | Phase 2 | Pending |
| VERIFY-04 | Phase 2 | Pending |
| VERIFY-05 | Phase 2 | Pending |

---

*Requirements for milestone v1.0 - defined 2026-04-28*
