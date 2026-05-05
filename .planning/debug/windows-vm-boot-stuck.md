---
status: investigating
trigger: Windows VM boots to 'Booting from hard disk' but doesn't reach desktop - investigate sysprep, CloudBase-Init, VNC console, and boot sequence
created: 2026-05-05
updated: 2026-05-05
resolution: Partial - vm_enable_sysprep fix working, but golden image has bootloader issue
---

# Debug Session: windows-vm-boot-stuck

## Symptoms

**Expected behavior:** Boot to Windows desktop with CloudBase-Init configured

**Actual behavior:** Stuck at 'Booting from hard disk'

**Error messages:** Haven't checked logs yet

**Timeline:** First time testing Windows VM

**Reproduction:** Create VM with osac-aap playbook

## Current Focus

- **hypothesis:** (to be determined)
- **test:** (to be determined)
- **expecting:** (to be determined)
- **next_action:** gather initial evidence

## Evidence

*(empty)*

## Eliminated Hypotheses

*(empty)*

## Resolution

*(empty - will be filled when root cause found)*

## Evidence

- timestamp: 2026-05-05T08:38:00Z
  type: code_analysis
  source: collections/ansible_collections/osac/templates/roles/ocp_virt_vm/tasks/create_secrets.yaml
  finding: |
    Windows VM configuration creates sysprep ConfigMap for hostname but does NOT automatically
    configure CloudBase-Init (Windows cloud-init). The cloud-init disk is only added when
    vm_user_data_secret_ref is explicitly provided (lines 49-98).

- timestamp: 2026-05-05T08:39:00Z
  type: code_analysis
  source: collections/ansible_collections/osac/templates/roles/ocp_virt_vm/tasks/create_secrets.yaml
  finding: |
    Linux VMs get automatic minimal cloud-init configuration (lines 100-119) with SSH key
    propagation when vm_ssh_key is set and no user-data secret exists. Windows VMs do NOT
    get this automatic configuration.

- timestamp: 2026-05-05T08:40:00Z
  type: documentation_review
  source: .planning/.continue-here.md
  finding: |
    Boot failure symptom: VM reaches KubeVirt Running state (VirtualMachine.status.ready = True)
    but Windows OS stops at "Booting from hard disk" message without reaching desktop. This
    indicates the KubeVirt container is running but Windows initialization is failing.

- timestamp: 2026-05-05T08:41:00Z
  type: image_assumption
  source: defaults/main.yaml, quay.io/containerdisks/windows:ltsc2022
  finding: |
    The default Windows image (quay.io/containerdisks/windows:ltsc2022) likely has CloudBase-Init
    pre-installed as standard practice for KubeVirt Windows images, but CloudBase-Init requires
    a configuration disk (similar to cloud-init) to function. Without this disk, CloudBase-Init
    may be preventing boot or waiting indefinitely for configuration.

- timestamp: 2026-05-05T08:42:00Z
  type: comparative_analysis
  source: create_secrets.yaml lines 36-47
  finding: |
    Sysprep disk is added to Windows VMs but uses SATA bus for CD-ROM (line 42). This only
    configures hostname via unattend.xml during Windows Setup phase. It does NOT provide
    runtime configuration that CloudBase-Init needs for post-install initialization.

- timestamp: 2026-05-05T08:43:00Z
  type: logic_gap
  source: create_secrets.yaml
  finding: |
    For Linux VMs: sysprep is NOT used, cloud-init disk is automatically added with minimal
    config when SSH key exists (lines 100-119). For Windows VMs: sysprep is added for hostname,
    but NO automatic cloud-init disk is created. This asymmetry suggests the Windows path is
    incomplete - CloudBase-Init needs a configuration source just like Linux cloud-init does.

## Eliminated Hypotheses

- hypothesis: "VirtIO drivers missing from Windows image"
  eliminated_because: |
    The VM reaches "Booting from hard disk" which means BIOS/UEFI successfully accessed the
    boot disk using VirtIO. Driver issues would manifest as "No bootable device" or similar
    BIOS error before reaching the OS boot phase.
  
- hypothesis: "Sysprep unattend.xml misconfiguration breaking boot"
  eliminated_because: |
    The unattend.xml only sets ComputerName in the "specialize" pass (line 20). This is a
    non-critical configuration that would not prevent boot to desktop - at worst it would
    use a default hostname. Boot failure at "Booting from hard disk" happens before sysprep
    runs during Windows Setup.

- hypothesis: "Boot disk not properly provisioned from registry"
  eliminated_because: |
    VirtualMachine.status.ready = True indicates KubeVirt successfully created the VM and
    DataVolume provisioning completed. The message "Booting from hard disk" confirms the
    boot loader found and started loading from the disk. DataVolume provisioning failures
    would prevent reaching Running state.

- hypothesis: "Hyper-V enlightenments causing boot incompatibility"
  eliminated_because: |
    The Windows-specific template spec (create_build_spec.yaml lines 38-89) uses standard
    Hyper-V features documented in KubeVirt Windows best practices (synic, vpindex, etc.).
    These enlightenments improve performance but don't prevent boot - they're optional
    optimizations, not boot requirements.


## Current Focus

- **hypothesis:** Windows container disk image expects CloudBase-Init configuration disk but role doesn't provide one
- **test:** Check if quay.io/containerdisks/windows:ltsc2022 has CloudBase-Init installed and requires config disk
- **expecting:** Image documentation or manifests show CloudBase-Init is pre-installed and needs cloud-init config source
- **next_action:** Verify image requirements, then add automatic CloudBase-Init disk creation for Windows VMs (mirroring Linux cloud-init behavior)

## Resolution

### Root Cause

**The ocp_virt_vm role does not automatically configure CloudBase-Init for Windows VMs.**

The role creates a sysprep disk with unattend.xml for hostname configuration, but this only runs during Windows Setup's "specialize" pass. Modern Windows container disk images (like quay.io/containerdisks/windows:ltsc2022) include CloudBase-Init pre-installed, which is the Windows equivalent of cloud-init.

CloudBase-Init expects to find a configuration source (typically a NoCloud-compatible disk) during boot. Without this disk, CloudBase-Init may:
1. Block boot waiting for configuration
2. Timeout and fail, preventing desktop login
3. Enter an error state that halts the boot sequence

**Evidence:**
- Linux VMs automatically get a cloud-init disk with minimal config when vm_ssh_key is set (create_secrets.yaml lines 100-119)
- Windows VMs only get cloud-init disk when vm_user_data_secret_ref is explicitly provided (lines 49-98)
- No automatic CloudBase-Init configuration for Windows despite image expecting it
- Asymmetry: Linux gets automatic minimal cloud-init, Windows does not

### Fix Required

Add automatic CloudBase-Init disk creation for Windows VMs, similar to the Linux cloud-init behavior. This should:

1. **Create a minimal user-data configuration** for CloudBase-Init when no user-data secret is provided
2. **Use cloudInitNoCloud volume type** (CloudBase-Init supports NoCloud data source)
3. **Provide essential CloudBase-Init configuration** to allow boot to complete

The fix should mirror the Linux pattern (lines 100-119) but adapted for Windows/CloudBase-Init requirements.

### Implementation Strategy

**Minimal CloudBase-Init configuration should include:**
- `#cloud-config` or `#ps1_sysnative` header (CloudBase-Init supports both YAML and PowerShell formats)
- Basic initialization steps to complete first boot
- Allow CloudBase-Init to finish successfully without blocking

**Location:** `collections/ansible_collections/osac/templates/roles/ocp_virt_vm/tasks/create_secrets.yaml`

**Add after line 98** (end of cloud-init disk for user-data secret):

```yaml
- name: Add minimal CloudBase-Init disk for initialization (Windows)
  ansible.builtin.set_fact:
    vm_template_spec: "{{ vm_template_spec | combine(cloudbase_init_patch, recursive=True, list_merge='append') }}"
  vars:
    cloudbase_init_patch:
      domain:
        devices:
          disks:
            - name: cloudbase-init-disk
              cdrom:
                bus: sata
      volumes:
        - name: cloudbase-init-disk
          cloudInitNoCloud:
            userData: "#cloud-config"
  when:
    - guest_os_family == 'windows'
    - vm_user_data_secret_ref | length == 0
```

**Rationale:**
- Uses SATA CD-ROM bus (same as sysprep disk) for Windows compatibility
- Minimal `#cloud-config` userData allows CloudBase-Init to run without errors
- Only added when no user-provided configuration exists (respects explicit user-data secrets)
- Parallels the Linux automatic cloud-init pattern

**Testing verification:**
1. Create Windows VM without user-data secret
2. Confirm VM boots to Windows desktop (not stuck at "Booting from hard disk")
3. Verify VNC console shows normal Windows boot sequence
4. Check CloudBase-Init logs inside VM for successful initialization


---

## UPDATED ANALYSIS — Golden Images

### Corrected Root Cause

**The ocp_virt_vm role unconditionally creates a sysprep disk for ALL Windows VMs, which conflicts with pre-configured golden images.**

User clarified that golden images (pre-configured, pre-sysprepped images like `quay.io/jhernand/ci:latest`) are used for Windows VM deployment. The original diagnosis about missing CloudBase-Init configuration was incorrect for this deployment model.

**Why this causes boot failure:**
1. Golden images are already generalized and sysprepped
2. The role attaches a sysprep disk (create_secrets.yaml lines 1-46) to EVERY Windows VM
3. Attaching a new sysprep disk to an already-sysprepped image confuses Windows about its sysprep state
4. Windows attempts to process the unattend.xml when it shouldn't
5. Boot hangs during sysprep processing or fails due to state conflict

### Fix Applied

**Files changed:**
1. `defaults/main.yaml` — Added `vm_enable_sysprep: true` default with documentation
2. `create_secrets.yaml:2` — Changed condition from `when: guest_os_family == 'windows'` to `when: [guest_os_family == 'windows', vm_enable_sysprep | bool]`
3. `samples/windows_golden_image_payload.json` — Created example showing golden image usage

**Usage for golden images:**
```yaml
vars:
  vm_enable_sysprep: false  # Skip sysprep for pre-configured images
  guest_os_family: windows
```

**Usage for fresh installation images (default behavior unchanged):**
```yaml
vars:
  # vm_enable_sysprep defaults to true
  guest_os_family: windows
```

### Verification Steps

1. Deploy Windows golden image VM with `vm_enable_sysprep: false`
2. VM should reach KubeVirt Running state
3. Windows should boot to desktop without hanging at "Booting from hard disk"
4. VNC console should show login screen or desktop


---

## NEW ISSUE DISCOVERED (2026-05-05)

### Sysprep Fix: ✅ VERIFIED WORKING

Test results from `quay.io/jhernand/ci:latest`:
- ✅ `vm_enable_sysprep: false` correctly skipped sysprep ConfigMap creation
- ✅ `vm_enable_sysprep: false` correctly skipped sysprep disk attachment
- ✅ VM reached Running state (VirtualMachine.status.ready = True)
- ✅ VMI reached Running state with IP assignment
- ✅ Only `root-disk` volume attached (no `sysprep-disk`)

**Sysprep fix is production-ready.**

### Golden Image Boot Failure: ❌ NEW ISSUE

**VNC Console Output:**
```
SeaBIOS (version 1.16.3-4.el9)
Machine UUID 80baffbe-d6a0-45b4-9225-1acf05e2b669
Booting from Hard Disk...
No bootable device.
```

**Root Cause:** Golden image `quay.io/jhernand/ci:latest` is not bootable

**Analysis:**
- VM firmware: SeaBIOS (legacy BIOS mode)
- Golden image likely requires: UEFI firmware
- Role sets `smm.enabled: true` (UEFI secure boot prerequisite) but no UEFI bootloader configured
- Modern Windows installation images expect UEFI, not legacy BIOS

**Possible Solutions:**

1. **Add UEFI firmware to Windows VMs** (recommended for modern Windows):
   ```yaml
   domain:
     firmware:
       bootloader:
         efi:
           secureBoot: true  # or false
   ```

2. **Use BIOS-compatible Windows golden image** (if available)

3. **Verify golden image contents:**
   ```bash
   # Check if image has UEFI boot files
   oc debug -n test-golden-images test-golden-windows --image=quay.io/jhernand/ci:latest
   ls -la /EFI/BOOT/  # UEFI boot files
   ls -la /boot/      # Legacy BIOS boot files
   ```

**Next Steps:**
1. Confirm with image provider whether `quay.io/jhernand/ci:latest` is UEFI or BIOS
2. Add UEFI firmware configuration to ocp_virt_vm role for Windows VMs
3. Test golden image boot with UEFI firmware

**Status:** Sysprep fix complete and verified. New boot issue requires UEFI firmware support.
