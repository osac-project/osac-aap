# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

## Milestone: v1.0 — Windows VM Provisioning

**Shipped:** 2026-04-29
**Phases:** 1 | **Plans:** 3

### What Was Built
- Complete `windows_oci_vm` Ansible template role (16 files, ~732 lines YAML) for provisioning Windows VMs on OpenShift Virtualization
- Windows-specific VM configuration: sysprep hostname (15-char truncation), 10 Hyper-V enlightenments, Windows clock config, SATA CD-ROM for sysprep, 900s ready timeout
- CloudBase-Init user-data delivery via cloudInitNoCloud volume type
- Windows ComputeInstance test fixture for integration testing
- Templates README documentation with `windows_oci_vm` section and corrected `template_type` instructions

### What Worked
- **Following the ocp_virt_vm pattern** reduced implementation risk — identical 16-file structure meant the orchestration layer required zero new logic
- **Early UAT** caught an orphaned delete task bug (SSH key + cloud-init secret deletion copied from Linux role) before it could cause issues in production
- **Investigating Linux parity before Phase 2** revealed that deeper VM verification was net-new capability, not a gap — saved an entire phase of unnecessary work
- **Code review + security threat verification** during execution caught real issues (missing kubeconfig param, error suppression in sysprep cleanup, hostname truncation bug)

### What Was Inefficient
- **Phase 2 was planned before investigating Linux parity** — if we had checked `ocp_virt_vm`'s verification level during requirements, Phase 2 would never have been scoped
- **Copy-paste from ocp_virt_vm** left orphaned resources in `delete_resources.yaml` (SSH key and cloud-init secret tasks) that only UAT caught — a systematic diff check during Plan 02 would have prevented this

### Patterns Established
- Windows VM templates use sysprep ConfigMap + unattend.xml for hostname setting (not cloud-init)
- Sysprep disks must use `cdrom: bus: sata` (Windows Setup requirement)
- Windows VM ready timeout should be 900s (vs 600s for Linux)
- Template `template_type` must be `compute_instance` (not `vm`) — TemplateTypeEnum in `find_template_roles.py` only accepts `cluster`, `compute_instance`, `network`

### Key Lessons
1. **Always investigate existing parity before planning new phases** — the Phase 2 removal saved significant effort because we discovered Linux VMs have no deeper verification either
2. **Copy-paste from reference implementations requires a systematic cleanup pass** — delete_resources.yaml had Linux-specific tasks that don't apply to Windows
3. **README documentation should be updated alongside code, not deferred** — the `template_type: vm` error in the README template instructions could have misled future template authors

---

## Milestone: v1.1 — ocp_virt_vm Consolidation

**Shipped:** 2026-05-02
**Phases:** 1 | **Plans:** 3

### What Was Built
- Unified `ocp_virt_vm` Ansible template role: handles both Linux and Windows VMs via `guest_os_family` branching
- `infer_guest_os_family.yaml` task: infers OS family from `osac.openshift.io/guest-os-family` annotation or `containerdisks/windows` image path heuristic
- Deleted `windows_oci_vm` role directory (16 files) — single unified template replaces it
- Removed orphaned "Delete cloud-init secret" task: create/delete symmetry established for all resources
- Updated `exposed_ports` argument_specs description with OS-dependent default note

### What Worked
- **Research-first approach** — RESEARCH.md verified exactly which decisions were done vs. missing before any code was touched; no guessing about implementation state
- **PATTERNS.md specificity** — exact line numbers and target text in each pattern assignment meant executor tasks needed zero codebase exploration

### What Was Inefficient
- None identified — phase scope was well-defined from the start

### Patterns Established
- `infer_guest_os_family.yaml` as the standard entry point for OS-conditional branching in compute templates — always include before any task that checks `guest_os_family`
- Create/delete resource symmetry rule: grep every resource name in delete_resources.yaml against all create_*.yaml files before adding a delete task
- argument_specs.yaml description convention: runtime-conditional behavior belongs in the `description:` folded scalar, not in additional default fields

### Key Lessons
1. **Verify implementation state before planning** — the research phase showed D-05 through D-10 were already done; planning only covered the gaps
2. **Orphaned delete tasks are invisible at runtime** — the soft-fail pattern silences them; systematic create/delete audits are the only way to catch them

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Phases | Plans | Key Change |
|-----------|--------|-------|------------|
| v1.0 | 1 | 3 | Established Windows VM provisioning pattern; scoped verification to existing Linux parity |
| v1.1 | 1 | 3 | Consolidated windows_oci_vm into ocp_virt_vm; established unified Linux+Windows compute template pattern |

### Top Lessons (Verified Across Milestones)

1. Investigate existing patterns before planning new work — avoids unnecessary phases
2. Copy-paste requires systematic review — orphaned resources from reference implementations cause bugs
