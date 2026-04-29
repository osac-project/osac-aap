# Phase 1: Windows VM Provisioning - Context

**Gathered:** 2026-04-28
**Status:** Ready for planning

## Phase Boundary

Create an Ansible template role (`osac.templates.windows_oci_vm`) that provisions Windows virtual machines in OpenShift Virtualization from OCI container images. The template must handle Windows-specific configuration (virtio-win drivers, CloudBase-Init, hostname setting) while following the established `ocp_virt_vm` pattern for Linux VMs.

**In scope:**
- Boot Windows VMs from OCI container images via DataVolume registry source
- Apply CPU, memory, and disk sizing from ComputeInstance spec
- Connect VMs to specified VirtualNetwork and Subnet
- Set Windows hostname from ComputeInstance metadata
- Create VirtualMachine CR with Windows-optimized configuration (virtio drivers, Hyper-V enlightenments)

**Out of scope (deferred to Phase 2 or later milestones):**
- VM verification tasks (network, RDP, guest agent, VNC) - Phase 2
- Active Directory domain join - v2
- Windows license activation - v2
- PowerShell script execution - v2
- Full sysprep automation - v2

## Implementation Decisions

### VM Specification (Windows-specific)
- **D-01:** Disk bus configuration uses **virtio** for best performance (requires virtio-win drivers in Windows image, aligns with KubeVirt best practices)
- **D-02:** CloudBase-Init user-data format is **cloud-config YAML** (similar to Linux cloud-init, easier to template and maintain than PowerShell scripts)
- **D-03:** Hyper-V enlightenments configuration **reused from ocp_virt_vm template** (already optimized for Windows: relaxed, vapic, spinlocks)

### Hostname Configuration
- **D-04:** Windows hostname set via **sysprep unattend.xml** (minimal sysprep for hostname only, not full automation)
- **D-05:** Unattend.xml embedded in CloudBase-Init user-data or as separate ConfigMap/Secret (planner determines best approach)

### Claude's Discretion
- **Template file structure:** Claude decides whether to duplicate all 13 task files from `ocp_virt_vm` or parameterize OS differences. Consider: independent Windows template (easier customization) vs. shared logic (less duplication). Recommendation: start with duplication for clearer separation, refactor to shared logic if patterns emerge in v2.

## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### OSAC Template Patterns
- `collections/ansible_collections/osac/templates/roles/ocp_virt_vm/` — Reference implementation for Linux VMs (13 task files, override pattern)
- `collections/ansible_collections/osac/service/roles/` — Reusable service roles (finalizer, lease, wait_for, common)
- `.planning/codebase/ARCHITECTURE.md` — Override pattern documentation, template dispatch mechanism

### Windows-Specific Documentation
- CloudBase-Init cloud-config format — web research required for user-data schema
- KubeVirt Windows guest configuration — web research required for virtio drivers, Hyper-V enlightenments
- Sysprep unattend.xml schema for hostname — web research required for minimal XML structure

## Existing Code Insights

### Reusable Assets
- **ocp_virt_vm template (13 task files):** Provides proven pattern for VM provisioning with override support at each step
  - `create.yaml` — Main orchestration with 6 overrideable steps
  - `create_build_spec.yaml` — Build VM template spec base
  - `create_modify_vm_spec.yaml` — Apply customizations to VM spec
  - `create_resources.yaml` — Create VirtualMachine and DataVolume CRs
  - `create_validate.yaml` — Validate params and VM config
  - `create_wait_annotate.yaml` — Wait for VM ready, annotate ComputeInstance
  - `create_secrets.yaml` — Handle registry pull secrets
  - `create_pre_create_hook.yaml`, `create_post_create_hook.yaml` — Extension points
  - `delete.yaml`, `delete_resources.yaml`, `delete_pre_delete_hook.yaml`, `delete_post_delete_hook.yaml` — Deletion flow

- **osac.service.common role:** Provides `get_remote_cluster_kubeconfig.yaml` for multi-cluster access
- **kubernetes.core collection:** CRD manipulation via `kubernetes.core.k8s` module

### Established Patterns
- **Override pattern:** Each step defines `{step_name}_default` and checks for `{step_name}_override` to enable customer customization without forking
- **Dynamic dispatch:** Template selected via `implementationStrategy` field in ComputeInstance spec (`windows_oci_vm`)
- **Finalizer pattern:** Add finalizer at workflow start, remove after cleanup (prevents premature deletion)
- **Lease pattern:** Acquire resource lock with unique holder ID, release at completion/failure (prevents concurrent modifications)

### Integration Points
- **Entry point:** `playbook_osac_create_compute_instance.yml` (root) → `osac.workflows.compute_instance.create` → dynamic include_role(`osac.templates.{{ implementation_strategy }}`)
- **Workflow orchestration:** `collections/ansible_collections/osac/workflows/playbooks/compute_instance/create.yml`
- **Service roles used:** finalizer (add/remove), lease (acquire/release), wait_for (VM ready state)
- **ComputeInstance spec extraction:** `ansible_eda.event.payload.spec` contains sizing, network, template parameters
- **Target namespace:** Determined by `osac.openshift.io/subnet-target-namespace` annotation or tenant namespace

## Specific Ideas

- **User-data delivery:** CloudBase-Init user-data can be injected via ConfigMap or Secret referenced in VirtualMachine spec (similar to cloud-init for Linux)
- **virtio-win drivers assumption:** Windows OCI images MUST include virtio-win drivers pre-installed (template does not install drivers, only configures disk bus)
- **Hostname in unattend.xml:** Minimal sysprep configuration with `<ComputerName>` element only (not full sysprep automation)

## Deferred Ideas

None — discussion stayed within phase scope

---

*Phase: 1-Windows VM Provisioning*
*Context gathered: 2026-04-28*
