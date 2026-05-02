# Phase 1: Windows VM Provisioning - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-02
**Phase:** 1-windows-vm-provisioning
**Areas discussed:** argument_specs exposed_ports, Planning doc updates, Linux regression test strategy, ansible-lint compliance

---

## argument_specs exposed_ports

| Option | Description | Selected |
|--------|-------------|----------|
| Document OS-dependent defaults | Add a note in the description explaining default is 22/tcp for Linux and 3389/tcp for Windows. Static default stays 22/tcp. | ✓ |
| Remove the default from the spec | Drop the static default from argument_specs.yaml entirely; actual defaults live in defaults/main.yaml. | |
| You decide | Claude picks the most consistent approach with the existing OSAC pattern. | |

**User's choice:** Document OS-dependent defaults
**Follow-up — where to put the note:**

| Option | Description | Selected |
|--------|-------------|----------|
| In the exposed_ports description field | Append the note directly to the exposed_ports field description. | ✓ |
| In the guest_os_family description | Cross-reference from the guest_os_family option description instead. | |

**User's choice:** In the exposed_ports description field
**Notes:** Note text: "Default is `22/tcp` for Linux and `3389/tcp` for Windows (applied at runtime via `guest_os_family`)."

---

## Planning doc updates

| Option | Description | Selected |
|--------|-------------|----------|
| Update PROJECT.md only | PROJECT.md is live; RETROSPECTIVE.md and MILESTONES.md stay as historical record. | |
| Update all three | Update PROJECT.md, RETROSPECTIVE.md, and MILESTONES.md to describe the consolidated ocp_virt_vm approach. | ✓ |
| Leave all as-is | They're historical artifacts; code is the truth. | |

**User's choice:** Update all three
**Follow-up — key message:**

| Option | Description | Selected |
|--------|-------------|----------|
| Unified template, guest_os_family branching | ocp_virt_vm handles both Linux and Windows. OS family inferred automatically. Single template, single OSAC catalog registration. | ✓ |
| Refactor from two-role to one-role model | Emphasize the before/after: v1.0 shipped as two roles, this consolidates into one. | |

**User's choice:** Unified template, guest_os_family branching

---

## Linux regression test strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Static verification only | Grep/read checks that Linux tasks have no Windows guards leaking in. No live cluster test. | |
| Run existing integration tests | The existing ocp_virt_vm integration test suite covers the Linux path. Run it. | ✓ |
| Add a Linux fixture check | Add a verification step tracing through the Linux flow explicitly. | |

**User's choice:** Run existing integration tests
**Notes:** The integration test suite is the regression gate for the Linux path.

---

## ansible-lint compliance

| Option | Description | Selected |
|--------|-------------|----------|
| Before committing (pre-commit hooks) | Run ansible-lint and yamllint as part of the plan; block commit on failure. | ✓ |
| After committing (CI only) | Let CI catch lint issues. | |

**User's choice:** Before committing (pre-commit hooks)
**Notes:** Project already has pre-commit hooks configured. Lint must pass before final commit.

---

## Claude's Discretion

None — user made explicit choices for all four areas.

## Deferred Ideas

None — discussion stayed within phase scope.
