---
phase: 01-windows-vm-provisioning
plan: 02
subsystem: templates
tags: [windows, vm-provisioning, kubevirt, sysprep, cloudbase-init]
dependency_graph:
  requires: [01-01]
  provides: [windows-vm-task-implementation]
  affects: [osac.templates.windows_oci_vm]
tech_stack:
  added: [sysprep, cloudbase-init, hyper-v-enlightenments]
  patterns: [windows-hostname-truncation, cdrom-bus-sata, extended-wait-timeout]
key_files:
  created:
    - collections/ansible_collections/osac/templates/roles/windows_oci_vm/tasks/create_validate.yaml
    - collections/ansible_collections/osac/templates/roles/windows_oci_vm/tasks/create_build_spec.yaml
    - collections/ansible_collections/osac/templates/roles/windows_oci_vm/tasks/create_secrets.yaml
    - collections/ansible_collections/osac/templates/roles/windows_oci_vm/tasks/create_resources.yaml
    - collections/ansible_collections/osac/templates/roles/windows_oci_vm/tasks/create_wait_annotate.yaml
    - collections/ansible_collections/osac/templates/roles/windows_oci_vm/tasks/delete_resources.yaml
  modified: []
decisions:
  - "Windows hostname truncated to 15 characters without forcing uppercase (Windows normalizes internally)"
  - "Sysprep disk uses cdrom bus sata (not disk bus virtio) per Windows Setup requirements"
  - "VM wait timeout increased to 900 seconds (from 600) to accommodate Windows first boot and sysprep execution"
  - "SSH key handling omitted from create_secrets.yaml (Windows uses RDP, not SSH)"
  - "CloudBase-Init user-data uses cloudInitNoCloud volume type (compatible with cloud-config YAML format)"
  - "Enhanced Hyper-V enlightenments added: synic, vpindex, frequencies, reenlightenment, tlbflush, reset, runtime"
metrics:
  duration: 3 minutes
  tasks_completed: 2
  files_created: 6
  commits: 2
  completed_date: "2026-04-28"
---

# Phase 01 Plan 02: Windows VM Task Implementation Summary

Windows-specific VM provisioning logic with sysprep hostname configuration, enhanced Hyper-V enlightenments, and CloudBase-Init user-data delivery.

## What Was Built

Created 6 substantive task files implementing the core Windows VM provisioning behavior for the `windows_oci_vm` template role:

1. **create_validate.yaml**: Extracts VM configuration from ComputeInstance spec with Windows hostname truncation (15 chars)
2. **create_build_spec.yaml**: Builds VM domain spec with Windows clock configuration and enhanced Hyper-V enlightenments
3. **create_secrets.yaml**: Creates sysprep ConfigMap with unattend.xml and handles CloudBase-Init user-data
4. **create_resources.yaml**: Creates DataVolume and VirtualMachine resources (OS-agnostic, identical to ocp_virt_vm)
5. **create_wait_annotate.yaml**: Waits for VM ready state with extended timeout and displays Windows-specific info
6. **delete_resources.yaml**: Cleans up all resources including Windows-specific sysprep ConfigMap

Total role file count: 16 (10 from Plan 01 + 6 from this plan)

## Key Implementations

### Windows Hostname Handling (PROV-04)

**create_validate.yaml** extracts hostname from `ComputeInstance.metadata.name` with 15-character truncation:

```yaml
- name: Extract VM hostname from ComputeInstance metadata
  ansible.builtin.set_fact:
    vm_hostname: "{{ compute_instance.metadata.name | truncate(15, True, '') }}"

- name: Log hostname truncation warning
  ansible.builtin.debug:
    msg: "WARNING: ComputeInstance name '{{ compute_instance.metadata.name }}' truncated to '{{ vm_hostname }}' for Windows hostname (15 char limit)"
  when: compute_instance.metadata.name | length > 15
```

Hostname is NOT forced to uppercase — Windows normalizes case internally per RESEARCH.md findings.

### Windows Clock Configuration (D-03)

**create_build_spec.yaml** includes Windows-optimized clock configuration:

```yaml
clock:
  utc: {}
  timer:
    hpet:
      present: false
    pit:
      tickPolicy: delay
    rtc:
      tickPolicy: catchup
    hyperv: {}
```

This configuration ensures accurate timekeeping in Windows VMs running on KubeVirt/OpenShift Virtualization.

### Enhanced Hyper-V Enlightenments (D-03)

**create_build_spec.yaml** adds 7 enhanced Hyper-V features beyond the base ocp_virt_vm configuration:

```yaml
hyperv:
  relaxed: {}           # base (from ocp_virt_vm)
  vapic: {}             # base (from ocp_virt_vm)
  spinlocks:            # base (from ocp_virt_vm)
    spinlocks: 8191
  synic: {}             # ENHANCED
  vpindex: {}           # ENHANCED
  frequencies: {}       # ENHANCED
  reenlightenment: {}   # ENHANCED
  tlbflush: {}          # ENHANCED
  reset: {}             # ENHANCED
  runtime: {}           # ENHANCED
```

These enlightenments improve Windows guest performance by enabling paravirtualized features.

### Sysprep Configuration (PROV-05, D-04, D-05)

**create_secrets.yaml** creates a ConfigMap with minimal unattend.xml for hostname setting:

```yaml
- name: Create sysprep ConfigMap with unattend.xml for hostname
  kubernetes.core.k8s:
    state: present
    definition:
      apiVersion: v1
      kind: ConfigMap
      metadata:
        name: "{{ compute_instance_name }}-sysprep"
        namespace: "{{ compute_instance_target_namespace }}"
      data:
        Unattend.xml: |
          <?xml version="1.0" encoding="utf-8"?>
          <unattend xmlns="urn:schemas-microsoft-com:unattend">
            <settings pass="specialize">
              <component name="Microsoft-Windows-Shell-Setup" ...>
                <ComputerName>{{ vm_hostname }}</ComputerName>
              </component>
            </settings>
          </unattend>
```

The sysprep disk is mounted as **cdrom bus sata** (not disk bus virtio) per Windows Setup requirements:

```yaml
- name: Add sysprep disk to template spec
  ansible.builtin.set_fact:
    vm_template_spec: "{{ vm_template_spec | combine(sysprep_patch, recursive=True, list_merge='append') }}"
  vars:
    sysprep_patch:
      domain:
        devices:
          disks:
            - name: sysprep-disk
              cdrom:
                bus: sata
      volumes:
        - name: sysprep-disk
          sysprep:
            configMap:
              name: "{{ compute_instance_name }}-sysprep"
```

### CloudBase-Init User-Data (PROV-02, D-02)

**create_secrets.yaml** copies user-data secret from ComputeInstance namespace to VM namespace and mounts it via `cloudInitNoCloud`:

```yaml
- name: Copy user-data secret to VM namespace and add cloud-init disk to template spec
  when: vm_user_data_secret_ref | length > 0
  block:
    - name: Read user-data secret from ComputeInstance namespace
      kubernetes.core.k8s_info:
        api_version: v1
        kind: Secret
        name: "{{ vm_user_data_secret_ref }}"
        namespace: "{{ compute_instance.metadata.namespace }}"
      register: user_data_secret

    - name: Create user-data secret in VM namespace
      kubernetes.core.k8s:
        state: present
        definition:
          apiVersion: v1
          kind: Secret
          metadata:
            name: "{{ compute_instance_name }}-user-data"
            namespace: "{{ compute_instance_target_namespace }}"
          type: Opaque
          data: "{{ user_data_secret.resources[0].data }}"

    - name: Add cloud-init disk to template spec
      ansible.builtin.set_fact:
        vm_template_spec: "{{ vm_template_spec | combine(cloud_init_patch, ...) }}"
      vars:
        cloud_init_patch:
          domain:
            devices:
              disks:
                - name: cloud-init-disk
                  disk:
                    bus: virtio
                  serial: cloud-init
          volumes:
            - name: cloud-init-disk
              cloudInitNoCloud:
                secretRef:
                  name: "{{ compute_instance_name }}-user-data"
```

CloudBase-Init can consume `cloudInitNoCloud` with cloud-config YAML format (similar to Linux cloud-init).

### Extended Wait Timeout (Pitfall 4)

**create_wait_annotate.yaml** uses 900-second timeout (15 minutes) instead of 600 seconds to accommodate Windows first boot and sysprep execution:

```yaml
- name: Wait for VM to be ready
  kubernetes.core.k8s_info:
    api_version: kubevirt.io/v1
    kind: VirtualMachine
    name: "{{ compute_instance_name }}"
    namespace: "{{ compute_instance_target_namespace }}"
    wait: true
    wait_condition:
      type: Ready
      status: "True"
    wait_timeout: 900
  when: vm_run_strategy != "Halted"
```

The display message includes Windows-specific information:

```yaml
- name: Display VM information
  ansible.builtin.debug:
    msg:
      - "Virtual Machine '{{ compute_instance_name }}' created successfully"
      - "OS: Windows"
      - "Namespace: {{ compute_instance_target_namespace }}"
      - "Image: {{ vm_image_source }}"
      - "CPU Cores: {{ vm_cpu_cores }}/Memory: {{ vm_memory }}"
      - "Root Disk Size: {{ vm_boot_disk_size }}"
      - "Additional Disks: {{ vm_additional_disks | length }}"
      - "RunStrategy: {{ vm_run_strategy }}"
      - "Hostname: {{ vm_hostname }}"
      - "Status: {{ vm_status.resources[0].status.printableStatus | default('Unknown') }}"
```

### Sysprep ConfigMap Cleanup (Pitfall 5)

**delete_resources.yaml** includes sysprep ConfigMap cleanup with soft-fail pattern (identical to other secret cleanups):

```yaml
- name: Delete sysprep ConfigMap
  kubernetes.core.k8s:
    api_version: v1
    kind: ConfigMap
    name: "{{ compute_instance_name }}-sysprep"
    namespace: "{{ compute_instance_target_namespace }}"
    state: absent
  register: delete_sysprep_configmap
  failed_when:
    - delete_sysprep_configmap.failed is defined
    - delete_sysprep_configmap.failed
    - "'not found' not in (delete_sysprep_configmap.msg | default(''))"
```

This prevents errors if the ConfigMap was already deleted or never created.

## Deviations from Plan

None — plan executed exactly as written.

## Requirements Satisfied

- **PROV-01**: Boot Windows VM from OCI container image via DataVolume registry source
- **PROV-02**: Apply CPU/memory/disk sizing from ComputeInstance spec
- **PROV-03**: Connect VM to VirtualNetwork/Subnet specified in spec (via existing VM orchestration)
- **PROV-04**: Set Windows hostname from ComputeInstance metadata (truncated to 15 chars)
- **PROV-05**: Create VirtualMachine CR with Windows-optimized configuration (clock, Hyper-V, sysprep)

## Technical Details

### File Organization

All 6 task files follow the established ocp_virt_vm pattern:

- **create_validate.yaml**: Parameter validation and spec extraction
- **create_build_spec.yaml**: VM template spec construction
- **create_secrets.yaml**: Secrets and ConfigMaps creation
- **create_resources.yaml**: Kubernetes resource creation
- **create_wait_annotate.yaml**: Readiness waiting and status annotation
- **delete_resources.yaml**: Resource cleanup

### Windows-Specific Adaptations

| File | Windows-Specific Changes | Rationale |
|------|--------------------------|-----------|
| create_validate.yaml | Added `vm_hostname` extraction with truncate(15) | Windows NetBIOS name limit |
| create_build_spec.yaml | Added `clock` block with Windows timers | Accurate Windows timekeeping |
| create_build_spec.yaml | Added 7 enhanced Hyper-V enlightenments | Improved Windows performance |
| create_secrets.yaml | Added sysprep ConfigMap with unattend.xml | Hostname configuration |
| create_secrets.yaml | Sysprep disk uses cdrom bus sata | Windows Setup requirement |
| create_secrets.yaml | Omitted SSH key handling blocks | Windows uses RDP, not SSH |
| create_wait_annotate.yaml | Increased timeout to 900 seconds | Windows first boot duration |
| create_wait_annotate.yaml | Added "OS: Windows" and hostname to display | Windows-specific context |
| delete_resources.yaml | Added sysprep ConfigMap cleanup | Resource lifecycle completeness |

### OS-Agnostic Files

**create_resources.yaml** is a verbatim copy from ocp_virt_vm with zero changes. This file:
- Creates DataVolume from registry source (`docker://{{ vm_image_source }}`)
- Creates VirtualMachine CR using `vm_template_spec` (which already has Windows config)
- Handles additional disks and restart requests
- Contains no OS-specific logic

This demonstrates clean separation of concerns: Windows-specific configuration is built in `create_build_spec.yaml` and `create_secrets.yaml`, then applied generically in `create_resources.yaml`.

## Validation Results

All verification checks passed:

1. Total file count: 16 (10 from Plan 01 + 6 from this plan)
2. Zero occurrences of `ocp_virt_vm` in any file
3. Hostname truncation pattern present: `truncate(15, True, '')`
4. Windows clock configuration present: `clock:`, `hpet:`, `hyperv: {}`
5. Enhanced Hyper-V enlightenments present: `synic:`, `vpindex:`, `frequencies:`, `reenlightenment:`, `tlbflush:`, `reset:`, `runtime:`
6. Root disk uses virtio bus: `bus: virtio`
7. Sysprep ConfigMap creation present: `sysprep`, `ComputerName`
8. Sysprep disk uses cdrom bus sata: `bus: sata`
9. CloudBase-Init user-data present: `cloudInitNoCloud`
10. SSH key handling absent: no `ssh-public-key` references
11. Extended wait timeout: `wait_timeout: 900`
12. Windows OS indicator: `OS: Windows`
13. Hostname display: `vm_hostname`
14. Sysprep cleanup present: `delete_sysprep_configmap`, `ConfigMap`

## Integration Points

The 6 task files integrate with the role skeleton from Plan 01:

- **create.yaml** (Plan 01) orchestrates the 6-step creation flow:
  1. Pre-create hook
  2. Validate (this plan)
  3. Build spec (this plan)
  4. Secrets (this plan)
  5. Resources (this plan)
  6. Wait and annotate (this plan)
  7. Post-create hook

- **delete.yaml** (Plan 01) orchestrates the deletion flow:
  1. Pre-delete hook
  2. Delete resources (this plan)
  3. Post-delete hook

- **defaults/main.yaml** (Plan 01) provides `default_spec` and `default_arg_specs` consumed by create_validate.yaml
- **meta/argument_specs.yaml** (Plan 01) defines role parameters
- **meta/osac.yaml** (Plan 01) registers template with OSAC system

## Next Steps

With this plan complete, the `windows_oci_vm` role has all core provisioning functionality:

- ✅ Role skeleton with orchestration files (Plan 01)
- ✅ Windows-specific task implementations (this plan)
- ⏳ Verification tasks (Plan 03) — network, RDP, guest agent, VNC

Plan 03 will add verification tasks to confirm the VM is accessible after provisioning.

## Commits

1. **9844bcb**: feat(01-02): add Windows VM validation, build spec, and secrets tasks
   - create_validate.yaml with hostname truncation
   - create_build_spec.yaml with Windows clock and enhanced Hyper-V enlightenments
   - create_secrets.yaml with sysprep ConfigMap and CloudBase-Init user-data

2. **c37280f**: feat(01-02): add Windows VM resource creation, wait, and deletion tasks
   - create_resources.yaml (OS-agnostic DataVolume and VirtualMachine creation)
   - create_wait_annotate.yaml with 900s timeout and Windows-specific display
   - delete_resources.yaml with sysprep ConfigMap cleanup

## Self-Check: PASSED

All created files exist:
- ✅ create_validate.yaml
- ✅ create_build_spec.yaml
- ✅ create_secrets.yaml
- ✅ create_resources.yaml
- ✅ create_wait_annotate.yaml
- ✅ delete_resources.yaml

All commits exist:
- ✅ 9844bcb (Task 1)
- ✅ c37280f (Task 2)

All Windows-specific patterns verified:
- ✅ Hostname truncation to 15 chars
- ✅ Windows clock configuration
- ✅ Enhanced Hyper-V enlightenments (7 features)
- ✅ Sysprep ConfigMap with unattend.xml
- ✅ Sysprep disk as cdrom bus sata
- ✅ CloudBase-Init user-data via cloudInitNoCloud
- ✅ Extended wait timeout (900s)
- ✅ Windows OS indicator in display
- ✅ Sysprep ConfigMap cleanup in delete flow
- ✅ Zero ocp_virt_vm references
- ✅ Total file count: 16
