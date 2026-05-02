---
phase: 01
phase_name: "windows-vm-provisioning"
project: "Windows VM Provisioning for OpenShift Virtualization"
generated: "2026-04-30"
counts:
  decisions: 9
  lessons: 3
  patterns: 5
  surprises: 3
missing_artifacts: []
---

# Phase 01 Learnings: windows-vm-provisioning

## Decisions

### Copy-and-modify approach from ocp_virt_vm
Decided to create the windows_oci_vm role by copying the existing ocp_virt_vm role structure (16 files) and making targeted modifications rather than building from scratch. This preserves the override pattern, maintains structural parity (identical file names), and ensures the new template integrates seamlessly with existing OSAC orchestration.

**Rationale:** Structural parity means developers familiar with ocp_virt_vm can navigate windows_oci_vm, and the same testing patterns apply. Only two categories of changes were needed: FQCN updates (ocp_virt_vm -> windows_oci_vm) and OS-specific defaults/logic.
**Source:** 01-01-PLAN.md, 01-01-SUMMARY.md

---

### Windows hostname truncated to 15 characters without uppercase forcing
Decided to truncate the ComputeInstance metadata.name to 15 characters for the Windows hostname (NetBIOS limit) but not force uppercase, because Windows normalizes case internally.

**Rationale:** Per RESEARCH.md findings (Open Question 4), Windows handles case normalization itself. Forcing uppercase in the template would create a mismatch between the configured hostname and what Windows actually reports. The 15-character truncation is mandatory per NetBIOS specification.
**Source:** 01-02-PLAN.md, 01-02-SUMMARY.md

---

### Sysprep disk uses cdrom bus sata, not disk bus virtio
Windows Setup expects the unattend.xml answer file on a CD-ROM drive. Using virtio bus for the sysprep disk would cause Windows Setup to fail silently during the specialize pass.

**Rationale:** This was identified as Pitfall 3 during research. KubeVirt's sysprep volume type mounts content as an ISO, which must be presented to the guest via SATA CD-ROM for Windows to detect it.
**Source:** 01-02-PLAN.md, 01-02-SUMMARY.md

---

### VM wait timeout increased from 600 to 900 seconds
Windows first boot with sysprep execution takes significantly longer than Linux boot, requiring a 900-second (15-minute) wait timeout instead of the default 600 seconds.

**Rationale:** Identified as Pitfall 4 during research. Windows sysprep runs during first boot and includes disk setup, driver installation, and the specialize pass. 600 seconds is insufficient and would cause false timeout failures.
**Source:** 01-02-PLAN.md, 01-02-SUMMARY.md

---

### SSH key handling omitted for Windows VMs
The create_secrets.yaml for Windows omits the SSH key propagation and accessCredentials blocks present in ocp_virt_vm. Windows VMs use RDP (port 3389), not SSH.

**Rationale:** SSH is not a native Windows service. Including SSH key injection would create unused resources and mislead operators. CloudBase-Init user-data (via cloudInitNoCloud) is the appropriate channel for custom Windows configuration.
**Source:** 01-02-PLAN.md, 01-02-SUMMARY.md

---

### CloudBase-Init user-data via cloudInitNoCloud volume type
CloudBase-Init can consume the same cloudInitNoCloud volume type with cloud-config YAML format that Linux cloud-init uses. No separate volume type is needed for Windows user-data delivery.

**Rationale:** CloudBase-Init implements the OpenStack ConfigDrive and NoCloud data sources, making it compatible with KubeVirt's cloudInitNoCloud volume. This enables the same user-data secret copy pattern used in ocp_virt_vm.
**Source:** 01-02-PLAN.md, 01-02-SUMMARY.md

---

### Enhanced Hyper-V enlightenments (7 additional features)
Added synic, vpindex, frequencies, reenlightenment, tlbflush, reset, and runtime to the base Hyper-V features (relaxed, vapic, spinlocks) already present in ocp_virt_vm.

**Rationale:** These paravirtualized features improve Windows guest performance on KVM/KubeVirt. Without them, Windows runs in a degraded mode with software-emulated timers and interrupt handling, resulting in significantly worse I/O and scheduling performance.
**Source:** 01-02-PLAN.md, 01-02-SUMMARY.md

---

### create_resources.yaml kept as OS-agnostic verbatim copy
The resource creation file (DataVolume + VirtualMachine CR) was copied verbatim from ocp_virt_vm with zero changes, demonstrating clean separation of concerns.

**Rationale:** All Windows-specific configuration is built upstream in create_build_spec.yaml (VM spec) and create_secrets.yaml (sysprep + user-data). By the time create_resources.yaml runs, vm_template_spec already contains all OS-specific settings. This separation means future OS templates only need to modify spec construction, not resource creation.
**Source:** 01-02-PLAN.md, 01-02-SUMMARY.md

---

### Test fixture name kept under 15 characters
Used "test-windows-vm" (15 chars exactly) to avoid triggering hostname truncation warnings during integration tests.

**Rationale:** A fixture name longer than 15 chars would produce a truncation warning on every test run, which is noise rather than signal. The fixture should exercise the happy path; truncation can be tested separately.
**Source:** 01-03-PLAN.md, 01-03-SUMMARY.md

---

## Lessons

### Orphaned resource cleanup tasks survive FQCN verification
UAT discovered that delete_resources.yaml contained orphaned delete tasks for SSH key secret ({name}-ssh-public-key) and cloud-init secret ({name}-cloud-init) that are never created by the Windows VM role. These were blindly copied from ocp_virt_vm. The automated verification checked for zero ocp_virt_vm string references but did not catch semantically incorrect blocks — deleting resources that the create flow never produces.

**Context:** The FQCN grep verification (zero ocp_virt_vm occurrences) passed because the orphaned tasks used generic variable names, not role-specific FQCNs. Static string matching cannot detect semantic mismatches between create and delete flows. This was classified as a major severity issue during UAT and required inline fix.
**Source:** 01-UAT.md (Test 10)

---

### Wave dependencies require explicit merge in parallel worktrees
When Plan 03 (wave 3) ran in a parallel worktree, it started at the planning base commit without wave 1 and wave 2 execution artifacts. The role directory didn't exist, blocking all verification tasks. Required manually merging prior wave commits before proceeding.

**Context:** Each worktree starts from the same base commit. When a plan has `depends_on: [02]`, the executor must merge prior wave commits into the worktree before the dependent plan can run. This is expected behavior for parallel wave execution but must be handled explicitly — it's not automatic.
**Source:** 01-03-SUMMARY.md (Deviations section)

---

### Thorough upfront research eliminates execution deviations
Plans 01 and 02 both executed exactly as written with zero deviations. The extensive research phase (01-RESEARCH.md identifying pitfalls, decisions, and open questions) and pattern analysis (01-PATTERNS.md mapping ocp_virt_vm structure) meant no surprises during execution.

**Context:** The research phase identified 5 specific pitfalls (FQCN copy-paste errors, hostname truncation, sysprep bus type, wait timeout, sysprep cleanup) and 5 design decisions upfront. All were addressed in the plan specifications, resulting in predictable execution. The only issue found was in UAT (orphaned delete tasks), which was a semantic gap the plans didn't anticipate.
**Source:** 01-01-SUMMARY.md, 01-02-SUMMARY.md

---

## Patterns

### Override/default dispatch for role step customization
Each step in the create and delete flows uses an override/default dispatch pattern: the orchestration file checks for a `*_override` variable and falls back to `*_default`. This enables downstream customization without modifying the core role.

**When to use:** When creating Ansible roles that need extensibility points. Each step (secrets, resources, hooks, etc.) can be individually overridden by setting a variable before role invocation. The no-op hook files (create_pre_create_hook.yaml, etc.) provide documented extension points.
**Source:** 01-01-PLAN.md, 01-VERIFICATION.md

---

### Soft-fail deletion for optional Kubernetes resources
Resource cleanup tasks use `failed_when` with a "not found" string check to gracefully handle already-deleted or never-created resources. Pattern: `failed_when: [result.failed is defined, result.failed, "'not found' not in (result.msg | default(''))"]`.

**When to use:** When deleting Kubernetes resources that may or may not exist (e.g., optional user-data secrets, sysprep ConfigMaps). Prevents the delete flow from failing when a resource was already cleaned up or was never created due to an optional configuration path.
**Source:** 01-02-PLAN.md, 01-02-SUMMARY.md

---

### Template creation via structural copy-and-specialize
New OSAC compute templates are created by copying an existing role and making targeted modifications: (1) FQCN updates in orchestration files, (2) OS-specific defaults in config files, (3) OS-specific logic in substantive task files. The file structure (16 files across defaults/, meta/, tasks/) remains identical.

**When to use:** When adding a new OS template (e.g., Ubuntu, RHEL, SUSE). Copy ocp_virt_vm or windows_oci_vm, update FQCNs globally, modify defaults/main.yaml for OS-appropriate values, and adapt the substantive task files (validate, build_spec, secrets, delete_resources) for OS-specific behavior. create_resources.yaml and orchestration files remain unchanged.
**Source:** 01-01-PLAN.md, 01-02-PLAN.md, 01-VERIFICATION.md

---

### OSAC template discovery via meta/osac.yaml
Templates register with the OSAC system via a `template_type: compute_instance` field in `meta/osac.yaml`. The `osac.service.enumerate_templates` service discovers all roles with this metadata. Title and description in this file control how the template appears in the OSAC catalog.

**When to use:** When creating any new OSAC template role. The `meta/osac.yaml` file with `template_type` field is required for the template to be discoverable. Without it, the role exists but cannot be dispatched by the OSAC orchestration layer.
**Source:** 01-01-PLAN.md, 01-01-SUMMARY.md

---

### Three-wave plan decomposition (skeleton -> implementation -> verification)
The phase was decomposed into three sequential plans: Wave 1 (role skeleton with config and orchestration files), Wave 2 (substantive task files with OS-specific logic), Wave 3 (test fixture and final verification). Each wave builds on the previous and can be independently verified.

**When to use:** When building a new component from scratch that has clear structural layers. The skeleton wave establishes directory structure and wiring, the implementation wave fills in business logic, and the verification wave confirms everything integrates correctly. This decomposition enables parallel execution of independent waves and clear dependency tracking.
**Source:** 01-01-PLAN.md, 01-02-PLAN.md, 01-03-PLAN.md

---

## Surprises

### Semantic delete-flow errors survive comprehensive automated verification
Despite thorough automated verification (16 artifact checks, 10 key link verifications, 5 data flow traces, FQCN count verification), the orphaned SSH key and cloud-init secret delete tasks survived until UAT. Automated verification caught string-level issues (wrong FQCN, missing files, wrong defaults) but could not detect that delete_resources.yaml was deleting resources that create_secrets.yaml never creates.

**Impact:** Major severity UAT finding required inline fix. Demonstrates that automated verification based on string matching and file existence is necessary but not sufficient — semantic review of create/delete flow symmetry needs explicit UAT test cases. Future template creation should include a "delete-only-what-you-create" verification step.
**Source:** 01-UAT.md (Test 10)

---

### Zero plan deviations across Plans 01 and 02
Both Plans 01 and 02 executed exactly as written with no deviations — every file was created exactly as specified, every verification passed on first attempt. This is unusual for implementation work and suggests the upfront research phase (01-RESEARCH.md) and pattern analysis (01-PATTERNS.md) were exceptionally thorough.

**Impact:** Positive — validates the GSD workflow's invest-in-research approach. The ~10 minutes of research and planning saved debugging time during execution. The only issue found was in UAT (Test 10), which was a gap in the plan specification itself, not an execution deviation.
**Source:** 01-01-SUMMARY.md, 01-02-SUMMARY.md

---

### Total execution time of ~10 minutes for 17 files
All three plans completed in approximately 10 minutes total (3 + 3 + 4 minutes), producing 16 role files and 1 test fixture. The template-based approach (copy from ocp_virt_vm) enabled very fast execution compared to greenfield development.

**Impact:** Demonstrates that the copy-and-specialize pattern for OSAC templates enables rapid template development. The next OS template (e.g., Ubuntu, RHEL) should be similarly fast, especially now that the pattern is documented and the windows_oci_vm role provides a second reference implementation alongside ocp_virt_vm.
**Source:** 01-01-SUMMARY.md, 01-02-SUMMARY.md, 01-03-SUMMARY.md
