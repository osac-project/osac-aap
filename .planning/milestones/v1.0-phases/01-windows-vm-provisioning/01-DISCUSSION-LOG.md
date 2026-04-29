# Phase 1: Windows VM Provisioning - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-28
**Phase:** 1-Windows VM Provisioning
**Areas discussed:** VM spec differences from Linux, Template file structure, Hostname setting mechanism

---

## VM Spec Differences from Linux

### Question 1: Disk Bus Configuration

| Option | Description | Selected |
|--------|-------------|----------|
| virtio (Recommended) | Best performance, requires virtio-win drivers in Windows image - matches KubeVirt best practices | ✓ |
| sata | Lower performance but more compatible - no special drivers needed | |
| You decide | Claude picks based on OpenShift Virtualization standards | |

**User's choice:** virtio (Recommended)
**Notes:** Chose virtio for best performance, aligning with KubeVirt best practices. Assumes Windows OCI images have virtio-win drivers pre-installed.

### Question 2: CloudBase-Init User-Data Format

| Option | Description | Selected |
|--------|-------------|----------|
| cloud-config YAML (Recommended) | CloudBase-Init supports cloud-config format - similar to Linux cloud-init, easier to maintain | ✓ |
| PowerShell script | Batch/PowerShell in user-data - more flexible but harder to template | |
| You decide | Claude picks based on CloudBase-Init documentation | |

**User's choice:** cloud-config YAML (Recommended)
**Notes:** Selected cloud-config YAML for consistency with Linux patterns and easier template maintenance.

---

## Template File Structure

### Question: Duplicate or Share Task Files

| Option | Description | Selected |
|--------|-------------|----------|
| Duplicate all 13 files (Recommended) | Independent template - easier to customize Windows-specific behavior without affecting Linux VMs | |
| Share common tasks via parameters | Parameterize OS differences - less code duplication but more complex logic | |
| You decide | Claude picks based on OSAC template patterns | ✓ |

**User's choice:** You decide
**Notes:** User deferred to Claude. Recommendation: start with duplication for clarity, refactor to shared logic if patterns emerge in v2.

---

## Hostname Setting Mechanism

### Question: Hostname Configuration Method

| Option | Description | Selected |
|--------|-------------|----------|
| CloudBase-Init user-data (Recommended) | Set hostname in cloud-config YAML - handled during first boot, clean and declarative | |
| Sysprep unattend.xml | Requires sysprep automation - deferred to v2 per PROJECT.md | ✓ |
| You decide | Claude picks based on CloudBase-Init capabilities | |

**User's choice:** Sysprep unattend.xml
**Notes:** User clarified: "Just hostname via unattend.xml file" - minimal sysprep for hostname only, NOT full sysprep automation. This stays in Phase 1 scope.

---

## Claude's Discretion

- **Template file structure:** Whether to duplicate all task files from ocp_virt_vm or parameterize OS differences

## Deferred Ideas

None — discussion stayed within phase scope. Sysprep automation (beyond minimal hostname setting) remains deferred to v2 per PROJECT.md.
