# Phase 01: ocp_virt_vm Consolidation - Pattern Map

**Mapped:** 2026-05-02
**Files analyzed:** 5
**Analogs found:** 5 / 5

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `collections/ansible_collections/osac/templates/roles/ocp_virt_vm/meta/argument_specs.yaml` | config | transform | Same file (existing `guest_os_family` entry uses the description-with-runtime-note pattern) | self-analog |
| `collections/ansible_collections/osac/templates/roles/ocp_virt_vm/tasks/delete_resources.yaml` | utility | CRUD | Same file (the existing soft-fail delete blocks are the analog for the remaining tasks) | self-analog |
| `.planning/PROJECT.md` | config | — | Existing PROJECT.md structure (sections, update instructions, key decisions table) | self-analog |
| `.planning/MILESTONES.md` | config | — | Existing MILESTONES.md structure (version block, key accomplishments list, key decisions list) | self-analog |
| `.planning/RETROSPECTIVE.md` | config | — | Existing RETROSPECTIVE.md structure (what was built, what worked, patterns established, key lessons) | self-analog |

All five files are modifications of existing files. The closest analog for each is the file itself — the patterns to follow are already present within each file and need to be continued, not introduced.

---

## Pattern Assignments

### `meta/argument_specs.yaml` — D-01: exposed_ports description update

**Analog:** The `guest_os_family` entry in the same file (lines 4-15), which establishes the convention of describing runtime-dependent behavior in the description field.

**Existing description pattern to copy from** (lines 11-15):
```yaml
        description: >
          OS family for the guest VM. If not supplied, the role infers from ComputeInstance
          annotation osac.openshift.io/guest-os-family (linux|windows) or from spec.image.sourceRef
          containing containerdisks/windows. "linux" uses cloud-init / SSH defaults; "windows"
          applies Windows sizing defaults, sysprep, Hyper-V / clock domain spec, and matching delete cleanup.
```

This establishes that runtime-conditional behavior belongs in the `description:` field using a folded scalar (`>`), not in a separate field.

**Target state for `exposed_ports` description block** (lines 49-56) — append the OS-dependent default sentence:
```yaml
          exposed_ports:
            description: >
              Ports to expose on the VM for ingress traffic.
              The syntax is a comma-separated list of `<port>/<protocol>` pairs, where `<protocol>` is either `tcp` or `udp`.
              For example, `22/tcp,80/tcp` will expose tcp ports 22 and 80 on the VM.
              Default is `22/tcp` for Linux and `3389/tcp` for Windows (applied at runtime via `guest_os_family`).
            type: str
            required: false
            default: "22/tcp"
```

**What must not change:** The `default: "22/tcp"` static value stays. Only the `description:` text changes (one sentence appended).

**Edit location:** Lines 50-53 of `collections/ansible_collections/osac/templates/roles/ocp_virt_vm/meta/argument_specs.yaml`. The folded scalar block ends before `type: str` on line 54.

---

### `tasks/delete_resources.yaml` — Remove orphaned "Delete cloud-init secret" task

**Analog:** The surrounding soft-fail delete tasks in the same file — specifically the `delete_user_data_secret` task (lines 93-105) and `delete_ssh_secret` task (lines 122-135), which demonstrate the correct pattern for Linux-specific optional resource deletion.

**Block to remove entirely** (lines 107-120):
```yaml
- name: Delete cloud-init secret (Linux)
  kubernetes.core.k8s:
    kubeconfig: "{{ remote_cluster_kubeconfig | default(omit) }}"
    api_version: v1
    kind: Secret
    name: "{{ compute_instance_name }}-cloud-init"
    namespace: "{{ compute_instance_target_namespace }}"
    state: absent
  register: delete_cloud_init_secret
  failed_when:
    - delete_cloud_init_secret.failed is defined
    - delete_cloud_init_secret.failed
    - "'not found' not in (delete_cloud_init_secret.msg | default(''))"
  when: guest_os_family == 'linux'
```

**Why this block is removed:** `create_secrets.yaml` never creates a secret named `{name}-cloud-init`. The Linux create flow creates `{name}-user-data` (when user-data secret ref is set) and `{name}-ssh-public-key` (when SSH key is present). The `-cloud-init` name has no create-side counterpart. The soft-fail pattern (`'not found' not in ...`) suppresses the resulting error at runtime, but the task is semantically incorrect. Removing it eliminates future confusion without any behavioral change.

**Correct create/delete resource symmetry after removal:**

| Resource | Created in | Deleted in | OS Gate |
|----------|-----------|------------|---------|
| `{name}-user-data` (Secret) | `create_secrets.yaml` | `delete_resources.yaml` lines 93-105 | None (both OS) |
| `{name}-ssh-public-key` (Secret) | `create_secrets.yaml` | `delete_resources.yaml` lines 122-135 | `linux` |
| `{name}-sysprep` (ConfigMap) | `create_secrets.yaml` | `delete_resources.yaml` lines 137-150 | `windows` |

**What must not change:** All other tasks in the file are correct and must remain unchanged.

---

### `.planning/PROJECT.md` — D-02: Reflect unified ocp_virt_vm architecture

**Analog:** The existing PROJECT.md structure — all sections, the key decisions table format, and the update instructions block at the bottom are the pattern to follow. The rewrite updates content within that structure, not the structure itself.

**Sections requiring content updates:**

1. **"What This Is" section** (lines 3-5): Replace `windows_oci_vm` and `implementationStrategy: windows_oci_vm` with the unified architecture description. Key message: `ocp_virt_vm` handles both Linux and Windows via `guest_os_family` branching; single template, single OSAC catalog registration; OS family inferred automatically from annotation or image path.

2. **"Current State" section** (lines 12-16): Replace "16-file Ansible role (`osac.templates.windows_oci_vm`)" with accurate description of the consolidated role. The `windows_oci_vm` role is deleted; `ocp_virt_vm` now serves both OS families.

3. **"Context" section** (lines 46-57): Replace `implementationStrategy: windows_oci_vm` references. Routing is via `template_id: osac.templates.ocp_virt_vm` in the ComputeInstance spec for both Linux and Windows.

4. **"Key Decisions" table** (lines 72-83): Replace the `implementationStrategy: windows_oci_vm` row. Add a row for the consolidation decision: `ocp_virt_vm` as unified template with `guest_os_family` branching.

**Existing table format to continue** (lines 72-74):
```yaml
| Decision | Rationale | Outcome |
|----------|-----------|---------|
| implementationStrategy: windows_oci_vm | Clear, descriptive name ... | ✓ Implemented |
```

**Replacement row content:**
```
| ocp_virt_vm as unified Linux+Windows template | Single template, single catalog registration; OS family inferred from annotation or image path; eliminates role duplication | ✓ Implemented (v1.1) |
```

**What must not change:** The "Evolution" section (lines 86-100) and the section headers and formatting conventions. The deferred items in "Out of Scope" remain accurate and should not change.

---

### `.planning/MILESTONES.md` — D-02: Reflect unified architecture

**Analog:** The existing v1.0 block format (lines 7-29) — version header, started/shipped/phases/plans/tasks metadata, numbered key accomplishments list, bulleted key decisions list, archive links.

**Content to update in the v1.0 block:**

1. **"Key accomplishments" list** (lines 14-19): Item 1 references "Created `windows_oci_vm` template role (16 files)". Replace with the consolidation accomplishment: merged `windows_oci_vm` into `ocp_virt_vm`, creating a unified Linux+Windows compute template.

2. **"Key decisions" list** (lines 22-27): Replace "`implementationStrategy: windows_oci_vm`" bullet with the consolidation decision. Keep the other decisions (sysprep disk as SATA CD-ROM, 900s timeout, etc.) — they remain accurate facts about Windows VM behavior.

**New v1.0 key accomplishments item 1 (replacement):**
```
1. Consolidated `windows_oci_vm` into `ocp_virt_vm` — unified Linux+Windows compute template via `guest_os_family` branching; single catalog registration, OS family inferred automatically from annotation or image path
```

**New key decision bullet (replacement for `implementationStrategy: windows_oci_vm`):**
```
- `ocp_virt_vm` as unified template — single OSAC catalog registration handles both Linux and Windows; OS family inferred from `osac.openshift.io/guest-os-family` annotation or `containerdisks/windows` image path heuristic
```

**What must not change:** The archive link (line 29), the structural metadata (started/shipped/phases/plans/tasks), and the remaining key decisions (sysprep SATA CD-ROM, 900s timeout, Phase 2 deferral) which remain accurate.

---

### `.planning/RETROSPECTIVE.md` — D-02: Reflect consolidated approach

**Analog:** The existing milestone retrospective block format (lines 5-37) — what was built, what worked, what was inefficient, patterns established, key lessons. The cross-milestone trends table and top lessons section (lines 40-52) are the pattern to continue.

**Sections requiring content updates:**

1. **"What Was Built" section** (lines 10-15): Replace `windows_oci_vm` references. The v1.1 (consolidation) built: unified `ocp_virt_vm` role with `guest_os_family` branching, `infer_guest_os_family.yaml` task, deletion of `windows_oci_vm` role, updated test fixture, updated planning docs.

2. **"Patterns Established" section** (lines 28-31): Add the OS-inference pattern: `infer_guest_os_family.yaml` as the standard entry point for OS-conditional branching in compute templates.

3. **Cross-milestone trends table** (lines 44-46): Add a v1.1 row documenting the consolidation.

**New cross-milestone trends row:**
```
| v1.1 | 1 | 1 | Consolidated windows_oci_vm into ocp_virt_vm; established unified Linux+Windows compute template pattern |
```

**What must not change:** The "What Worked", "What Was Inefficient", and "Key Lessons" sections from v1.0 remain accurate historical record and must not be altered. The "Top Lessons" list (lines 49-52) may be extended but not replaced.

---

## Shared Patterns

### argument_specs.yaml description convention
**Source:** `collections/ansible_collections/osac/templates/roles/ocp_virt_vm/meta/argument_specs.yaml` lines 11-15
**Apply to:** `exposed_ports` description field only
**Pattern:** Use folded scalar (`>`) for multi-sentence descriptions. Runtime-conditional behavior (OS-family-dependent values) belongs in the `description:` text, not in additional `default:` fields.

### Soft-fail delete pattern
**Source:** `collections/ansible_collections/osac/templates/roles/ocp_virt_vm/tasks/delete_resources.yaml` lines 93-105
**Apply to:** Any future optional resource delete task in delete_resources.yaml
```yaml
  register: delete_<resource>
  failed_when:
    - delete_<resource>.failed is defined
    - delete_<resource>.failed
    - "'not found' not in (delete_<resource>.msg | default(''))"
```
This three-condition pattern allows "not found" errors to pass silently while surfacing genuine API errors.

### Create/delete resource symmetry rule
**Source:** `tasks/create_secrets.yaml` and `tasks/delete_resources.yaml`
**Apply to:** All future delete task additions
**Rule:** Every resource name in a delete task must have a corresponding create task. Verify by grepping the resource name (e.g., `{name}-cloud-init`) across all `create_*.yaml` files before adding a delete task. If no create-side counterpart exists, the delete task must not be added.

### Planning doc update conventions
**Source:** `.planning/PROJECT.md` lines 86-100 (Evolution section)
**Apply to:** All three planning doc updates (PROJECT.md, MILESTONES.md, RETROSPECTIVE.md)
**Pattern:** Update content within existing section structure. Never remove sections or restructure headers. Add to "Key Decisions" tables rather than replacing existing rows when possible. Historical content (what worked/didn't in v1.0) is preserved as-is.

---

## No Analog Found

None — all five files have clear analogs (self-analogs in all cases, since all are modifications of existing files with established internal patterns).

---

## Metadata

**Analog search scope:** `collections/ansible_collections/osac/templates/roles/ocp_virt_vm/`, `.planning/`
**Files scanned:** 5 (all modified files read in full; no files > 2,000 lines)
**Pattern extraction date:** 2026-05-02
