---
phase: "01"
reviewers: [cursor]
reviewed_at: "2026-05-03T00:00:00Z"
plans_reviewed:
  - 01-01-PLAN.md
  - 01-02-PLAN.md
  - 01-03-PLAN.md
---

# Cross-AI Plan Review — Phase 01 (ocp_virt_vm Consolidation)

## Cursor Review

# Cross-AI Plan Review: Phase 1 — `ocp_virt_vm` Consolidation

## 1. Summary

The three-plan split is sensible: **01-01** closes verifiable code gaps with explicit verification commands; **01-02** updates planning artifacts in parallel; **01-03** gates merges on lint and Linux regression. Together they cover the stated phase goal and decisions D-01 through D-04, with a clear Wave 1 / Wave 2 ordering for verification after code edits. The main quality issue is an **internal contradiction in Plan 01-02** between "preserve v1.0 unchanged" and a must-have that requires **v1.0** milestone text to reflect the unified template—those cannot both be true. Resolving that inconsistency, and tightening wording on **PROJECT.md** so "no `windows_oci_vm` as active" still allows honest historical/archival mentions, will make the doc plan executable without scope fights.

## 2. Strengths

- **Clear, testable acceptance criteria** for 01-01 (grep + YAML validity) reduce ambiguity for autonomous execution.
- **Explicit create/delete symmetry** called out for the orphan `cloud-init` delete aligns with Ansible maintainability and avoids silent resource leaks or meaningless tasks.
- **D-04 and D-03** are framed as blocking gates with fallbacks (CI / PR checks when kind is missing)—practical for real setups.
- **Dependency choice** (01-03 → 01-01 only) correctly treats 01-02 as non-blocking for executable Ansible behavior; avoids unnecessary serialization.
- **Scope discipline**: 01-01 avoids changing `default: "22/tcp"` while documenting runtime behavior—matches the user decision and avoids breaking consumers that rely on the static default in specs/UI.

## 3. Concerns

- **HIGH — Plan 01-02 contradiction:** Task 2 requires **historical v1.0 content preserved unchanged** while a must-have demands **"MILESTONES.md v1.0 key decisions reflect ocp_virt_vm as unified template."** Updating v1.0 key decisions *is* changing v1.0. Fix by narrowing the must-have to **v1.1** (or explicitly allow a surgical correction to v1.0 with strikethrough/errata—if that is allowed, "preserved unchanged" must be reworded).
- **MEDIUM — 01-03 lint paths vs. 01-01 edits:** Verification runs `yamllint` only on `argument_specs.yaml` and `delete_resources.yaml`. If those paths are meant to be relative to the role directory, the commands should **chdir or pass full paths** (e.g. `collections/.../ocp_virt_vm/meta/argument_specs.yaml`) so autonomous runs don't lint the wrong files or fail with "not found." The plan should pin **working directory** or **paths** unambiguously.
- **MEDIUM — Integration test scope vs. consolidation risk:** Stated tests focus on **Linux create**. That matches D-03, but the *consolidation* also touches **Windows** and **shared** tasks. If the suite has **no Windows path** or **guest_os_family** assertions, regression coverage is **partial** by design—acceptable if explicitly acknowledged; otherwise consider at least one **molecule/unit**-style assert or a **dry-run** Windows fixture if feasible.
- **MEDIUM — PROJECT.md "no windows_oci_vm":** A strict reading of "no references to `windows_oci_vm` as the active implementation" can collide with useful text ("removed," "replaced by," "migrated from"). The plan should require **no outdated architecture presented as current**, not necessarily **zero string occurrences**.
- **LOW — Folded scalar in `argument_specs.yaml`:** Appending a sentence to a folded block is usually fine; watch **line wrapping** and **lint rules** (e.g. line length) so yamllint stays green without awkward reflow.
- **LOW — Wave 1 parallelism:** 01-01 and 01-02 independent is good; ensure **merge order** or **single PR** policy is clear so doc updates don't land describing behavior that isn't merged yet (process, not Ansible).

## 4. Suggestions

- **Resolve 01-02 must-haves:** Replace "v1.0 key decisions reflect unified template" with "**v1.1** documents consolidation; v1.0 unchanged **or** add an errata subsection under v1.1 that points to frozen v1.0 text."
- **Pin 01-03 commands:** Prefix all lint targets with **repo-root-relative** paths or `cd` to the role; mirror **CI** job paths if they already exist.
- **Optional small addition to 01-03:** If CI runs ansible-lint on the **whole collection** or repo, align local commands with CI so "passes locally" implies "passes in pipeline."
- **Symmetry note in 01-01:** After removing the orphan task, add a **one-line comment in RESEARCH.md or PLAN** (not necessarily in YAML) that `{name}-cloud-init` was never created—helps future readers avoid re-adding it.
- **RETROSPECTIVE / MILESTONES:** When adding v1.1, include **decision IDs** (D-01–D-10) for traceability to the user decision list.

## 5. Risk Assessment

**Overall risk: LOW**

**Justification:** Changes in 01-01 are **documentation** in argument specs plus **removal of a no-op delete** that was already soft-failing—low blast radius if verified as non-created. Lint and Linux integration gates catch **YAML/syntax regressions** and **Linux path** breakage. Residual risk is **incomplete Windows-side validation** (MEDIUM impact if Windows-only tasks regress) and **plan ambiguity in 01-02** (process/doc integrity, not runtime)—fixing the v1.0 vs v1.1 wording keeps risk **LOW** for merged execution.

---

## Consensus Summary

*(Single reviewer — no consensus calculation needed)*

### Strengths

- Testable acceptance criteria throughout (grep-verifiable)
- Correct wave dependency (01-03 → 01-01, 01-02 independent)
- D-04 and D-03 framed as hard blocking gates with CI fallback

### Agreed Concerns

- **HIGH**: Plan 01-02 internal contradiction — "preserve v1.0 unchanged" vs must-have requiring v1.0 key decisions to reflect unified template
- **MEDIUM**: 01-03 lint paths should be pinned to repo-root-relative paths
- **MEDIUM**: PROJECT.md acceptance criteria "zero occurrences" too strict — should be "no active architecture references"

### Action Before Executing

Fix Plan 01-02 must-have wording before execution:
- `"MILESTONES.md v1.0 key decisions reflect ocp_virt_vm as unified template"` → change to reference v1.1 section only
- PROJECT.md acceptance criterion: loosen from `grep -c "windows_oci_vm" returns 0` to `no outdated architecture presented as current`

---

## Cursor Review (2026-05-04T09:11:55Z)

Here is a structured review. I skimmed the live `ocp_virt_vm` role under `collections/ansible_collections/osac/templates/roles/ocp_virt_vm/` so the feedback matches your tree, not only the plan text.

---

## PLAN 01-01: Code-level gap fixes

### Summary
The scope is tight and the success criteria are testable, but **Task 2 must be executed against the real task name and secret identity**. In the current repo, `delete_resources.yaml` has **“Delete user-data secret”** for `{{ compute_instance_name }}-user-data`, and `create_secrets.yaml` **does** create that secret when `vm_user_data_secret_ref` is non-empty. The planning artifacts describe removing an older **“Delete cloud-init secret”** / `{name}-cloud-init` task. If anyone interprets the plan as “drop all cloud-init–related deletes” and removes **user-data** cleanup, you would break symmetry and **leave user-data secrets behind** after delete.

### Strengths
- Small blast radius: metadata copy + delete-task cleanup.
- Explicit **create/delete symmetry** as a must-have aligns with ops hygiene and avoids confusing no-op deletes.
- `exposed_ports` clarification in `argument_specs` helps AAP/operators understand that runtime defaults depend on `guest_os_family`.

### Concerns
- **HIGH — Task naming / semantics:** Plan text says **“Delete cloud-init secret”**; the file today shows **“Delete user-data secret”**. Implementation must verify `grep`/task titles and **`metadata.name`** so you only remove an **orphaned** `{name}-cloud-init` (or equivalent) delete, **not** the user-data secret delete that pairs with create.
- **LOW — Task 1 may already be satisfied:** `meta/argument_specs.yaml` already documents that defaults are `22/tcp` vs `3389/tcp` via `guest_os_family`. The plan should say whether “append” means an extra sentence or **re-verify** wording vs catalog UX.
- **MEDIUM — Symmetry checklist:** Beyond the orphaned task, symmetry should explicitly cover **minimal Linux cloud-init** (inline `userData`, no user-data Secret): delete should remain safe/idempotent for that path (your `failed_when` / not-found handling already supports that).

### Suggestions
- Add a **one-line verification** to Task 2: after edit, confirm `create_secrets.yaml` creates `{name}-user-data` in the mirrored-user-data block and that **that** delete remains.
- Optionally add **`when:` parity** on “Delete user-data secret” mirroring create conditions (only if delete should never touch that secret in paths where create never ran — optional hardening).

### Risk assessment
**MEDIUM** — Correct if the orphaned task is truly gone or correctly identified; **HIGH** risk of a bad edit if Task 2 is applied to the wrong task.

---

## PLAN 01-02: Planning documentation update

### Summary
Straightforward narrative work that closes the loop for maintainers and matches the stated phase goal (**unified architecture in docs**). Main risk is **stale or divergent docs** (`vendor/` copies, duplicate `ocp_virt_vm` trees) if contributors only edit one canonical path.

### Strengths
- Ties consolidation to **PROJECT / MILESTONES / RETROSPECTIVE**, which is the right level for “what did we ship and why.”
- Calling out **infer_guest_os_family** in RETROSPECTIVE captures the behavioral contract future readers need.

### Concerns
- **MEDIUM — Source of truth:** This repo also has `vendor/ansible_collections/osac/massopencloud/roles/ocp_virt_vm/` (and similar). If `vendor/` is generated or pinned, docs should say **which tree is authoritative** so updates are not duplicated or forgotten.
- **LOW — Scope:** “Reflect consolidation” is vague; define minimal bullets (single template, single catalog registration, branching variable, inference order) so the update does not creep into full design rewrite.

### Suggestions
- In PROJECT.md, add a short **“Authoritative role path”** pointer (templates vs vendor) if that is a recurring confusion.
- Cross-link **Must-haves from 01-01** in MILESTONES so doc claims trace to verified behavior.

### Risk assessment
**LOW** for correctness of the codebase; **MEDIUM** for documentation accuracy if repo layout is not clarified.

---

## PLAN 01-03: Lint gate + Linux integration regression

### Summary
A solid **definition of done** for consolidation: lint clean + **Linux `compute_instance_create`** still passes. The project’s own verification notes (`uv run ansible-lint`, `uv run yamllint --strict`) are the right execution pattern when tools are not on bare `PATH`.

### Strengths
- **Full role** `ansible-lint` (not only touched files) catches collateral issues — aligns with excerpts in `.planning/.../01-VERIFICATION.md`.
- Linux integration test as **regression gate** is appropriate for “unified template” changes that could break the existing happy path.

### Concerns
- **MEDIUM — Coverage gap:** Linux-only gate does **not** prove Windows paths; acceptable if phase scope is explicitly “no new Windows integration in this phase,” but the risk should be acknowledged in the plan.
- **LOW — “Zero warnings” vs tool noise:** Your own 01-03 summary mentions **informational** ansible-lint messages about config scan / yamllint compatibility. The plan should state whether **exit code 0 + zero rule violations** is enough, or whether *any* stderr warning fails the gate.
- **MEDIUM — Environment:** Integration tests on **kind** (or similar) need a documented **CI vs local** expectation; flakes block merges if the gate is strict.

### Suggestions
- Pin **exact commands** in the plan (paths, `uv sync` / lockfile) so runs are reproducible across machines.
- Add an **optional** follow-up line: “If Windows E2E exists but is manual, record result in phase notes” — without expanding scope unless you want it.

### Risk assessment
**LOW–MEDIUM** — Low for “lint only”; medium if integration tests are environment-sensitive or Windows regressions are out of scope but operationally important.

---

## Phase-level notes (cross-plan)

1. **Ordering:** Run **01-01 → 01-03** in sequence; **01-02** can proceed in parallel but should be **finalized after** code must-haves so docs match shipped behavior.
2. **Security:** Incorrect removal of **user-data** delete is the main **secretion / cleanup** concern; the orphaned **cloud-init-named** delete is hygiene only.
3. **Phase goal fit:** The three plans together **do** cover “remaining code gaps + docs + verification,” provided **01-01 Task 2** is executed with the **correct** task and **01-03**’s Linux-only scope is **explicitly accepted**.

---

## Overall risk assessment

**MEDIUM**, driven almost entirely by **PLAN 01-01 Task 2 ambiguity** (wrong task removed → leaked secrets or broken deletes). **01-02** and **01-03** are lower risk if commands and scope are pinned as above.

---

*Note: I’m in **Ask mode** — I only read the repo; I did not run linters or tests.* If you want those run and results folded into this review, switch to Agent mode or run the same `uv run` commands locally.

---

## Consensus Summary (Cursor — post-ship review)

Cursor inspected the live role files directly, not just the plan text.

### Agreed Strengths
- Minimal, focused scope: only two code changes (exposed_ports description, orphaned task removal) — no risk of unintended regressions
- Lint + integration test gate (Plan 01-03) as a hard prerequisite is sound engineering

### Agreed Concerns
- The YAML comment added to `argument_specs.yaml` documents the ordering dependency between the spec default and the Windows runtime override — but if `create_validate.yaml` is ever refactored, the comment alone won't enforce the invariant (no automated test asserts the ordering)
- `delete_resources.yaml` stop-wait still uses `VirtualMachine` Ready=False as the signal (since replaced by VMI disappearance poll in WR-03 fix, but this was a valid concern at plan time)

### Divergent Views
- Cursor flagged the description-only fix in Plan 01-01 as potentially insufficient (the machine-readable `default` field is still Linux-only); this was addressed in WR-01 with a YAML comment — both reviewers agree a code-level invariant would be stronger than documentation alone
