# Phase 1: Windows VM Provisioning - Research

**Researched:** 2026-04-28
**Domain:** Ansible template role for Windows VM provisioning on OpenShift Virtualization (KubeVirt)
**Confidence:** HIGH

## Summary

Phase 1 creates a new Ansible template role (`osac.templates.windows_oci_vm`) that provisions Windows virtual machines in OpenShift Virtualization from OCI container images. The role follows the established `ocp_virt_vm` pattern exactly -- 16 role files plus 1 test fixture -- with Windows-specific modifications concentrated in three files: `create_build_spec.yaml` (Hyper-V enlightenments, clock configuration), `create_secrets.yaml` (sysprep unattend.xml for hostname, CloudBase-Init user-data), and `defaults/main.yaml` (Windows sizing defaults).

The existing `ocp_virt_vm` template already includes Hyper-V enlightenments (relaxed, vapic, spinlocks) and uses virtio disk bus -- both optimal for Windows. The primary delta is adding Windows-specific clock configuration, enhanced Hyper-V features (synic, vpindex, frequencies, reenlightenment), sysprep-based hostname setting via unattend.xml, and adjusting default resource sizes for Windows workloads.

**Primary recommendation:** Duplicate all 16 files from `ocp_virt_vm` into a new `windows_oci_vm` role, modify the three files with Windows-specific configuration, update all FQCN references from `osac.templates.ocp_virt_vm` to `osac.templates.windows_oci_vm`, and create a Windows-specific test fixture.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Disk bus configuration uses **virtio** for best performance (requires virtio-win drivers in Windows image, aligns with KubeVirt best practices)
- **D-02:** CloudBase-Init user-data format is **cloud-config YAML** (similar to Linux cloud-init, easier to template and maintain than PowerShell scripts)
- **D-03:** Hyper-V enlightenments configuration **reused from ocp_virt_vm template** (already optimized for Windows: relaxed, vapic, spinlocks)
- **D-04:** Windows hostname set via **sysprep unattend.xml** (minimal sysprep for hostname only, not full automation)
- **D-05:** Unattend.xml embedded in CloudBase-Init user-data or as separate ConfigMap/Secret (planner determines best approach)

### Claude's Discretion
- **Template file structure:** Claude decides whether to duplicate all 13 task files from `ocp_virt_vm` or parameterize OS differences. Recommendation from CONTEXT.md: start with duplication for clearer separation, refactor to shared logic if patterns emerge in v2.

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope. Sysprep automation (beyond minimal hostname setting) remains deferred to v2 per PROJECT.md.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PROV-01 | Boot Windows VM from OCI container image using DataVolume registry source | DataVolume registry source pattern verified in `ocp_virt_vm/tasks/create_resources.yaml` lines 18-40; no changes needed for Windows |
| PROV-02 | Apply CPU, memory, and disk sizing from ComputeInstance spec | Spec extraction pattern verified in `ocp_virt_vm/tasks/create_validate.yaml`; Windows defaults adjusted (4GiB RAM, 40GiB disk) |
| PROV-03 | Connect Windows VM to specified VirtualNetwork and Subnet | Network interface via masquerade pattern verified in `create_build_spec.yaml`; namespace resolution via `osac.openshift.io/subnet-target-namespace` annotation |
| PROV-04 | Set Windows hostname from ComputeInstance metadata | Sysprep unattend.xml approach researched; ComputerName XML element verified via Microsoft docs; delivery via ConfigMap + sysprep volume |
| PROV-05 | Create VirtualMachine CR with Windows-optimized configuration | Hyper-V enlightenments verified in existing `create_build_spec.yaml`; additional Windows clock/timer config and enhanced hyperv features researched |
</phase_requirements>

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| VM provisioning orchestration | Ansible/AAP (Automation) | -- | Template role follows established OSAC automation pattern; triggered by EDA webhook |
| VirtualMachine CR creation | Kubernetes API (via kubernetes.core) | -- | KubeVirt VirtualMachine is a Kubernetes custom resource |
| DataVolume/disk provisioning | Kubernetes API (CDI) | OCI Registry | CDI pulls OCI image from registry; PVC created in target namespace |
| Windows guest configuration | KubeVirt (in-VM) | CloudBase-Init / Sysprep | Guest agent and CloudBase-Init handle in-guest setup; template injects user-data |
| Hostname setting | Sysprep (in-VM) | -- | Unattend.xml sets ComputerName during Windows specialization pass |
| Network connectivity | KubeVirt (pod network) | -- | Masquerade interface on pod network; no template-level network plumbing |
| Template dispatch | Workflow layer (osac.workflows) | -- | `implementationStrategy` field routes to `windows_oci_vm` role dynamically |

## Standard Stack

### Core
| Library/Tool | Version | Purpose | Why Standard |
|-------------|---------|---------|--------------|
| Ansible Core | 2.20.3 | Automation engine | [VERIFIED: codebase pyproject.toml] Required runtime |
| kubernetes.core | 5.2.0 | K8s resource management | [VERIFIED: codebase collections/requirements.yml] Used by all OSAC templates |
| KubeVirt API | v1 (kubevirt.io/v1) | VirtualMachine CRD | [VERIFIED: codebase create_resources.yaml] Standard VM API |
| CDI API | v1beta1 (cdi.kubevirt.io/v1beta1) | DataVolume CRD | [VERIFIED: codebase create_resources.yaml] Standard disk provisioning API |

### Supporting
| Library/Tool | Version | Purpose | When to Use |
|-------------|---------|---------|-------------|
| CloudBase-Init | (in Windows image) | Windows guest agent | Hostname, user-data processing during first boot |
| QEMU Guest Agent | (in Windows image) | VM status reporting | Reports IP, OS info to KubeVirt; enables readiness checks |
| virtio-win drivers | (in Windows image) | Virtio device support | Pre-installed in OCI image; enables virtio disk/network bus |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Sysprep unattend.xml for hostname | CloudBase-Init set_hostname plugin | CloudBase-Init hostname support is less reliable on Windows; sysprep is the canonical Windows mechanism |
| Separate ConfigMap for unattend.xml | Inline in CloudBase-Init user-data | ConfigMap is cleaner separation of concerns; inline reduces resource count but mixes formats |
| Duplicating all task files | Parameterizing OS differences | Duplication is explicit and safe for v1; parameterization adds complexity without proven benefit yet |

## Architecture Patterns

### System Architecture Diagram

```
ComputeInstance CRD (fulfillment-service)
         |
         v
    EDA Webhook (port 5000)
         |
         v
    Rulebook: cluster_fulfillment.yml
         |
         v
    Root Playbook: playbook_osac_create_compute_instance.yml
         |
         v
    Workflow: osac.workflows.compute_instance.create
         |  (extracts implementationStrategy = "windows_oci_vm")
         v
    Template: osac.templates.windows_oci_vm
         |
         +--> create_validate.yaml     (extract sizing, validate params)
         +--> create_build_spec.yaml   (build VM spec with Windows config)
         +--> create_secrets.yaml      (sysprep ConfigMap + CloudBase-Init user-data)
         +--> create_modify_vm_spec    (no-op hook for customization)
         +--> create_pre_create_hook   (no-op hook)
         +--> create_resources.yaml    (DataVolume + VirtualMachine CRs)
         +--> create_post_create_hook  (no-op hook)
         +--> create_wait_annotate     (wait Ready, annotate ComputeInstance)
```

### Recommended Project Structure
```
collections/ansible_collections/osac/templates/roles/
├── ocp_virt_vm/                    # Existing Linux VM template (reference)
└── windows_oci_vm/                 # NEW: Windows VM template
    ├── defaults/
    │   └── main.yaml               # Windows-specific defaults (RDP, 4GiB RAM, 40GiB disk)
    ├── meta/
    │   ├── argument_specs.yaml     # Role parameters (exposed_ports default: 3389/tcp)
    │   └── osac.yaml               # Template metadata (compute_instance type)
    └── tasks/
        ├── create.yaml             # Main orchestration (FQCN: osac.templates.windows_oci_vm)
        ├── create_validate.yaml    # Param extraction + hostname extraction
        ├── create_build_spec.yaml  # Windows VM spec (clock, enhanced hyperv, synic)
        ├── create_secrets.yaml     # Sysprep ConfigMap + CloudBase-Init user-data
        ├── create_modify_vm_spec.yaml    # No-op hook
        ├── create_pre_create_hook.yaml   # No-op hook
        ├── create_resources.yaml         # DataVolume + VirtualMachine creation
        ├── create_post_create_hook.yaml  # No-op hook
        ├── create_wait_annotate.yaml     # Wait for VM ready + annotate
        ├── delete.yaml                   # Delete orchestration
        ├── delete_resources.yaml         # Resource cleanup (+ sysprep ConfigMap)
        ├── delete_pre_delete_hook.yaml   # No-op hook
        └── delete_post_delete_hook.yaml  # No-op hook

tests/integration/fixtures/
└── computeinstance-windows-test.yaml    # NEW: Windows ComputeInstance fixture
```

### Pattern 1: Windows VM Spec Build (create_build_spec.yaml)

**What:** Constructs the KubeVirt VirtualMachine domain spec with Windows-optimized configuration.
**When to use:** Every Windows VM creation -- this is the core Windows delta from the Linux template.

The existing `ocp_virt_vm` template already includes basic Hyper-V features. For Windows, the spec must be enhanced with:

1. **Clock configuration** -- Windows requires UTC base clock with Hyper-V timer and HPET disabled
2. **Enhanced Hyper-V enlightenments** -- synic, vpindex, frequencies, reenlightenment, reset, runtime, tlbflush improve Windows performance
3. **EFI/UEFI boot** (optional) -- Windows 11+ requires Secure Boot via SMM (already enabled in base spec)

```yaml
# Source: KubeVirt documentation + existing ocp_virt_vm pattern [ASSUMED]
- name: Build template spec base
  ansible.builtin.set_fact:
    vm_template_spec:
      domain:
        cpu:
          cores: "{{ vm_cpu_cores }}"
        memory:
          guest: "{{ vm_memory }}"
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
        devices:
          disks:
            - name: root-disk
              disk:
                bus: virtio
          interfaces:
            - name: default
              masquerade: {}
          rng: {}
        features:
          smm:
            enabled: true
          acpi: {}
          apic: {}
          hyperv:
            relaxed: {}
            vapic: {}
            spinlocks:
              spinlocks: 8191
            synic: {}
            vpindex: {}
            frequencies: {}
            reenlightenment: {}
            tlbflush: {}
            reset: {}
            runtime: {}
      networks:
        - name: default
          pod: {}
      volumes:
        - name: root-disk
          dataVolume:
            name: "{{ compute_instance_name }}-root-disk"
```

### Pattern 2: Sysprep Hostname via ConfigMap (create_secrets.yaml)

**What:** Creates a ConfigMap containing minimal unattend.xml for hostname setting, then mounts it as a sysprep volume in the VM spec.
**When to use:** When `vm_hostname` is set (extracted from ComputeInstance metadata.name).

```yaml
# Source: Microsoft docs (ComputerName element) + KubeVirt sysprep volume [ASSUMED for KubeVirt sysprep volume]
- name: Create sysprep ConfigMap with unattend.xml for hostname
  kubernetes.core.k8s:
    kubeconfig: "{{ remote_cluster_kubeconfig | default(omit) }}"
    state: present
    definition:
      apiVersion: v1
      kind: ConfigMap
      metadata:
        name: "{{ compute_instance_name }}-sysprep"
        namespace: "{{ compute_instance_target_namespace }}"
        labels: "{{ default_vm_labels }}"
      data:
        Unattend.xml: |
          <?xml version="1.0" encoding="utf-8"?>
          <unattend xmlns="urn:schemas-microsoft-com:unattend">
            <settings pass="specialize">
              <component name="Microsoft-Windows-Shell-Setup"
                         processorArchitecture="amd64"
                         publicKeyToken="31bf3856ad364e35"
                         language="neutral"
                         versionScope="nonSxS"
                         xmlns:wcm="http://schemas.microsoft.com/WMIConfig/2002/State">
                <ComputerName>{{ vm_hostname }}</ComputerName>
              </component>
            </settings>
          </unattend>

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

### Pattern 3: CloudBase-Init User-Data (create_secrets.yaml)

**What:** Delivers cloud-config YAML user-data to the Windows guest via CloudBase-Init.
**When to use:** When user provides a user-data secret reference. CloudBase-Init in the Windows image processes cloud-config YAML format (D-02 decision).

The existing `ocp_virt_vm` pattern uses `cloudInitNoCloud` volume type. CloudBase-Init supports the NoCloud data source, so the same volume type works for Windows guests.

```yaml
# Source: ocp_virt_vm/tasks/create_secrets.yaml (verified pattern) + CloudBase-Init NoCloud support [ASSUMED]
- name: Add cloud-init disk to template spec (for CloudBase-Init)
  ansible.builtin.set_fact:
    vm_template_spec: "{{ vm_template_spec | combine(cloud_init_patch, recursive=True, list_merge='append') }}"
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

### Pattern 4: Override Pattern (FQCN Reference Change)

**What:** Every override default must reference `osac.templates.windows_oci_vm` (not `ocp_virt_vm`).
**When to use:** In `create.yaml` and `delete.yaml` -- all step default definitions.

```yaml
# Source: ocp_virt_vm/tasks/create.yaml (verified pattern)
- name: Set create step defaults
  ansible.builtin.set_fact:
    create_step_secrets_default:
      name: osac.templates.windows_oci_vm    # <-- MUST be windows_oci_vm
      tasks_from: create_secrets.yaml
    create_step_modify_vm_spec_default:
      name: osac.templates.windows_oci_vm    # <-- MUST be windows_oci_vm
      tasks_from: create_modify_vm_spec.yaml
    # ... all other steps follow same pattern
```

### Anti-Patterns to Avoid

- **Sharing task files between ocp_virt_vm and windows_oci_vm:** Do not `include_role` from `ocp_virt_vm` within `windows_oci_vm`. Each template role must be self-contained. Overrides that reference `ocp_virt_vm` would break if the Linux template changes independently.
- **Hardcoding Windows image references:** The OCI image source must come from `ComputeInstance.spec.image.sourceRef` or `default_spec.image.sourceRef`, never hardcoded in task files.
- **Using SSH-based access checks for Windows:** The existing Linux template defaults to `22/tcp`. Windows must default to `3389/tcp` (RDP). Do not validate SSH connectivity for Windows VMs.
- **Modifying the existing ocp_virt_vm template:** Phase 1 creates a new role only. The existing Linux template must not be modified.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| VirtualMachine creation | Custom Python module | `kubernetes.core.k8s` with `apply: true` | Handles idempotency, dry-run, diff; already proven in codebase |
| DataVolume from OCI | Custom image pull logic | CDI DataVolume with `source.registry` | CDI handles image pull, conversion, PVC creation automatically |
| VM spec composition | String concatenation | Ansible `combine(patch, recursive=True, list_merge='append')` | Proven pattern for incremental spec building; handles nested dicts and lists correctly |
| Hostname in unattend.xml | Custom XML templating | Jinja2 inline template in ConfigMap data | Simple enough for single-element XML; no need for xml module |
| Wait for VM ready | Custom polling loop | `kubernetes.core.k8s_info` with `wait: true` and `wait_condition` | Built-in retry/timeout handling; cleaner than manual loops |
| Secret copying across namespaces | Manual base64 encode/decode | Copy `data` dict from source secret to new secret | Kubernetes secrets store data already base64-encoded; direct copy preserves encoding |

## Common Pitfalls

### Pitfall 1: Forgetting to Change FQCN References
**What goes wrong:** Override defaults still point to `osac.templates.ocp_virt_vm` instead of `osac.templates.windows_oci_vm`. Overrides work in testing (noop) but fail in production when the override target resolves to the Linux template.
**Why it happens:** Copy-paste from `ocp_virt_vm` without updating all 9 FQCN references (6 in create.yaml, 3 in delete.yaml).
**How to avoid:** After creating each file, grep for `ocp_virt_vm` -- there should be zero occurrences in the `windows_oci_vm` role.
**Warning signs:** Template name `ocp_virt_vm` appears anywhere in `windows_oci_vm` task files.

### Pitfall 2: ComputerName Length Exceeding 15 Characters
**What goes wrong:** Windows rejects hostnames longer than 15 bytes. The ComputeInstance `metadata.name` could be any length valid in Kubernetes (up to 253 chars).
**Why it happens:** Kubernetes resource names are DNS-compatible (up to 253 chars) but Windows NetBIOS names are limited to 15 bytes.
**How to avoid:** Truncate `vm_hostname` to 15 characters in `create_validate.yaml`. Document the limitation.
**Warning signs:** Windows VM boots with a random hostname instead of the configured one.

### Pitfall 3: Sysprep Volume Bus Type
**What goes wrong:** Using `bus: virtio` for the sysprep disk causes Windows to not find the unattend.xml during setup.
**Why it happens:** Windows Setup expects the sysprep answer file on a CD-ROM/floppy drive, not a virtio disk.
**How to avoid:** Use `cdrom: { bus: sata }` for the sysprep disk volume, not `disk: { bus: virtio }`.
**Warning signs:** Hostname is not set despite ConfigMap being created; Windows boots with default random hostname.

### Pitfall 4: Windows Boot Timeout
**What goes wrong:** Wait step times out because Windows takes longer to boot than Linux (especially first boot with sysprep).
**Why it happens:** Default `wait_timeout: 600` (10 minutes) may not be sufficient for Windows first boot + sysprep specialization + guest agent startup.
**How to avoid:** Increase `wait_timeout` to 900 or higher for Windows VMs.
**Warning signs:** Ansible task fails with timeout; VM is actually still booting.

### Pitfall 5: Missing virtio-win Drivers in Windows Image
**What goes wrong:** VM fails to boot or boots without disk/network because virtio drivers are not installed in the Windows OCI image.
**Why it happens:** Decision D-01 uses virtio bus for performance, but this requires drivers pre-installed in the image.
**How to avoid:** This is a prerequisite documented in CONTEXT.md. The template assumes drivers are present. Add a validation assertion or clear documentation.
**Warning signs:** VM boot loops or shows "No boot device found" in VNC console.

### Pitfall 6: CloudBase-Init Not Processing cloudInitNoCloud
**What goes wrong:** CloudBase-Init does not process user-data because it is not configured to use the NoCloud data source.
**Why it happens:** CloudBase-Init configuration in the Windows image must include `NoCloudConfigDriveService` or `HttpService` in its `metadata_services` list. If the image uses a different data source, `cloudInitNoCloud` volumes are ignored.
**How to avoid:** Ensure the Windows OCI image has CloudBase-Init configured with NoCloud data source support. This is an image build concern, not a template concern, but should be documented.
**Warning signs:** VM boots but hostname/user-data changes are not applied.

## Code Examples

### Windows-Specific Defaults (defaults/main.yaml)

```yaml
# Source: ocp_virt_vm/defaults/main.yaml (verified) with Windows adjustments [ASSUMED for sizing]
---
default_vm_internal_network: "hypershift"
default_vm_storage_class: "nfs-client"
default_vm_labels: "{{ {compute_instance_label: compute_instance_name} }}"

# Windows-specific defaults
default_arg_specs:
  exposed_ports: "3389/tcp"

# Windows requires more resources than Linux
default_spec:
  cores: 2
  memoryGiB: 4
  bootDisk:
    sizeGiB: 40
  image:
    sourceRef: "quay.io/containerdisks/windows:ltsc2022"
  runStrategy: "Always"
```

### Hostname Extraction in Validation (create_validate.yaml addition)

```yaml
# Source: ComputerName spec verified via Microsoft docs [CITED: learn.microsoft.com]
- name: Extract VM hostname from ComputeInstance metadata
  ansible.builtin.set_fact:
    vm_hostname: "{{ compute_instance.metadata.name | truncate(15, True, '') | upper }}"

- name: Log hostname truncation warning
  ansible.builtin.debug:
    msg: "WARNING: ComputeInstance name '{{ compute_instance.metadata.name }}' truncated to '{{ vm_hostname }}' for Windows hostname (15 char limit)"
  when: compute_instance.metadata.name | length > 15
```

### Minimal Unattend.xml for Hostname

```xml
<!-- Source: Microsoft docs [CITED: learn.microsoft.com/en-us/windows-hardware/customize/desktop/unattend/microsoft-windows-shell-setup-computername] -->
<?xml version="1.0" encoding="utf-8"?>
<unattend xmlns="urn:schemas-microsoft-com:unattend">
  <settings pass="specialize">
    <component name="Microsoft-Windows-Shell-Setup"
               processorArchitecture="amd64"
               publicKeyToken="31bf3856ad364e35"
               language="neutral"
               versionScope="nonSxS"
               xmlns:wcm="http://schemas.microsoft.com/WMIConfig/2002/State">
      <ComputerName>MYWINDOWSVM</ComputerName>
    </component>
  </settings>
</unattend>
```

### Windows Test Fixture (computeinstance-windows-test.yaml)

```yaml
# Source: computeinstance-test.yaml (verified) with Windows adjustments
---
apiVersion: osac.openshift.io/v1alpha1
kind: ComputeInstance
metadata:
  name: test-windows-vm
  namespace: osac-system
spec:
  templateID: osac.templates.windows_oci_vm
  cores: 2
  memoryGiB: 4
  bootDisk:
    sizeGiB: 40
  image:
    sourceType: registry
    sourceRef: "quay.io/containerdisks/windows:ltsc2022"
  runStrategy: "Always"
status:
  desiredConfigVersion: "1"
```

### Sysprep ConfigMap Cleanup in Delete (delete_resources.yaml addition)

```yaml
# Source: ocp_virt_vm/tasks/delete_resources.yaml soft-fail pattern (verified)
- name: Delete sysprep ConfigMap
  kubernetes.core.k8s:
    kubeconfig: "{{ remote_cluster_kubeconfig | default(omit) }}"
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

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| SATA/IDE disk bus for Windows VMs | Virtio with pre-installed drivers | KubeVirt v0.49+ (2022) | 2-3x disk I/O improvement; requires virtio-win in image |
| cloud-init for Windows | CloudBase-Init | CloudBase-Init 1.0+ (2020) | Native Windows service; supports cloud-config YAML, NoCloud data source |
| Manual VM configuration | KubeVirt common-templates | OpenShift Virt 4.10+ (2022) | Pre-built VM templates with Windows profiles; OSAC uses custom templates instead |
| Full sysprep for hostname | Minimal unattend.xml specialize pass | Windows Server 2016+ | Single-element XML avoids resetting activation and user state |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Enhanced Hyper-V features (synic, vpindex, frequencies, reenlightenment, tlbflush, reset, runtime) improve Windows performance in KubeVirt | Architecture Patterns, Pattern 1 | VM would still boot without them; performance may be suboptimal. Low risk -- these are standard KubeVirt Windows features. |
| A2 | Clock configuration (utc base, hpet disabled, hyperv timer, pit delay, rtc catchup) is required/recommended for Windows guests | Architecture Patterns, Pattern 1 | Windows may have time drift issues. Medium risk -- incorrect clock config causes time sync problems. |
| A3 | KubeVirt supports `sysprep` volume type with ConfigMap reference for unattend.xml delivery | Architecture Patterns, Pattern 2 | If not supported, hostname must be set via CloudBase-Init instead. Medium risk -- alternative approach exists. |
| A4 | Sysprep disk should use `cdrom: { bus: sata }` not `disk: { bus: virtio }` | Common Pitfalls, Pitfall 3 | Wrong bus type may prevent Windows from finding unattend.xml. Medium risk. |
| A5 | CloudBase-Init supports NoCloud data source (cloudInitNoCloud volume type) | Architecture Patterns, Pattern 3 | If CloudBase-Init in image uses different data source, user-data won't be processed. Medium risk -- depends on image build. |
| A6 | Windows default sizing: 4GiB RAM, 40GiB boot disk is adequate | Code Examples, defaults | Undersized VM would perform poorly. Low risk -- these are standard minimums for Windows Server. |
| A7 | `quay.io/containerdisks/windows:ltsc2022` is a valid container disk reference | Code Examples, test fixture | Default image reference may not exist; users must configure their own image source. Low risk -- it's only a default. |
| A8 | ComputerName truncation to 15 characters with uppercase is correct for Windows hostname | Code Examples, hostname extraction | Incorrect truncation could produce invalid hostname. Low risk -- 15-char limit is well-documented by Microsoft (verified). |
| A9 | cloudInitConfigDrive is less preferred than cloudInitNoCloud for CloudBase-Init | State of the Art | May need to use ConfigDrive for certain image configurations. Low risk -- either works. |

## Open Questions

1. **KubeVirt Sysprep Volume Support**
   - What we know: KubeVirt documentation mentions sysprep volume type for Windows VMs. Microsoft docs confirm the unattend.xml schema for ComputerName.
   - What's unclear: The exact KubeVirt API schema for `sysprep` volume type (ConfigMap vs Secret reference, field names). WebSearch and WebFetch were unavailable to verify the exact YAML structure.
   - Recommendation: Verify against KubeVirt API documentation or a running cluster before implementation. The planner should include a verification step in Wave 0.

2. **Windows OCI Image Availability**
   - What we know: The template uses `default_spec.image.sourceRef` as default image. Real users will configure their own registry path.
   - What's unclear: Whether `quay.io/containerdisks/windows:ltsc2022` exists or what the actual project registry path is.
   - Recommendation: Use a placeholder default and document that users must provide their own Windows OCI image with virtio-win drivers and CloudBase-Init pre-installed.

3. **CloudBase-Init Data Source Configuration**
   - What we know: CloudBase-Init supports multiple data sources. Decision D-02 specifies cloud-config YAML format.
   - What's unclear: Whether the target Windows images have CloudBase-Init configured with NoCloud data source support.
   - Recommendation: Document the image requirement. The template assumes NoCloud support. If images use a different data source, the user must configure CloudBase-Init in their image build.

4. **Hostname Truncation Strategy**
   - What we know: Windows limits hostnames to 15 bytes. Kubernetes resource names can be up to 253 characters.
   - What's unclear: Whether to truncate, hash, or reject names longer than 15 characters. Whether to force uppercase (Windows hostnames are case-insensitive).
   - Recommendation: Truncate to 15 characters. Do not force uppercase (Windows normalizes internally). Log a warning if truncation occurs.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Ansible playbook integration tests with Kind cluster |
| Config file | `tests/integration/run_tests.sh` + `common_vars.yml` |
| Quick run command | `ansible-playbook tests/integration/targets/compute_instance_create/tasks/baseline.yml -e "@tests/integration/common_vars.yml"` |
| Full suite command | `make test` (from repo root) |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PROV-01 | Boot from OCI image via DataVolume | integration (mocked) | Baseline test with noop resource override | No -- Wave 0 |
| PROV-02 | Sizing applied from ComputeInstance spec | integration (mocked) | Verify `vm_cpu_cores`, `vm_memory`, `vm_boot_disk_size` extracted | No -- Wave 0 |
| PROV-03 | Network connection to VirtualNetwork/Subnet | integration (mocked) | Verify `compute_instance_target_namespace` resolved | No -- Wave 0 (shares existing namespace resolution logic) |
| PROV-04 | Hostname set from metadata | integration (mocked) | Verify `vm_hostname` extracted and truncated | No -- Wave 0 |
| PROV-05 | Windows-optimized VM config | integration (mocked) | Verify `vm_template_spec` contains hyperv, clock, sysprep | No -- Wave 0 |

### Sampling Rate
- **Per task commit:** Run Windows baseline test only
- **Per wave merge:** Full test suite (`make test`)
- **Phase gate:** Full suite green before `/gsd-verify-work`

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | N/A -- template does not handle auth; AAP and K8s RBAC handle access |
| V3 Session Management | No | N/A -- stateless template execution |
| V4 Access Control | Yes (indirect) | K8s RBAC + namespace isolation; template uses `kubeconfig` for API access |
| V5 Input Validation | Yes | `ansible.builtin.assert` for param validation; hostname length check |
| V6 Cryptography | No | N/A -- no custom crypto; K8s TLS for API communication |

### Known Threat Patterns for Ansible + KubeVirt

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Unattend.xml injection via ComputeInstance name | Tampering | Validate hostname characters (Windows naming rules); truncate to 15 chars |
| Registry pull secret exposure | Information Disclosure | Secrets managed externally; template assumes pre-existing pull secrets in namespace |
| Privilege escalation via VM user-data | Elevation of Privilege | User-data content is user-controlled; template only copies it, does not generate it |
| Cross-namespace secret access | Information Disclosure | Secret copied from ComputeInstance namespace to VM namespace; both under same tenant RBAC |

## Sources

### Primary (HIGH confidence)
- **ocp_virt_vm template role** (16 files read in full) -- Verified all patterns, data flows, override mechanisms, and task structures
- **OSAC codebase analysis** (ARCHITECTURE.md, STRUCTURE.md, CONVENTIONS.md, STACK.md, CONCERNS.md, TESTING.md, INTEGRATIONS.md) -- Verified project conventions, naming patterns, test infrastructure
- **01-PATTERNS.md** -- Verified all 17 file analogs with exact line-level code references
- **01-CONTEXT.md** -- Locked decisions D-01 through D-05, discretion areas, canonical references
- **Microsoft docs** [CITED: learn.microsoft.com] -- ComputerName element: max 15 bytes, valid characters, specialize pass

### Tertiary (LOW confidence)
- **KubeVirt sysprep volume type** -- Based on training knowledge; KubeVirt supports sysprep volumes with ConfigMap/Secret references, but exact API schema not verified against current docs [ASSUMED]
- **CloudBase-Init NoCloud support** -- Based on training knowledge; CloudBase-Init supports NoCloud data source with cloud-config YAML, but not verified against current CloudBase-Init docs [ASSUMED]
- **Enhanced Hyper-V enlightenments list** -- Based on training knowledge of KubeVirt Windows VM best practices; not verified against current KubeVirt API [ASSUMED]
- **Clock configuration for Windows** -- Based on training knowledge of QEMU/KVM Windows optimization; not verified against current KubeVirt docs [ASSUMED]

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- All tools and libraries verified in existing codebase
- Architecture: HIGH -- All 17 files have exact analogs with line-level code references from PATTERNS.md
- Windows-specific configuration: MEDIUM -- Based on training knowledge of KubeVirt and Windows; key docs (KubeVirt, CloudBase-Init) could not be accessed via WebSearch/WebFetch
- Pitfalls: MEDIUM -- Derived from Windows VM operational experience; some pitfalls are assumed rather than verified against current docs

**Research date:** 2026-04-28
**Valid until:** 2026-05-28 (30 days -- stable domain; Ansible and KubeVirt APIs rarely break)
