# Phase 1: Windows VM Provisioning - Context

**Gathered:** 2026-05-02
**Status:** Ready for planning

<domain>
## Phase Boundary

Consolidate the shipped `windows_oci_vm` role into `ocp_virt_vm`, making `ocp_virt_vm` a unified compute template that provisions both Linux and Windows VMs. OS family is inferred automatically from a ComputeInstance annotation or image path heuristic, and drives all branching behavior (domain spec, initialization, secrets, delete cleanup, wait timeout). The standalone `windows_oci_vm` role is deleted entirely.

</domain>

<decisions>
## Implementation Decisions

### argument_specs.yaml — exposed_ports default
- **D-01:** Document OS-dependent defaults in the `exposed_ports` description field. Append a note: "Default is `22/tcp` for Linux and `3389/tcp` for Windows (applied at runtime via `guest_os_family`)." The static `default:` value stays as `22/tcp` (Linux role default before runtime override).

### Planning documentation
- **D-02:** Update all three planning documents — `PROJECT.md`, `RETROSPECTIVE.md`, and `MILESTONES.md` — to reflect the unified architecture. Key message: `ocp_virt_vm` handles both Linux and Windows via `guest_os_family` branching; single template, single OSAC catalog registration; OS family inferred automatically.

### Linux regression verification
- **D-03:** Run existing integration tests to verify the Linux path is unaffected by the consolidation. The integration test suite for `ocp_virt_vm` is the regression gate.

### ansible-lint compliance
- **D-04:** Verify lint compliance before committing. Run `ansible-lint` and `yamllint` against the modified files as part of the plan. Block commit on lint failure. Pre-commit hooks are already configured in the project.

### Carried forward from Phase 1 LEARNINGS.md (locked decisions) [informational]
- **D-05 [informational]:** Windows hostname truncated to 15 characters, no uppercase forcing (Windows normalizes case internally). Already implemented — verified by research.
- **D-06 [informational]:** Sysprep disk uses `cdrom` bus `sata` — required by Windows Setup; virtio bus not supported for sysprep media. Already implemented — verified by research.
- **D-07 [informational]:** Windows VM ready wait timeout is 900s (Windows first boot + sysprep takes significantly longer than Linux). Already implemented — verified by research.
- **D-08 [informational]:** SSH key injection is Linux-only; Windows uses RDP (port 3389). Already implemented — verified by research.
- **D-09 [informational]:** CloudBase-Init user-data delivered via `cloudInitNoCloud` volume — same as Linux cloud-init, no separate volume type needed. Already implemented — verified by research.
- **D-10 [informational]:** Soft-fail deletion pattern: `failed_when` with "not found" string check on all optional Kubernetes resource deletes. Already implemented — verified by research.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Role under modification
- `collections/ansible_collections/osac/templates/roles/ocp_virt_vm/` — Full role directory; all task, defaults, and meta files are in scope.
- `collections/ansible_collections/osac/templates/roles/ocp_virt_vm/tasks/infer_guest_os_family.yaml` — New task that sets `guest_os_family` from annotation, image heuristic, or default. Central to the branching mechanism.

### Planning docs to update
- `.planning/PROJECT.md` — Live project description consumed by future agents; must reflect unified architecture.
- `.planning/RETROSPECTIVE.md` — Milestone retrospective; update to describe consolidated approach.
- `.planning/MILESTONES.md` — Milestone delivery summary; update to reflect ocp_virt_vm unification.

### Phase history (read-only reference)
- `.planning/phases/01-windows-vm-provisioning/01-LEARNINGS.md` — Decisions, lessons, and patterns from the original Phase 1 that are locked (D-05 through D-10 above).
- `.planning/milestones/v1.0-phases/01-windows-vm-provisioning/01-RESEARCH.md` — Original research; pitfall list (sysprep bus, wait timeout, FQCN errors) still relevant as verification checklist.

### Test fixtures
- `tests/integration/fixtures/computeinstance-windows-test.yaml` — Windows test fixture; `templateID` already updated to `osac.templates.ocp_virt_vm`.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `ocp_virt_vm/tasks/infer_guest_os_family.yaml` — Already implemented; sets `guest_os_family` from `osac.openshift.io/guest-os-family` annotation or `containerdisks/windows` image path heuristic.
- `defaults/main.yaml` `_guest_os_windows_default_spec` / `_guest_os_windows_default_arg_specs` — Windows resource profile applied in `create.yaml` when `guest_os_family == 'windows'`.

### Established Patterns
- **Override/default dispatch:** Every create/delete step checks `*_override` before falling back to `*_default`. All overrides point to `osac.templates.ocp_virt_vm` (already correct in consolidated role).
- **Soft-fail deletion:** `register` + `failed_when` with "not found" check on optional resource deletes. Sysprep ConfigMap delete now includes this pattern (fixed in current branch).
- **`combine(recursive=True, list_merge='append')` for spec patching:** All OS-specific volumes/disks appended to base spec via this pattern. Verified correct — no duplicates possible since all disk/volume names are unique.

### Integration Points
- `playbook_osac_create_compute_instance.yml` — Dispatches via `templateID` → `include_role: name: "{{ template_id }}"`. No changes needed; `osac.templates.ocp_virt_vm` is the correct target for both OS families.
- `meta/osac.yaml` — Already updated with unified title and description. `template_type: compute_instance` unchanged.
- `meta/argument_specs.yaml` — Needs `exposed_ports` description updated per D-01.

</code_context>

<specifics>
## Specific Ideas

- The `exposed_ports` description update should read: `"Default is 22/tcp for Linux and 3389/tcp for Windows (applied at runtime via guest_os_family)."`
- Planning doc updates should emphasize: single template, single OSAC catalog registration, OS family inferred automatically from annotation or image path.
- ansible-lint must pass before the final commit; pre-commit hooks are the enforcement mechanism.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 1-windows-vm-provisioning*
*Context gathered: 2026-05-02*
