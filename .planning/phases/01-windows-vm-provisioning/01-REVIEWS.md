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
