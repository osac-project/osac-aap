# Phase 01: ocp_virt_vm Consolidation - Research

**Researched:** 2026-05-02
**Domain:** Ansible role consolidation — merging windows_oci_vm into ocp_virt_vm
**Confidence:** HIGH (all findings verified against working tree; no external lookups needed)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Document OS-dependent defaults in `exposed_ports` description. Append: "Default is `22/tcp` for Linux and `3389/tcp` for Windows (applied at runtime via `guest_os_family`)." Static `default:` value stays as `22/tcp`.
- **D-02:** Update PROJECT.md, RETROSPECTIVE.md, and MILESTONES.md to reflect unified architecture. Key message: `ocp_virt_vm` handles both Linux and Windows via `guest_os_family` branching; single template, single OSAC catalog registration; OS family inferred automatically.
- **D-03:** Run existing integration tests to verify the Linux path is unaffected.
- **D-04:** Verify lint compliance before committing. Run `ansible-lint` and `yamllint`. Block commit on lint failure. Pre-commit hooks are already configured.
- **D-05:** Windows hostname truncated to 15 characters, no uppercase forcing.
- **D-06:** Sysprep disk uses `cdrom` bus `sata`.
- **D-07:** Windows VM ready wait timeout is 900s.
- **D-08:** SSH key injection is Linux-only.
- **D-09:** CloudBase-Init user-data delivered via `cloudInitNoCloud` volume.
- **D-10:** Soft-fail deletion pattern: `failed_when` with "not found" string check on optional deletes.

### Claude's Discretion

None — all decisions are locked.

### Deferred Ideas (OUT OF SCOPE)

None.
</user_constraints>

---

## Summary

This phase consolidates the `windows_oci_vm` role (deleted in the working tree) into `ocp_virt_vm`. The working tree already contains the bulk of the implementation: `infer_guest_os_family.yaml` is complete and correct, Windows domain spec branching is implemented, sysprep secrets use the right bus type, wait timeout is OS-conditional, delete cleanup is OS-gated, and the test fixture points to `osac.templates.ocp_virt_vm`. The `windows_oci_vm` role directory is fully deleted.

Two decisions from CONTEXT.md are NOT yet implemented: D-01 (`exposed_ports` description update in `argument_specs.yaml`) and D-02 (planning docs — PROJECT.md, MILESTONES.md, RETROSPECTIVE.md — still describe the old `windows_oci_vm` architecture). Everything else is done and correct.

One pre-existing issue exists in `delete_resources.yaml`: a "Delete cloud-init secret" task deletes a secret named `{name}-cloud-init` that `create_secrets.yaml` never creates. This orphaned delete task predates the current branch and does not affect correctness (the soft-fail pattern handles the "not found" case), but a plan should include fixing it as part of the cleanup to avoid future confusion.

**Primary recommendation:** The plan needs two code edits (D-01 and the orphaned delete task) and three planning doc rewrites (D-02), then lint verification and Linux regression test confirmation.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| OS family inference | Role tasks (ocp_virt_vm) | ComputeInstance annotation / image path | Logic lives in `infer_guest_os_family.yaml`; reads annotation then image heuristic |
| Windows domain spec | Role tasks (create_build_spec.yaml) | defaults/main.yaml (profile values) | Spec branching at build time; OS-specific Hyper-V clock/timer config |
| Sysprep hostname | Role tasks (create_secrets.yaml) | Kubernetes ConfigMap | ConfigMap with unattend.xml; SATA CD-ROM disk added to spec |
| SSH key injection | Role tasks (create_secrets.yaml) | Kubernetes Secret | Linux-only gate (`when: guest_os_family == 'linux'`) |
| Wait timeout | Role tasks (create_wait_annotate.yaml) | — | Inline ternary `900 if guest_os_family == 'windows' else 600` |
| Delete cleanup | Role tasks (delete_resources.yaml) | — | OS-gated `when:` conditions on optional resource deletes |
| OSAC template dispatch | Playbook (playbook_osac_create_compute_instance.yml) | — | `include_role: name: "{{ template_id }}"` — no changes needed |

---

## Decision Audit: What Is Done vs. What Is Missing

### D-01: exposed_ports description update — NOT DONE

**Status:** GAP — the description in `meta/argument_specs.yaml` is identical before and after the branch.

Current text (unchanged from baseline):
```
description: >
  Ports to expose on the VM for ingress traffic.
  The syntax is a comma-separated list of `<port>/<protocol>` pairs, where `<protocol>` is either `tcp` or `udp`.
  For example, `22/tcp,80/tcp` will expose tcp ports 22 and 80 on the VM.
```

Required text per D-01 (must append):
```
Default is `22/tcp` for Linux and `3389/tcp` for Windows (applied at runtime via `guest_os_family`).
```

The `default: "22/tcp"` static value is already correct and must not change.

[VERIFIED: git diff HEAD -- collections/ansible_collections/osac/templates/roles/ocp_virt_vm/meta/argument_specs.yaml]

---

### D-02: Planning docs update — NOT DONE

**Status:** GAP — PROJECT.md, MILESTONES.md, and RETROSPECTIVE.md all still describe the old `windows_oci_vm` architecture.

Specific stale content in PROJECT.md:
- "What This Is" describes the role as provisioning via `implementationStrategy: windows_oci_vm`
- "Current State" states "16-file Ansible role (`osac.templates.windows_oci_vm`)"
- "Context" says "Uses `implementationStrategy: windows_oci_vm`"
- "Key Decisions" table references `implementationStrategy: windows_oci_vm` as implemented

Specific stale content in MILESTONES.md (v1.0 section):
- "Created `windows_oci_vm` template role (16 files)"
- Key decision: "`implementationStrategy: windows_oci_vm` — clear, descriptive routing name"

Specific stale content in RETROSPECTIVE.md:
- "What Was Built" describes `windows_oci_vm` role
- References `implementationStrategy: windows_oci_vm` as routing name

Required messaging per D-02: `ocp_virt_vm` handles both Linux and Windows via `guest_os_family` branching; single template, single OSAC catalog registration; OS family inferred automatically from annotation or image path.

[VERIFIED: git status shows no modifications to .planning/PROJECT.md, .planning/MILESTONES.md, .planning/RETROSPECTIVE.md]

---

### D-03: Linux regression verification — DEFERRED TO EXECUTION

**Status:** Not yet executed (runtime requirement). The existing integration test suite in `tests/integration/targets/compute_instance_create/` uses the Linux fixture (`computeinstance-test.yaml`) and runs against `osac.templates.ocp_virt_vm`. It verifies the create flow with all override hooks.

The `run_tests.sh` script runs `compute_instance_create` (baseline + overrides) as part of the standard workflow test suite. The plan must include running this suite as a gate, not just asserting it will pass.

[VERIFIED: tests/integration/run_tests.sh; tests/integration/targets/compute_instance_create/tasks/baseline.yml]

---

### D-04: Lint compliance — DEFERRED TO EXECUTION

**Status:** Not yet executed. `yamllint` and `ansible-lint` are not available in the local environment — they are installed via `uv` in CI (`ansible-lint>=25.2.1` in `pyproject.toml` development group). Pre-commit hooks enforce `yamllint --strict`.

Static checks performed in this research:
- No trailing whitespace found in any modified file
- No tab characters found in any modified file
- No missing newlines at end of files
- YAML structure verified syntactically correct via Python `yaml.safe_load`

The plan must include `uv run ansible-lint` as a verification gate before committing.

[VERIFIED: .pre-commit-config.yaml; pyproject.toml; manual static analysis]

---

### D-05: Windows hostname truncated to 15 characters — DONE

**Status:** Implemented correctly in `create_validate.yaml`:
```yaml
- name: Extract VM hostname from ComputeInstance metadata (Windows NetBIOS limit)
  ansible.builtin.set_fact:
    vm_hostname: "{{ compute_instance.metadata.name[:15] }}"
  when: guest_os_family == 'windows'
```

No uppercase forcing. Warning task logs truncation only when name > 15 chars.

[VERIFIED: tasks/create_validate.yaml lines 23-33]

---

### D-06: Sysprep disk uses cdrom bus sata — DONE

**Status:** Implemented correctly in `create_secrets.yaml`:
```yaml
- name: sysprep-disk
  cdrom:
    bus: sata
```

The sysprep patch uses `cdrom:` (not `disk:`) with `bus: sata` — exactly matching the D-06 requirement.

[VERIFIED: tasks/create_secrets.yaml lines 40-42]

---

### D-07: Windows VM ready wait timeout is 900s — DONE

**Status:** Implemented correctly in `create_wait_annotate.yaml`:
```yaml
wait_timeout: "{{ 900 if guest_os_family == 'windows' else 600 }}"
```

[VERIFIED: tasks/create_wait_annotate.yaml line 17]

---

### D-08: SSH key injection is Linux-only — DONE

**Status:** Implemented correctly. Both the minimal cloud-init disk task and the SSH secret creation block are guarded with `when: guest_os_family == 'linux'`:
```yaml
- name: Add minimal cloud-init disk for SSH key propagation (Linux)
  when:
    - guest_os_family == 'linux'
    - vm_ssh_key | length > 0
    - vm_user_data_secret_ref | length == 0

- name: Create ssh public key secret and add accessCredentials to template spec (Linux)
  when:
    - guest_os_family == 'linux'
    - vm_ssh_key | length > 0
```

[VERIFIED: tasks/create_secrets.yaml lines 101-153]

---

### D-09: CloudBase-Init via cloudInitNoCloud volume — DONE

**Status:** Implemented correctly. The user-data block (when `vm_user_data_secret_ref | length > 0`) creates a cloudInitNoCloud volume for both OS families:
```yaml
cloudInitNoCloud:
  secretRef:
    name: "{{ compute_instance_name }}-user-data"
```

This block has no OS-family gate — it applies to both Linux and Windows when a user-data secret is specified.

[VERIFIED: tasks/create_secrets.yaml lines 49-99]

---

### D-10: Soft-fail deletion pattern — DONE

**Status:** Implemented correctly on all optional resource deletes in `delete_resources.yaml`:
- `delete_user_data_secret` (no OS gate — both families can have user-data)
- `delete_cloud_init_secret` (gated: `when: guest_os_family == 'linux'`)
- `delete_ssh_secret` (gated: `when: guest_os_family == 'linux'`)
- `delete_sysprep_configmap` (gated: `when: guest_os_family == 'windows'`)

All four use the pattern:
```yaml
failed_when:
  - result.failed is defined
  - result.failed
  - "'not found' not in (result.msg | default(''))"
```

[VERIFIED: tasks/delete_resources.yaml lines 101-150]

---

## Correctness Issues Found

### Issue 1: Orphaned "Delete cloud-init secret" task in delete_resources.yaml

**Severity:** Low (does not cause failures due to soft-fail pattern; no runtime breakage)
**Pre-existing:** Yes — this task exists in the baseline `ocp_virt_vm` before this branch
**Location:** `delete_resources.yaml` lines 107-120

`delete_resources.yaml` deletes a secret named `{name}-cloud-init` with `when: guest_os_family == 'linux'`. However, `create_secrets.yaml` never creates a secret with this name — Linux SSH key injection uses `{name}-user-data` (for user-data secret) and `{name}-ssh-public-key`. The `-cloud-init` name does not exist in the create flow.

This is the same class of bug identified in Phase 1 LEARNINGS.md (Test 10 UAT finding for `windows_oci_vm`): orphaned delete tasks copied from a reference implementation without semantic review.

The soft-fail `failed_when` pattern silently absorbs the "not found" error, so no runtime breakage occurs. However, the task is semantically incorrect and should be removed during this cleanup.

**Fix:** Remove the "Delete cloud-init secret" task block (lines 107-120 of delete_resources.yaml) or replace it with a comment explaining why it is absent.

[VERIFIED: tasks/delete_resources.yaml; tasks/create_secrets.yaml; git show HEAD:... (confirmed pre-existing)]

---

### Issue 2: `vm_hostname` variable is Windows-only but referenced in create_wait_annotate.yaml

**Severity:** Note only — not a bug
**Location:** `create_wait_annotate.yaml` line 52

`vm_hostname` is only set in `create_validate.yaml` when `guest_os_family == 'windows'`. In `create_wait_annotate.yaml`, the reference `"Hostname: {{ vm_hostname }}"` is inside a task guarded by `when: guest_os_family == 'windows'`, so it never executes on the Linux path. No undefined variable error occurs.

This is correct behavior — the conditional guard protects the Linux path. No action needed.

[VERIFIED: tasks/create_validate.yaml:25; tasks/create_wait_annotate.yaml:52-54]

---

## infer_guest_os_family.yaml — Correctness Verification

The logic in `infer_guest_os_family.yaml` is correct for all cases:

| Input | Result |
|-------|--------|
| No annotation, no windows image | Keeps role default (`linux`) |
| `osac.openshift.io/guest-os-family: windows` | `windows` |
| `osac.openshift.io/guest-os-family: WINDOWS` | `windows` (case-insensitive via `lower`) |
| `osac.openshift.io/guest-os-family: invalid` | Falls through to image heuristic |
| image contains `containerdisks/windows` | `windows` |
| image does not contain `containerdisks/windows` | Keeps role default |
| Annotation `linux` + Windows image | `linux` (annotation wins) |
| Invalid annotation + Windows image | `windows` (image heuristic wins) |
| `spec.image.sourceRef` absent | Treated as empty string via `| default('')` |

Logic is implemented as a single `set_fact` with nested Jinja2 ternaries — no undefined variable risk because all intermediate vars use `| default('')`.

[VERIFIED: tasks/infer_guest_os_family.yaml; manual logic simulation via Python]

---

## Runtime State Inventory

This is a role consolidation (rename/refactor category).

| Category | Items Found | Action Required |
|----------|-------------|-----------------|
| Stored data | None — KubeVirt VMs and DataVolumes are addressed by ComputeInstance `templateID` field, not by role name. Existing Windows VMs created by `windows_oci_vm` remain and are not affected (the role is not used for deletion routing — `templateID` in the ComputeInstance spec determines which role handles delete). | None |
| Live service config | AAP templates/job templates reference playbooks, not role names directly. The `playbook_osac_create_compute_instance.yml` dispatches via `template_id` variable from ComputeInstance spec. No AAP-level config references `windows_oci_vm` by name. | None — verify `templateID` in fixture is `osac.templates.ocp_virt_vm` (confirmed) |
| OS-registered state | None — no task scheduler entries, systemd units, or PM2 processes reference role names | None |
| Secrets/env vars | None — no secrets or env vars reference `windows_oci_vm` | None |
| Build artifacts | `windows_oci_vm` role directory deleted from working tree. No compiled artifacts (pure YAML). No installed packages referencing role name. | None |

**Existing live Windows VMs:** Any VMs created by the old `windows_oci_vm` role will still exist in the cluster. Their delete flow was triggered by `windows_oci_vm` previously. After consolidation, if they are deleted via OSAC, the ComputeInstance `templateID` must be `osac.templates.ocp_virt_vm` for the new delete path to execute. VMs created with `templateID: osac.templates.windows_oci_vm` would fail deletion unless the ComputeInstance spec is updated. This is a production concern but is **out of scope** for this phase (no live clusters in dev/test).

**Migration action required before production rollout:** Before deploying this consolidation to any cluster that has ComputeInstance resources with `templateID: osac.templates.windows_oci_vm`, one of the following must be completed:

1. **Field migration (recommended):** Run a one-time migration job that patches all existing ComputeInstance resources: `kubectl get computeinstance -A -o json | jq '... | select(.spec.templateID=="osac.templates.windows_oci_vm")' | kubectl patch ...` — update `spec.templateID` to `osac.templates.ocp_virt_vm`. Validate by re-running `get computeinstance -A` and confirming zero `windows_oci_vm` templateID values remain before enabling deletion.
2. **Compatibility shim (alternative):** Add a lookup in the OSAC delete flow that remaps `osac.templates.windows_oci_vm` → `osac.templates.ocp_virt_vm` at dispatch time, allowing in-flight ComputeInstance deletions to succeed without a field migration.

Track this as a pre-production migration task before the `run-windows-vm` branch is deployed to any live cluster.

[VERIFIED: No `windows_oci_vm` references in YAML files outside .planning; playbook dispatch via template_id variable]

---

## Standard Stack

### Tools Used in This Role

| Tool | Version | Purpose |
|------|---------|---------|
| `ansible-lint` | >=25.2.1 | Lint enforcement (CI + pre-commit) |
| `yamllint` | v1.35.1 | YAML formatting (pre-commit) |
| `kubernetes.core.k8s` | Collection dep | KubeVirt/k8s resource management |
| `ansible.builtin.set_fact` | stdlib | Variable setting / spec patching |
| `ansible.builtin.include_tasks` | stdlib | `infer_guest_os_family.yaml` inclusion |

### Lint Configuration

`ansible-lint` is configured via `.ansible-lint.yml` with these skips:
- `role-name[path]` — skipped (path-based collection naming)
- `parser-error` — known false positive for multi-play test playbooks
- `fqcn[keyword]` — skipped for `collections:` keyword usage

`yamllint` runs with `--strict` via pre-commit, using `.yamllint.yaml` (line-length disabled, truthy check-keys=false, comments min-spaces 1).

[VERIFIED: .ansible-lint.yml; .yamllint.yaml; .pre-commit-config.yaml]

---

## Common Pitfalls

### Pitfall 1: Orphaned delete tasks (already present — fix in plan)
**What goes wrong:** Delete tasks remove Kubernetes resources that the create flow never creates, causing confusion and masking real missing-cleanup bugs.
**Why it happens:** Copy-paste from reference roles without semantic create/delete symmetry review.
**How to avoid:** For every resource named in delete_resources.yaml, verify its name appears in create_secrets.yaml, create_build_spec.yaml, or create_resources.yaml.
**Warning signs:** Resource names in delete tasks that don't appear anywhere in create tasks.

### Pitfall 2: Undefined variable `vm_hostname` on Linux path
**What goes wrong:** If `vm_hostname` is referenced without an OS guard, Linux runs produce an `undefined variable` error.
**How to avoid:** Any task referencing `vm_hostname` must be guarded with `when: guest_os_family == 'windows'`.
**Current status:** Correctly guarded in both `create_validate.yaml` (where it is set) and `create_wait_annotate.yaml` (where it is referenced).

### Pitfall 3: ansible-lint not available locally
**What goes wrong:** Linting is silently skipped if `uv` virtual environment is not activated.
**How to avoid:** Run `uv run ansible-lint` — not bare `ansible-lint`. The tool lives in the `uv` environment defined by `pyproject.toml`.

### Pitfall 4: Pre-existing `{name}-cloud-init` orphan causes confusion
**What goes wrong:** Future reviewers see a delete task for a resource that doesn't exist and either (a) add a create task to match it, or (b) spend time debugging why it doesn't fail.
**How to avoid:** Remove the task during this cleanup. The soft-fail pattern hides the bug at runtime but the task is incorrect.

---

## Code Examples

### Correct exposed_ports description (D-01 target state)

The description block to replace in `meta/argument_specs.yaml`:

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

### Task block to remove from delete_resources.yaml (orphaned)

Remove lines 107-120:
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

This task has no corresponding create task. The correct Linux secret names are `{name}-user-data` and `{name}-ssh-public-key`.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| `uv` | ansible-lint, yamllint | Not found | — | Cannot run lint locally; use CI or install uv |
| `ansible-lint` | D-04 lint gate | Via uv only | >=25.2.1 | CI enforces on PR |
| `yamllint` | D-04 lint gate + pre-commit | Via uv only | v1.35.1 | CI enforces on PR |
| `git` | Commit | Available | — | — |
| `pre-commit` | Pre-commit hooks | Unknown (not checked) | — | Manual yamllint equivalent |

**Missing dependencies with no fallback:**
- `uv` not found locally — D-04 requires `uv run ansible-lint` to pass. Plan must either install uv or document that lint runs in CI only.

**Missing dependencies with fallback:**
- None that block the code changes.

---

## Validation Architecture

### Phase Requirements — Test Map

| Req | Behavior | Test Type | Automated Command | Coverage |
|-----|----------|-----------|-------------------|----------|
| D-01 | `exposed_ports` description updated | Static | grep for "22/tcp for Linux" in argument_specs.yaml | Manual verify |
| D-02 | Planning docs updated | Manual review | Grep for `ocp_virt_vm` in PROJECT.md | Manual verify |
| D-03 | Linux path unaffected | Integration | `./tests/integration/run_tests.sh` (requires kind cluster) | `compute_instance_create` baseline + overrides |
| D-04 | Lint clean | Lint | `uv run ansible-lint` | CI enforces |
| D-05–D-10 | Implementation correct | Already verified in this research | File inspection | Done |

### Wave 0 Gaps

- `uv` installation required for local lint: `curl -LsSf https://astral.sh/uv/install.sh | sh` then `uv sync --locked --all-extras --group development`
- Kind cluster required for D-03 integration tests: installed via CI `helm/kind-action`; local kind cluster can be used if available

---

## Open Questions (RESOLVED)

1. **Should the orphaned cloud-init secret delete task be removed or left with a comment?**
   - What we know: It is pre-existing, soft-fail, and not introduced by this branch.
   - What's unclear: Whether removing it is in scope for this consolidation phase (it's a bug fix, not strictly a consolidation task).
   - Recommendation: Include removal — this phase is a cleanup of ocp_virt_vm and it is the right time to fix it. The fix is one task block deletion with zero risk.
   - **RESOLVED: Included in Plan 01-01 Task 2.**

2. **Is a Windows-specific integration test target needed, or is the fixture sufficient for now?**
   - What we know: The `computeinstance-windows-test.yaml` fixture exists and `templateID` is correct. No `compute_instance_create_windows` test target exists in `tests/integration/targets/`.
   - What's unclear: CONTEXT.md says "Run existing integration tests" (D-03) — it does not require a new Windows test target.
   - Recommendation: No new test target needed for this phase. The existing Linux regression test (D-03) is sufficient. A Windows end-to-end test would require a real KubeVirt cluster and is deferred (in scope for a future v2 milestone).
   - **RESOLVED: No new Windows test target for this phase. Linux regression gate covers D-03 (Plan 01-03 Task 2).**

3. **Do existing live VMs with `templateID: osac.templates.windows_oci_vm` (old value) need migration?**
   - What we know: No live production clusters exist in dev/test. The test fixture has already been updated to `osac.templates.ocp_virt_vm`.
   - Recommendation: Document as out of scope. Add a note to MILESTONES.md or PROJECT.md migration section if upgrading a live cluster.
   - **RESOLVED: Out of scope for this phase. Noted in Plan 01-02 planning doc updates.**

---

## Sources

### Primary (HIGH confidence — verified against working tree)
- `collections/ansible_collections/osac/templates/roles/ocp_virt_vm/` — all task, defaults, meta files read directly
- `git diff HEAD` — confirmed which files changed and what changed
- `.planning/phases/01-windows-vm-provisioning/01-CONTEXT.md` — locked decisions
- `.planning/PROJECT.md`, `.planning/MILESTONES.md`, `.planning/RETROSPECTIVE.md` — confirmed stale content
- `tests/integration/` — test runner, fixtures, targets read directly
- `.ansible-lint.yml`, `.yamllint.yaml`, `.pre-commit-config.yaml`, `pyproject.toml` — lint tooling confirmed

---

## Assumptions Log

This table is empty — all claims in this research were verified directly against the working tree. No assumed knowledge was used.

---

## Metadata

**Confidence breakdown:**
- Decision audit (D-01 through D-10): HIGH — each decision verified by reading exact file content
- Infer logic correctness: HIGH — simulated all edge cases with Python
- Orphaned delete task: HIGH — traced create/delete resource names exhaustively
- Lint tooling availability: HIGH — verified via `command -v`, `pip3 list`, `pyproject.toml`
- Planning docs staleness: HIGH — confirmed via git status (no modifications) and file content read

**Research date:** 2026-05-02
**Valid until:** Indefinite — findings are against specific working tree state; re-verify if tree changes
